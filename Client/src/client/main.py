import sys, asyncio
from client.client import Client

def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <username> [server_ip]")
        return

    username = sys.argv[1].lower().strip()
    server_ip = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"

    client = Client(username, server_ip=server_ip)

    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        pass