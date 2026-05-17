from client.routes import app
from common.network_utils import init_logger

def start_client(port, verbose=False):
    init_logger(verbose, "client")
    app.run(debug=True, port=port, use_reloader=False)