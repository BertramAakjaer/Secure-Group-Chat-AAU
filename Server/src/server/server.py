import asyncio
import json
import logging
import socket

from common.utils import gen_random_uid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.clients = {}  # hash map af user_id og dens "writer" tcp connection
        self.name_uid_map = {} # hash map of name and user_id

    async def start(self): # Initialiserer serveren og starter med at lytte efter inkommende trafik
        server = await asyncio.start_server(self.handle_client, self.ip, self.port)
        
        display_ip = self.ip
        
        if self.ip == "0.0.0.0": # Finder "hosts" ip addresse for at kunne vise hvilken der skal forbindes til
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80)) # Google DNS
                    display_ip = s.getsockname()[0]
            except Exception:
                display_ip = "127.0.0.1"

        logging.info(f"MLS Delivery Service running on {display_ip}:{self.port}")
                
        async with server:
            await server.serve_forever()
    

    async def handle_client(self, reader, writer):
        username = None
        user_id = None
        addr = writer.get_extra_info('peername')
        
        try:
            # Første besked en klient sender er deres username
            data = await reader.readline()
            if not data:
                return
            
            reg_msg = json.loads(data.decode())
            username = reg_msg.get("username")
            
            if not username: # Hvis der ikke blev sendt et username
                logging.warning(f"Connection from {addr} missing username. Closing.")
                return
            elif username in self.name_uid_map: # Hvis det username allerede existerer
                logging.warning(f"Connection from {addr} already existing name: '{username}'. Closing.")
                username = None
                return
            
            user_id = gen_random_uid() # Opretter et tilfældigt user id
            while user_id in self.clients: # Generating userid
                user_id = gen_random_uid()

            self.name_uid_map[username] = user_id
            self.clients[user_id] = writer
            
            
            logging.info(f"[+] User '{username}' connected from {addr} and got the UID: {user_id}")

            # Loop til at læse om der er beskeder fra en klient
            while True:
                data = await reader.readline()
                if not data: # En klient er offline
                    break 
                
                message = json.loads(data.decode())
                
                # Gemmer kontekst af hvem der sendte beskeden
                message["sender"] = username
                
                # Sender besked til andre klienter
                await self.route_message(message)

        except ConnectionResetError:
            logging.warning(f"[-] User '{user_id}' connection reset.")
        except Exception as e:
            logging.error(f"Error with client {user_id}: {e}")
            
        finally: # Sker lige meget hvad om en conenction crasher
            self._disconnect(user_id, username, writer)



    async def route_message(self, message):
        target = message.get("dest")
        sender = message.get("sender")
        payload = json.dumps(message) + "\n"
        encoded_payload = payload.encode()

        if target == "all":
            # Sender til alle
            sender_uid = self.name_uid_map[sender]
            
            for uid, writer in self.clients.items():
                if uid != sender_uid:
                    try:
                        writer.write(encoded_payload)
                        await writer.drain()
                    except Exception as e:
                        logging.error(f"Failed to send to {uid}: {e}")

        elif target in self.clients:
            # Sender til en specific person
            try:
                writer = self.clients[target]
                writer.write(encoded_payload)
                await writer.drain()
            except Exception as e:
                logging.error(f"Failed to send to {target}: {e}")



    def _disconnect(self, user_id, username, writer):
        if username:
            del self.name_uid_map[username]
            logging.info(f"[-] User '{username}' disconnected")
        if user_id:
            del self.clients[user_id]
        
        writer.close()
