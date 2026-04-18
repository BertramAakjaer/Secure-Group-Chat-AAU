from flask import Flask, render_template, request, jsonify
import socket, threading, json, os, time

from common.utils import PackageType
from common.json_pcks import from_json
from common.config import CLIENT_BUFFER

import client.modules.data_structs as data_structs


app = Flask(__name__)

client_socket = None
tcp_listening_thread = None

session = data_structs.SessionInfo()


def recv_data(sock):
    try:
        data = sock.recv(CLIENT_BUFFER)
        if not data:
            session.messages.append("System: Connection closed by server.")
        
        # Return Message
        return data.decode('utf-8')
    except Exception as e:
        if session.is_connected:
            session.messages.append(f"System Error: {str(e)}")


# Created in a new thread when connection is made for the server
def tcp_listener(sock):
    global client_socket
    
    while session.is_connected:
        data = recv_data(sock)
        if data:
            session.messages.append(data)
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




@app.route('/')
def index():
    return render_template('index.html')




@app.route('/connect', methods=['POST'])
def connect():
    global client_socket, tcp_listening_thread
    
    data = request.json
    session.server_ip = str(data.get('ip'))
    session.username = str(data.get('username'))
    
    # Checks and removes earlier conenction for safety
    if session.is_connected and client_socket:
        session.is_connected = False
        client_socket.close()
        
    try:
        # Making new socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0) # Tries for 3 seconds on first TCP 3-way
        sock.connect((session.server_ip, session.server_port))
        sock.settimeout(None) # Remvoes the timeout for data transfers
        
        # Update session info and saving socket
        client_socket = sock
        
        while True:
            data = recv_data(sock)
            if data:
                json = from_json(data)
                if json.get("Type") == PackageType.NEW_UUID.value:
                    session.uuid = json.get("Payload", {}).get("UUID", "unknown")
                    break
        
        session.is_connected = True
        session.messages = [f"System: Connected to {session.server_ip} as {session.username}"]
        
        # Spawn the listening thread
        tcp_listening_thread = threading.Thread(target=tcp_listener, args=(sock,), daemon=True)
        tcp_listening_thread.start()
        
        return jsonify({
            "status": "success", 
            "uuid": session.uuid,
            "username": session.username
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400



# Message updates for the UI
@app.route('/poll', methods=['GET'])
def poll():
    return jsonify({
        'messages': session.messages,
        'connected': session.is_connected
    })




@app.route('/send', methods=['POST'])
def send():
    data = request.json
    msg = data.get('message', '')
    
    if msg and session.is_connected and client_socket:
        try:
            formatted_msg = f"[{session.username}] {msg}"
            client_socket.sendall(formatted_msg.encode('utf-8'))
            
            session.messages.append(f"You: {msg}")
            
            return jsonify({"status": "sent"})
        
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500
            
    return jsonify({"status": "failed", "reason": "Not connected or empty message"}), 400





def start_client(port):
    app.run(debug=True, port=port, use_reloader=False)