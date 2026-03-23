from flask import Flask, render_template

app = Flask(__name__)

# Flask's ONLY job is to serve the UI frontend.
@app.route('/')
def index():
    return render_template('index.html')

def main():
    app.run(debug=True, port=5000)

if __name__ == '__main__':
    main()