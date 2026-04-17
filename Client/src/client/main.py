import argparse
from client.client import start_client

def main():
    parser = argparse.ArgumentParser(description="Client to connect to a E2EE group chat")

    # Valgfrie "flag"
    parser.add_argument("-p", "--port", type=int, default=5555, help="Optional port (default: 5555)")

    args = parser.parse_args()
    
    # Initialisere klienten med port
    start_client(port=args.port)