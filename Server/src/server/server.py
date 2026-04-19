import socket
import threading

from common.config import SERVER_SOCKET_TIMEOUT
from common.utils import random_user_uid

import server.connection as connection

def start_server(ip, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Frees up the used port better after closing
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((ip, port))
    server.listen()
    server.settimeout(SERVER_SOCKET_TIMEOUT)
    
    print(f"[STARTING] Server is starting on {ip}:{port}")
        
    try:
        while True:
            try:
                conn, addr = server.accept()
            except socket.timeout:
                continue
            
            temp_uuid = random_user_uid()
            
            thread = threading.Thread(target=connection.handle_client, args=(conn, addr, temp_uuid), daemon=True)
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {len(connection.clients)}")
                
    except KeyboardInterrupt:
        print("\n[STOPPING] Server is shutting down...")
    finally:
        # Stopping all earlier connections
        for client_uuid in list(connection.clients.keys()):
            client_conn = connection.clients[client_uuid][0]
            client_conn.close()
        server.close()
        print("[OFFLINE] Server closed.")