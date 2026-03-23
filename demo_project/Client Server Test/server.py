import socket
import threading

HOST = '0.0.0.0'
PORT = 5555

clients = {}  # username -> socket
clients_lock = threading.Lock()


def broadcast(message):
    with clients_lock:
        dead_users = []
        for user, sock in clients.items():
            try:
                sock.sendall(message.encode('utf-8'))
            except Exception:
                dead_users.append(user)

        for user in dead_users:
            clients.pop(user, None)


def recv_line(sock):
    data = sock.recv(1024)
    if not data:
        return None
    return data.decode('utf-8', errors='replace').strip()


def handle_client(client_socket, address):
    username = None
    try:
        username = recv_line(client_socket)
        if not username:
            client_socket.sendall('ERROR: Missing username\n'.encode('utf-8'))
            client_socket.close()
            return

        with clients_lock:
            if username in clients:
                client_socket.sendall('ERROR: Username already exists.\n'.encode('utf-8'))
                client_socket.close()
                return
            clients[username] = client_socket

        broadcast(f"System: {username} has joined the chat.\n")

        while True:
            incoming = recv_line(client_socket)
            if incoming is None:
                break
            if incoming.strip().lower() == '/quit':
                break
            broadcast(f"{username}: {incoming}\n")

    except Exception as exc:
        print(f"[server] client {address} error: {exc}")

    finally:
        if username:
            with clients_lock:
                if username in clients:
                    clients.pop(username, None)
                    broadcast(f"System: {username} has left the chat.\n")
        client_socket.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((HOST, PORT))
    server.listen(10)
    
    print(f"Server listening on {HOST}:{PORT}...")

    try:
        while True:
            client_socket, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server.close()


if __name__ == '__main__':
    start_server()