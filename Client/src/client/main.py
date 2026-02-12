import asyncio, argparse
from client.client import Client

def main():
    parser = argparse.ArgumentParser(description="Client to connect to a E2EE group chat")

    # Påkrævede "flag"
    parser.add_argument("username", help="The username use in the groups")
    parser.add_argument("ip_address", help="The target IP address for the server")

    # Valgfrie "flag"
    parser.add_argument("-p", "--port", type=int, default=8888, help="Optional port (default: 8888)")

    args = parser.parse_args()

    username = args.username.lower().strip()
    
    
    # Initialisere klienten med deres username, ip og port
    client = Client(username, server_ip=args.ip_address, server_port=args.port)

    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        pass
    

if __name__ == "__main__":
    main()