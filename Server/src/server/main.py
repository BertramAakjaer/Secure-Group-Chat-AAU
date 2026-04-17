import asyncio
from server.server import start_server

import asyncio, argparse

def main():
    parser = argparse.ArgumentParser(description="Server for hosting an E2EE group chat")

    # Valgfrie "flag"
    parser.add_argument("--local", action="store_true", help="Run on 127.0.0.1 if set, otherwise 0.0.0.0")
    parser.add_argument("-p", "--port", type=int, default=5555, help="Optional port (default: 5555)")

    args = parser.parse_args()
    
    host_ip = "127.0.0.1" if args.local else "0.0.0.0"
    host_port = args.port

    # Initalisere og kører server objektet
    start_server(ip=host_ip, port=host_port)