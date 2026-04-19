import socket, threading, json, time

from common.utils import PackageType
from common.json_pcks import from_json, user_info_packet, group_msg_packet, create_group_packet, join_group_packet
from common.config import CLIENT_BUFFER

import client.data_structs as data_structs


client_socket = None
tcp_listening_thread = None

session = data_structs.SessionInfo()

# Modtagning a TCP data
def recv_data(sock):
    try:
        data = sock.recv(CLIENT_BUFFER)
        if not data:
            session.messages.append("System: Connection closed by server.")
        
        # Return Message
        return data
    
    except Exception as e:
        if session.is_connected:
            session.messages.append(f"System Error: {str(e)}")


def send_packet(packet, sock=None):
    target = sock if sock is not None else client_socket
    if not target:
        return False

    try:
        target.sendall(packet)
        return True
    except Exception as e:
        if session.is_connected:
            session.messages.append(f"System Error: {str(e)}")
        return False


# Created in a new thread when connection is made for the server
def tcp_listener(sock):
    global client_socket # For at den kan ændres
    
    while session.is_connected:
        data = recv_data(sock)
        if data:
            handle_incoming_message(data)
        else:
            break
            
    # Cleanup state when the connection drops
    session.is_connected = False
    if client_socket:
        try:
            client_socket.close()
        except:
            pass
    client_socket = None


# Checks msg header and chooses how to handle it
def handle_incoming_message(data):
    try:
        json_data = from_json(data)
        msg_type = json_data.get("Type")
        payload = json_data.get("Payload", {})
        
        match msg_type:
            case PackageType.GROUP_CREATED.value:
                session.group_uuid = payload.get("group_uuid")
                session.group_name = payload.get("group_name")
                session.messages.append(f"System: Group '{session.group_name}' created with ID {session.group_uuid}")
                session.is_waiting = False
            
            case PackageType.JOIN_REQUESTED.value:
                session.messages.append("System: Join request sent. Waiting for approval...")
                session.is_waiting = True
            
            case PackageType.JOIN_ACCEPTED.value:
                session.group_uuid = payload.get("group_uuid")
                session.group_name = payload.get("group_name")
                session.messages.append(f"System: Joined group '{session.group_name}'")
                session.is_waiting = False
            
            case PackageType.JOIN_DENIED.value:
                session.messages.append("System: Join request denied.")
                session.is_waiting = False
            
            case PackageType.MSG.value:
                message = payload.get("message", "")
                username = payload.get("username", payload.get("sender_uuid", "Unknown"))
                session.messages.append(f"[{username}] {message}")
    
    except json.JSONDecodeError:
        # Shouldn't happen but just in case
        session.messages.append(data)


def connect_to_server(ip, username):
    global client_socket, tcp_listening_thread
    
    session.server_ip = ip
    session.username = username
    
    # Checks and removes earlier connection for safety
    if session.is_connected and client_socket:
        session.is_connected = False
        client_socket.close()
        
    try:
        # Making new socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0) # Tries for 3 seconds on first TCP 3-way
        sock.connect((session.server_ip, session.server_port))
        sock.settimeout(None) # Removes the timeout for data transfers
        
        # Update session info and saving socket
        client_socket = sock
        
        while True:
            data = recv_data(sock)
            if data:
                json_data = from_json(data)
                if json_data.get("Type") == PackageType.NEW_UUID.value:
                    session.uuid = json_data.get("Payload", {}).get("UUID", "unknown")
                    
                    # Send username for server
                    # UUID sendes også men bruges egentligt ik af serveren
                    packet = user_info_packet(session.uuid, session.username)
                    send_packet(packet, sock)
                    break
        
        session.is_connected = True
        session.messages = [f"System: Connected to {session.server_ip} as {session.username}"]
        
        # Spawn the listening thread
        tcp_listening_thread = threading.Thread(target=tcp_listener, args=(sock,), daemon=True)
        tcp_listening_thread.start()
        
        return {"status": "success", "uuid": session.uuid, "username": session.username}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def send_message(msg):
    if msg and session.is_connected and client_socket:
        try:
            if session.group_uuid:
                packet = group_msg_packet(msg, session.uuid, session.group_uuid, session.username)
                send_packet(packet)
                
            # Shows the message for the sender
            session.messages.append(f"You: {msg}")
            
            return {"status": "sent"}
        
        except Exception as e:
            return {"status": "error", "error": str(e)}
            
    return {"status": "failed", "reason": "Not connected or empty message"}


def create_group(group_name):
    if session.is_connected and client_socket and not session.group_uuid:
        try:
            packet = create_group_packet(group_name, session.uuid)
            send_packet(packet)
            
            return {"status": "requested"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    return {"status": "failed", "reason": "Not connected or already in group"}


def join_group(group_uuid):
    if session.is_connected and client_socket and not session.group_uuid:
        try:
            packet = join_group_packet(group_uuid, session.uuid)
            send_packet(packet)
            
            return {"status": "requested"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    return {"status": "failed", "reason": "Not connected or already in group"}