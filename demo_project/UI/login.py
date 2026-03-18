from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/chat", methods=["POST"])
def chat():
    username = request.form.get("username")

    if not username:
        return redirect("/")

    return render_template("chat.html", username=username)

if __name__ == "__main__":
    app.run(debug=True)