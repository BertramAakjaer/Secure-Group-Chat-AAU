from flask import Flask, render_template, request, jsonify
import socket
import threading

app = Flask(__name__)

client_socket = None
chat_history = []
chat_lock = threading.Lock()

is_connected = False
username = ''


def append_chat(message):
    with chat_lock:
        chat_history.append(message)


def receive_messages():
    global is_connected, client_socket
    while is_connected and client_socket:
        try:
            raw = client_socket.recv(1024)
            if not raw:
                break

            text = raw.decode('utf-8', errors='replace').strip()
            if text:
                append_chat(text)

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
    return render_template('index.html', connected=is_connected, username=username)


@app.route('/connect', methods=['POST'])
def connect():
    global client_socket, is_connected, username
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

        client_socket = sock
        username = username_value
        is_connected = True

        with chat_lock:
            chat_history.clear()

        threading.Thread(target=receive_messages, daemon=True).start()

        return jsonify({'status': 'success'})

    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)})


@app.route('/send', methods=['POST'])
def send_message():
    global client_socket, is_connected

    if not is_connected or not client_socket:
        return jsonify({'status': 'error', 'message': 'Not connected'})

    data = request.get_json(force=True)
    message_value = (data.get('message') or '').strip()

    if not message_value:
        return jsonify({'status': 'error', 'message': 'Empty message'})

    try:
        client_socket.sendall((message_value + '\n').encode('utf-8'))
        return jsonify({'status': 'success'})
    except Exception as exc:
        is_connected = False
        return jsonify({'status': 'error', 'message': str(exc)})


@app.route('/disconnect', methods=['POST'])
def disconnect():
    global client_socket, is_connected, username
    if client_socket:
        try:
            client_socket.sendall('/quit\n'.encode('utf-8'))
            client_socket.close()
        except Exception:
            pass

    is_connected = False
    client_socket = None
    username = ''
    return jsonify({'status': 'success'})


@app.route('/messages')
def get_messages():
    with chat_lock:
        return jsonify({'messages': list(chat_history)})


if __name__ == '__main__':
    app.run(port=5000, threaded=True)
