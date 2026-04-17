from flask import Flask, render_template, request, jsonify
import socket
import threading
import json
import os

from common.utils import PackageType

app = Flask(__name__)


client_socket = None
chat_history = {}  # group_uuid -> list of messages
chat_lock = threading.Lock()

is_connected = False
username = ''
user_uuid = ''
current_group = None
groups = {}  # group_uuid -> name

CONFIG_FILE = "config.json"
CHATS_DIR = "../../../Group-Chats"  # Shared with server



def load_config():
    """Load user config (UUID and username) from file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    return None


def save_config(uuid, username):
    """Save user config to file."""
    config = {
        'uuid': uuid,
        'username': username
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")


def load_group_info(group_uuid):
    """Load group info from shared file."""
    path = os.path.join(CHATS_DIR, f"{group_uuid}_info.json")
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading group info: {e}")
    return None


def load_group_messages(group_uuid):
    """Load group messages from shared file."""
    path = os.path.join(CHATS_DIR, f"{group_uuid}_messages.json")
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading messages: {e}")
    return []


def load_all_groups():
    """Load all groups from shared folder."""
    groups = {}
    if os.path.exists(CHATS_DIR):
        try:
            for filename in os.listdir(CHATS_DIR):
                if filename.endswith("_info.json"):
                    group_uuid = filename.replace("_info.json", "")
                    info = load_group_info(group_uuid)
                    if info:
                        groups[group_uuid] = info['name']
        except Exception as e:
            print(f"Error loading groups: {e}")
    return groups


def start_client(port):
    app.run(port=5000, threaded=True)

def append_chat(group_uuid, message):
    with chat_lock:
        if group_uuid not in chat_history:
            chat_history[group_uuid] = []
        chat_history[group_uuid].append(message)


def receive_messages():
    global is_connected, client_socket, groups, current_group, user_uuid
    while is_connected and client_socket:
        try:
            raw = client_socket.recv(1024)
            if not raw:
                break

            text = raw.decode('utf-8', errors='replace').strip()
            if text:
                if text.startswith('GROUP:'):
                    _, group_uuid, message = text.split(':', 2)
                    append_chat(group_uuid, message)
                elif text.startswith('GROUP_CREATED:'):
                    _, group_uuid, group_name = text.split(':', 2)
                    with chat_lock:
                        groups[group_uuid] = group_name
                        if current_group is None:
                            current_group = group_uuid
                elif text.startswith('GROUP_ADDED:'):
                    _, group_uuid, group_name = text.split(':', 2)
                    with chat_lock:
                        groups[group_uuid] = group_name
                        if current_group is None:
                            current_group = group_uuid
                elif text.startswith('UUID:'):
                    user_uuid = text[5:]
                elif text.startswith('ERROR:'):
                    append_chat('system', text)  # or handle differently
                else:
                    append_chat('system', text)  # fallback

                if text.startswith('ERROR:'):
                    is_connected = False
                    break

        except Exception:
            break

    is_connected = False
    if client_socket:
        try:
            client_socket.close()
        except Exception:
            pass


@app.route('/')
def index():
    return render_template('index.html', connected=is_connected, username=username, user_uuid=user_uuid, groups=groups, current_group=current_group)


@app.route('/connect', methods=['POST'])
def connect():
    global client_socket, is_connected, username, user_uuid, current_group, groups
    data = request.get_json(force=True)

    if is_connected:
        return jsonify({'status': 'already connected'})

    username_value = (data.get('username') or '').strip()
    server_ip = (data.get('ip') or '').strip() or '127.0.0.1'

    if not username_value:
        return jsonify({'status': 'error', 'message': 'Username required'})

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_ip, 5555))
        sock.sendall((username_value + '\n').encode('utf-8'))

        # Wait for UUID
        response = sock.recv(1024).decode('utf-8', errors='replace').strip()
        if not response.startswith('UUID:'):
            sock.close()
            return jsonify({'status': 'error', 'message': 'Failed to get UUID'})

        client_socket = sock
        username = username_value
        user_uuid = response[5:]
        is_connected = True
        current_group = None
        groups = {}

        # Save config for future use
        save_config(user_uuid, username)

        with chat_lock:
            chat_history.clear()

        threading.Thread(target=receive_messages, daemon=True).start()

        return jsonify({'status': 'success', 'uuid': user_uuid})

    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)})


@app.route('/send', methods=['POST'])
def send_message():
    global client_socket, is_connected, current_group, username

    if not is_connected or not client_socket:
        return jsonify({'status': 'error', 'message': 'Not connected'})

    data = request.get_json(force=True)
    message_value = (data.get('message') or '').strip()
    group_uuid = data.get('group')

    if not message_value:
        return jsonify({'status': 'error', 'message': 'Empty message'})

    if not group_uuid:
        return jsonify({'status': 'error', 'message': 'No group selected'})

    try:
        # Local echo immediately for smooth UX
        with chat_lock:
            append_chat(group_uuid, f"{username}: {message_value}")

        client_socket.sendall(f"{group_uuid}:{message_value}\n".encode('utf-8'))
        return jsonify({'status': 'success'})
    except Exception as exc:
        is_connected = False
        return jsonify({'status': 'error', 'message': str(exc)})


@app.route('/disconnect', methods=['POST'])
def disconnect():
    global client_socket, is_connected, username, user_uuid, current_group, groups
    if client_socket:
        try:
            client_socket.sendall('/quit\n'.encode('utf-8'))
            client_socket.close()
        except Exception:
            pass

    is_connected = False
    client_socket = None
    username = ''
    user_uuid = ''
    current_group = None
    groups = {}
    with chat_lock:
        chat_history.clear()
    return jsonify({'status': 'success'})


@app.route('/create_group', methods=['POST'])
def create_group():
    global client_socket, is_connected
    if not is_connected or not client_socket:
        return jsonify({'status': 'error', 'message': 'Not connected'})

    data = request.get_json(force=True)
    group_name = (data.get('name') or '').strip()

    if not group_name:
        return jsonify({'status': 'error', 'message': 'Group name required'})

    try:
        client_socket.sendall(f":/create {group_name}\n".encode('utf-8'))
        return jsonify({'status': 'success'})
    except Exception as exc:
        is_connected = False
        return jsonify({'status': 'error', 'message': str(exc)})


@app.route('/add_user', methods=['POST'])
def add_user():
    global client_socket, is_connected, current_group
    if not is_connected or not client_socket:
        return jsonify({'status': 'error', 'message': 'Not connected'})

    if not current_group:
        return jsonify({'status': 'error', 'message': 'No group selected'})

    data = request.get_json(force=True)
    target_uuid = (data.get('uuid') or '').strip()

    if not target_uuid:
        return jsonify({'status': 'error', 'message': 'UUID required'})

    try:
        client_socket.sendall(f"{current_group}:/add {target_uuid}\n".encode('utf-8'))
        return jsonify({'status': 'success'})
    except Exception as exc:
        is_connected = False
        return jsonify({'status': 'error', 'message': str(exc)})


@app.route('/messages')
def get_messages():
    group_uuid = request.args.get('group')
    if not group_uuid:
        return jsonify({'error': 'group query parameter required'}), 400

    messages = load_group_messages(group_uuid)
    # Format messages for display
    formatted_messages = [f"{msg['user']}: {msg['text']}" for msg in messages]
    
    return jsonify({'messages': formatted_messages})


@app.route('/groups')
def get_groups():
    """Load groups from shared file storage."""
    groups = load_all_groups()
    return jsonify(groups)


@app.route('/load-config')
def load_config_route():
    """Load user's saved config."""
    config = load_config()
    if config:
        return jsonify({
            'status': 'success',
            'uuid': config.get('uuid'),
            'username': config.get('username')
        })
    else:
        return jsonify({'status': 'no_config'})