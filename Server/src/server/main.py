import asyncio
from server.server import Server


def main():
    service = Server(host="0.0.0.0")
    try:
        asyncio.run(service.start())
    except KeyboardInterrupt:
        pass