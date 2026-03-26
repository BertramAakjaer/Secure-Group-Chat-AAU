from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    chats = {
        "Erika": [
            {"sender": "Erika", "text": "Hey, how are you?", "time": "3 mins ago"},
            {"sender": "You", "text": "I'm good thanks!", "time": "2 mins ago"}
        ],
        "Madeline": [
            {"sender": "Madeline", "text": "Are we on today?", "time": "1 hour ago"}
        ],
        "Python": [
            {"sender": "Erika", "text": "What was the work again?", "time": "1 hour ago"}
        ],
        "Girlss": [
            {"sender": "Erika", "text": "Hey, how are you guys?", "time": "3 mins ago"},
            {"sender": "You", "text": "I'm good, thanks! How about you?", "time": "2 mins ago"},
            {"sender": "Madeline", "text": "Hey, I am good too, what about you?", "time": "1 mins ago"}
        ]
    }

    return render_template("index.html", chats=chats)

if __name__ == "__main__":
    app.run(debug=True)