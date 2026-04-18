import socket
import threading

from common.config import SERVER_BUFFER, SERVER_SOCKET_TIMEOUT
from common.utils import random_user_uid
from common.json_pcks import new_UUID_packet


clients = {} #  uuid-> (conn, addr)


def broadcast_msg(message, sender_conn):
    for uid, (conn, addr) in list(clients.items()): # Getting all connentions from the clients
        if conn != sender_conn:
            try:
                conn.sendall(message)
            except Exception:
                print("[ERROR] Failed to send to a client. Removing from list.")
                conn.close()
                del clients[uid]
                


# Thread that runs for each client
def handle_client(conn, addr, client_uuid):
    print(f"[NEW CONNECTION] {addr} connected.")
    
    
    try:
        conn.sendall(new_UUID_packet(client_uuid))
    
        while True:
            try:
                data = conn.recv(SERVER_BUFFER)
                
                # If no data, the client disconnected
                if not data:
                    break
                
                # Log the message to the server console
                print(f"[MESSAGE from {addr}]")
                
                # Broadcast the raw data to everyone else
                broadcast_msg(data, conn)
                
            except ConnectionResetError:
                break
            
            except Exception as e:
                print(f"[ERROR] Connection lost with {addr}: {e}")
                break
    finally: # Cleanup
        print(f"[DISCONNECTED] {addr} disconnected.")
        if client_uuid in clients:
            del clients[client_uuid]
        conn.close()



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
            
            clients[temp_uuid] = (conn, addr)
            
            thread = threading.Thread(target=handle_client, args=(conn, addr, temp_uuid), daemon=True)
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {len(clients)}")
                
    except KeyboardInterrupt:
        print("\n[STOPPING] Server is shutting down...")
    finally:
        # Stopping all earlier connections
        for client in clients:
            client.close()
        server.close()
        print("[OFFLINE] Server closed.")