from common.utils import gen_random_uid

import socket
import threading
import uuid

from datetime import datetime

BUFFER_SIZE = 1024

clients = []

def broadcast_msg(message, sender_conn):
    
    for client in clients.copy():  # Copy so that we can remove clients from the original list
        if client != sender_conn:
            try:
                client.sendall(message)
            except Exception as e:
                print(f"[ERROR] Failed to send to a client. Removing from list.")
                
                if client in clients:
                    clients.remove(client)
                client.close()
                


# Thread that runs for each client
def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    
    while True:
        try:
            data = conn.recv(BUFFER_SIZE)
            
            # If no data, the client disconnected
            if not data:
                break
            
            # Log the message to the server console
            decoded_msg = data.decode('utf-8')
            print(f"[MESSAGE from {addr}]: {decoded_msg}")
            
            # Broadcast the raw data to everyone else
            broadcast_msg(data, conn)
            
        except ConnectionResetError:
            break
        
        except Exception as e:
            print(f"[ERROR] Connection lost with {addr}: {e}")
            break

    # Cleanup
    print(f"[DISCONNECTED] {addr} disconnected.")
    if conn in clients:
        clients.remove(conn)
    conn.close()



def start_server(ip, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Frees up the used port better after closing
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((ip, port))
    server.listen()
    print(f"[STARTING] Server is starting on {ip}:{port}")
        
    try:
        while True:
            conn, addr = server.accept()
            clients.append(conn)
            
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {len(clients)}")
                
    except KeyboardInterrupt:
        print("\n[STOPPING] Server is shutting down...")
    finally:
        # Cleanup: Close all active client connections
        for client in clients:
            client.close()
        server.close()
        print("[OFFLINE] Server closed.")