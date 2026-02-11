import asyncio
import json
from aioconsole import ainput

from common.utils import PackageType

class Client:
    def __init__(self, username, server_ip="127.0.0.1", server_port=8888):
        self.username = username
        self.user_id = None
        
        self.server_ip = server_ip
        self.server_port = server_port
        
        self.reader = None
        self.writer = None
        
        self.running = True

    async def connect(self): # Opretter en connection til serveren via asyncio
        try:
            self.reader, self.writer = await asyncio.open_connection(self.server_ip, self.server_port)
            
            msg = json.dumps({"username": self.username}) + "\n" # Laver til json
            self.writer.write(msg.encode()) # Laver til rå bytes
            await self.writer.drain() # Venter på at "write" er færdig
            
            print(f"Connected as {self.username}")
            return True
        
        except Exception as e: # Hvis connection fejler
            print(f"Connection failed: {e}")
            return False


    async def start(self): # Kører selve logikken
        if not await self.connect(): # Opretter connection og tjekker om det var succesfuldt
            return

        # Kører både den der lytter til inkommende beskeder
        # samt den del der lader en bruger inskrive beskeder
        await asyncio.gather(
            self.listen_for_messages(),
            self.handle_user_input()
        )


    async def listen_for_messages(self): # lytter efter inkommende pakker
        while self.running:
            try:
                data = await self.reader.readline() # Hvis intet data kan læses er forbindelsen til serven stoppet
                if not data:
                    print("\nDisconnected from server !!")
                    self.running = False
                    break
                
                message = json.loads(data.decode()) # Tager bytes læst fra serveren om omdanner til python string og derefter fra string(json) til dict.
                self.process_incoming_message(message)
                
            except Exception as e:
                print(f"Network error: {e}")
                self.running = False
                break


    def process_incoming_message(self, msg):
        try:
            type = msg.get("type")
            sender = msg.get("sender")
            content = msg.get("content")
            
            match type:
                case PackageType.WELCOME:
                    print(f"\n[MLS] WELCOME received from {sender}. Joining group...")
                    # Logic: Initialize local group state from content
                
                case PackageType.COMMIT:
                    print(f"\n[MLS] Group Update (Commit) from {sender}.")
                    # Logic: Update local Ratchet Tree
                    
                case PackageType.MSG:
                    print(f"\n[{sender}]: {content}")
        
        except Exception as e:
            print(f"Error when finding Package type {e}")
        
        print(">> ", end="", flush=True)

    async def handle_user_input(self):
        while self.running:
            msg_content = await ainput(">> ")
            if not msg_content: continue

            await self.process_user_command(msg_content)

    async def process_user_command(self, content):
        payload = {}

        if content.startswith("/add"): # adding a new user
            parts = content.split(" ")
            if len(parts) > 1:
                target = parts[1]
                payload = {
                    "type": PackageType.WELCOME,
                    "dest": target,
                    "content": f"KeyPackage-For-{target}"
                }
            else:
                print("Usage: /add <userid>")
                return

        elif content == "/exit": # Exiting the group
            self.running = False
            return

        else:
            # Regular chat message
            payload = {
                "type": "MSG",
                "dest": "all",
                "content": content
            }

        # Send
        if self.writer:
            self.writer.write((json.dumps(payload) + "\n").encode())
            await self.writer.drain()