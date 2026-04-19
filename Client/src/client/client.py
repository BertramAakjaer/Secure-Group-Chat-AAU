from client.routes import app

def start_client(port):
    app.run(debug=True, port=port, use_reloader=False)