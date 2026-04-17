from common.utils import gen_random_uid

import socket
import threading
import uuid
import json
import os
from datetime import datetime


CHATS_DIR = "Group-Chats"
users = {}  # uuid -> {'name': str, 'socket': socket, 'groups': set()}
users_lock = threading.Lock()
file_lock = threading.Lock()


def init_group_chats_folder():
    """Initialize the Group-Chats folder if it doesn't exist."""
    if not os.path.exists(CHATS_DIR):
        os.makedirs(CHATS_DIR)


def get_group_info_path(group_uuid):
    """Get the path to the group info file."""
    return os.path.join(CHATS_DIR, f"{group_uuid}_info.json")


def get_group_messages_path(group_uuid):
    """Get the path to the group messages file."""
    return os.path.join(CHATS_DIR, f"{group_uuid}_messages.json")


def load_group_info(group_uuid):
    """Load group info from file."""
    with file_lock:
        path = get_group_info_path(group_uuid)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading group info {group_uuid}: {e}")
    return None


def save_group_info(group_uuid, data):
    """Save group info to file."""
    with file_lock:
        path = get_group_info_path(group_uuid)
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving group info {group_uuid}: {e}")


def load_group_messages(group_uuid):
    """Load group messages from file."""
    with file_lock:
        path = get_group_messages_path(group_uuid)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading messages {group_uuid}: {e}")
    return []


def save_group_message(group_uuid, message_text, username):
    """Append a message to the group messages file."""
    with file_lock:
        messages = load_group_messages(group_uuid)
        message_obj = {
            "user": username,
            "text": message_text,
            "timestamp": datetime.now().isoformat()
        }
        messages.append(message_obj)
        path = get_group_messages_path(group_uuid)
        try:
            with open(path, 'w') as f:
                json.dump(messages, f, indent=2)
        except Exception as e:
            print(f"Error saving message {group_uuid}: {e}")


def load_all_groups():
    """Load all group UUIDs from the Group-Chats folder."""
    groups = {}
    with file_lock:
        if os.path.exists(CHATS_DIR):
            for filename in os.listdir(CHATS_DIR):
                if filename.endswith("_info.json"):
                    group_uuid = filename.replace("_info.json", "")
                    info = load_group_info(group_uuid)
                    if info:
                        groups[group_uuid] = info
    return groups


def start_server(ip, port):
    init_group_chats_folder()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((ip, port))
    server.listen(10)
    server.settimeout(1.0)
    
    print(f"Server listening on {ip}:{port}...")
    
    try:
        while True:
            try:
                client_socket, addr = server.accept()
                server.settimeout(None)
                thread = threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True)
                thread.start()
                server.settimeout(1.0)
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server.close()


def recieve_line(sock):
    data = sock.recv(1024)
    if not data:
        return None
    return data.decode('utf-8', errors='replace').strip()


def broadcast(group_uuid, message_text, username):
    """Broadcast a message to all users in a group by writing to file and notifying sockets."""
    # Save message to file
    save_group_message(group_uuid, message_text, username)
    
    # Notify all connected users in this group
    with users_lock:
        group_info = load_group_info(group_uuid)
        if group_info:
            for user_uuid in group_info.get('users', []):
                if user_uuid in users:
                    try:
                        users[user_uuid]['socket'].sendall(f"GROUP:{group_uuid}:{message_text}\n".encode('utf-8'))
                    except Exception:
                        pass  # handle dead users later


def handle_command(cmd, group_uuid, user_uuid, sock, username):
    with users_lock:
        if group_uuid == '':
            if cmd.startswith('/create '):
                group_name = cmd[8:].strip()
                if not group_name:
                    sock.sendall('ERROR: Group name required\n'.encode('utf-8'))
                    return
                group_uuid_new = str(uuid.uuid4())
                
                # Create group info file
                group_info = {
                    'uuid': group_uuid_new,
                    'name': group_name,
                    'admin': user_uuid,
                    'users': [user_uuid]
                }
                save_group_info(group_uuid_new, group_info)
                
                # Create empty messages file
                save_group_message(group_uuid_new, f"System: {username} created the group.", "System")
                
                # Update user's groups
                users[user_uuid]['groups'].add(group_uuid_new)
                sock.sendall(f'GROUP_CREATED:{group_uuid_new}:{group_name}\n'.encode('utf-8'))
            else:
                sock.sendall('ERROR: Invalid command\n'.encode('utf-8'))
        else:
            if cmd.startswith('/add '):
                target_uuid = cmd[5:].strip()
                group_info = load_group_info(group_uuid)
                
                if group_info and user_uuid == group_info.get('admin'):
                    if target_uuid in users:
                        # Update group info file
                        if target_uuid not in group_info['users']:
                            group_info['users'].append(target_uuid)
                            save_group_info(group_uuid, group_info)
                        
                        # Update user's groups
                        users[target_uuid]['groups'].add(group_uuid)
                        users[target_uuid]['socket'].sendall(f'GROUP_ADDED:{group_uuid}:{group_info["name"]}\n'.encode('utf-8'))
                        broadcast(group_uuid, f"System: {users[target_uuid]['name']} has been added to the group.", "System")
                    else:
                        sock.sendall('ERROR: User not found\n'.encode('utf-8'))
                else:
                    sock.sendall('ERROR: Not admin or group not found\n'.encode('utf-8'))
            else:
                sock.sendall('ERROR: Invalid command\n'.encode('utf-8'))


def handle_client(client_socket, address):
    username = None
    user_uuid = None
    try:
        username = recieve_line(client_socket)
        if not username:
            client_socket.sendall('ERROR: Missing username\n'.encode('utf-8'))
            client_socket.close()
            return

        with users_lock:
            user_uuid = str(uuid.uuid4())
            users[user_uuid] = {'name': username, 'socket': client_socket, 'groups': set()}
            
            # Load existing groups and add user to their groups (if needed)
            # For now, just start with empty groups set

        client_socket.sendall(f'UUID:{user_uuid}\n'.encode('utf-8'))

        while True:
            incoming = recieve_line(client_socket)
            if incoming is None:
                break
            parts = incoming.split(':', 1)
            if len(parts) != 2:
                client_socket.sendall('ERROR: Invalid message format\n'.encode('utf-8'))
                continue
            group_uuid, message = parts
            if message.strip().lower() == '/quit':
                break
            if message.startswith('/'):
                handle_command(message, group_uuid, user_uuid, client_socket, username)
            else:
                with users_lock:
                    if group_uuid in users[user_uuid]['groups']:
                        broadcast(group_uuid, message, username)
                    else:
                        client_socket.sendall('ERROR: Not in group\n'.encode('utf-8'))

    except Exception as exc:
        print(f"[server] client {address} error: {exc}")

    finally:
        with users_lock:
            if user_uuid and user_uuid in users:
                # Notify groups that user left
                for group_uuid in list(users[user_uuid]['groups']):
                    group_info = load_group_info(group_uuid)
                    if group_info:
                        group_info['users'].remove(user_uuid)
                        save_group_info(group_uuid, group_info)
                        broadcast(group_uuid, f"System: {users[user_uuid]['name']} has left the group.", "System")
                del users[user_uuid]
        client_socket.close()

