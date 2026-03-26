# =================================
# IMPORTS OG OPSÆTNING AF FLASK
# =================================

# Importerer nødvendige funktioner fra Flask samt standardbiblioteker
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import string

# Opretter Flask app
app = Flask(__name__)

# Bruges til session (gemmer fx username midlertidigt)
app.secret_key = "supersecretkey"

# Gemmer chats i hukommelsen (forsvinder når server stopper)
chats = {}

# =================================
# GENERERING AF CHAT-ID
# =================================

# Funktion der laver et unikt chat-id bestående af bogstaver og tal
def generate_chat_id(length=6):
    while True:
        chat_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if chat_id not in chats:
            return chat_id

# =================================
# FORSIDE
# =================================

# Viser startside hvor brugeren kan vælge at oprette eller joine chat
@app.route("/")
def index():
    return render_template("forside.html")


# =================================
# OPRET CHAT
# =================================

# Håndterer oprettelse af en ny gruppechat
@app.route("/create", methods=["GET", "POST"])
def create_chat():
    if request.method == "POST":
        username = request.form.get("username")

        # Kontrollerer om brugernavn er udfyldt
        if not username:
            return render_template("create.html", error="Du skal skrive et brugernavn.")

        # Genererer nyt chat-id
        chat_id = generate_chat_id()

        # Opretter chat med første medlem
        chats[chat_id] = {
            "members": [username],
            "messages": []
        }

        # Gemmer bruger og chat i session
        session["username"] = username
        session["chat_id"] = chat_id

        # Sender brugeren videre til chatten
        return redirect(url_for("chat_room", chat_id=chat_id))

    return render_template("create.html")

# =================================
# JOIN CHAT
# =================================

# Gør det muligt at deltage i en eksisterende chat
@app.route("/join", methods=["GET", "POST"])
def join_chat():
    if request.method == "POST":
        username = request.form.get("username")
        chat_id = request.form.get("chat_id", "").upper()

        # Kontrollerer om begge felter er udfyldt
        if not username or not chat_id:
            return render_template("join.html", error="Udfyld både brugernavn og chat-id.")

        # Kontrollerer om chat-id findes
        if chat_id not in chats:
            return render_template("join.html", error="Chat-id findes ikke.")

        # Tilføjer bruger til chat hvis ikke allerede medlem
        if username not in chats[chat_id]["members"]:
            chats[chat_id]["members"].append(username)

        # Gemmer bruger i session
        session["username"] = username
        session["chat_id"] = chat_id

        # Sender brugeren videre til chatten
        return redirect(url_for("chat_room", chat_id=chat_id))

    return render_template("join.html")

# =================================
# CHAT SIDE
# =================================

# Viser selve chatten for en specifik gruppe
@app.route("/chat/<chat_id>")
def chat_room(chat_id):
    username = session.get("username")
    session_chat_id = session.get("chat_id")

    # Kontrollerer om brugeren har adgang til chatten
    if not username or session_chat_id != chat_id or chat_id not in chats:
        return redirect(url_for("join_chat"))

    return render_template(
        "chat.html",
        chat_id=chat_id,
        username=username,
        members=chats[chat_id]["members"],
    )

# =================================
# OPDATER MEMBERS
# =================================

@app.route("/get_members/<chat_id>")
def get_members(chat_id):
    if chat_id not in chats:
        return jsonify([])
    
    return jsonify(chats[chat_id]["members"])


# =================================
# SEND BESKED
# =================================

# Modtager besked fra frontend og gemmer den i chatten
@app.route("/send_message/<chat_id>", methods=["POST"])
def send_message(chat_id):
    username = session.get("username")

    # Kontrollerer om chat og bruger findes
    if chat_id not in chats or not username:
        return jsonify({"success": False}), 400

    data = request.get_json()
    message = data.get("message", "").strip()

    # Gemmer besked hvis den ikke er tom
    if message:
        chats[chat_id]["messages"].append({
            "username": username,
            "text": message
        })

    return jsonify({"success": True})

# =================================
# HENT BESKEDER
# =================================

# Sender alle beskeder i en chat til frontend
@app.route("/get_messages/<chat_id>")
def get_messages(chat_id):
    if chat_id not in chats:
        return jsonify([])

    return jsonify(chats[chat_id]["messages"])

# =================================
# START SERVER
# =================================

# Starter Flask serveren
if __name__ == "__main__":
    app.run(debug=True, port=5002)