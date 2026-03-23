import asyncio
import json
import websockets

from common.utils import PackageType

class Client:
    def __init__(self, username, server_ip="127.0.0.1", server_port=8888, ws_port=8765):
        self.username = username
        self.server_ip = server_ip
        self.server_port = server_port
        
        self.ws_port = ws_port # Local port for the UI browser to connect to
        self.ui_clients = set() # Keeps track of open browser tabs
        
        self.reader = None
        self.writer = None
        self.running = True

    async def connect_tcp(self):
        """Connects to the main chat server via TCP."""
        try:
            self.reader, self.writer = await asyncio.open_connection(self.server_ip, self.server_port)
            msg = json.dumps({"username": self.username}) + "\n"
            self.writer.write(msg.encode())
            await self.writer.drain()
            print(f"Connected to Chat Server as {self.username}")
            return True
        except Exception as e:
            print(f"TCP Connection failed: {e}")
            return False

    async def listen_tcp(self):
        """Listens for TCP messages from the server and forwards them to the Web UI."""
        if not self.reader: return
        
        while self.running:
            try:
                data = await self.reader.readline()
                if not data:
                    print("Disconnected from server.")
                    self.running = False
                    break
                
                # Forward the exact JSON payload to all connected browser tabs
                message_json = data.decode()
                websockets.broadcast(self.ui_clients, message_json)
                
            except Exception as e:
                print(f"Network error: {e}")
                self.running = False
                break

    async def handle_ws_client(self, websocket):
        """Handles incoming messages from the Browser UI."""
        self.ui_clients.add(websocket)
        try:
            async for content in websocket:
                # Browser sends plain text; we format it for TCP here.
                await self.process_ui_command(content)
        finally:
            self.ui_clients.remove(websocket)

    async def process_ui_command(self, content):
        """Parses UI input and sends via TCP."""
        payload = {}
        if content.startswith("/add"):
            parts = content.split(" ")
            if len(parts) > 1:
                target = parts[1]
                payload = {"type": PackageType.WELCOME, "dest": target, "content": f"KeyPackage-For-{target}"}
        else:
            payload = {"type": "MSG", "dest": "all", "content": content}

        if self.writer and payload:
            self.writer.write((json.dumps(payload) + "\n").encode())
            await self.writer.drain()

    async def start(self):
        """Starts both the TCP connection and the local UI WebSocket server."""
        if not await self.connect_tcp():
            return

        print(f"Starting UI bridge on ws://127.0.0.1:{self.ws_port}...")
        
        # Start the local WebSocket server to communicate with the browser
        async with websockets.serve(self.handle_ws_client, "127.0.0.1", self.ws_port):
            # Block and listen to the main TCP connection
            await self.listen_tcp()