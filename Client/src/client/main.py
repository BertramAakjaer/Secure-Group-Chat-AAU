import argparse

from client.client import start_client
from common.config import CLIENT_UI_PORT

def main():
    parser = argparse.ArgumentParser(description="Client to connect to a E2EE group chat")

    # Valgfrie "flag"
    parser.add_argument("-p", "--port", type=int, default=CLIENT_UI_PORT, help=f"Optional port for the local UI (default: {CLIENT_UI_PORT})")
    parser.add_argument("-v", "--verbose", action="store_true", help="Log all sent packets to json files")

    args = parser.parse_args()
    
    # Initialisere klienten med port
    start_client(port=args.port, verbose=args.verbose)