from flask import Flask, render_template, request, jsonify

import client.connection as connection

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/connect', methods=['POST'])
def connect():
    data = request.json
    ip = str(data.get('ip'))
    username = str(data.get('username'))
    
    result = connection.connect_to_server(ip, username)
    return jsonify(result)


@app.route('/create_group', methods=['POST'])
def create_group():
    data = request.json
    group_name = str(data.get('group_name', ''))
    
    if not group_name:
        return jsonify({"status": "error", "message": "Group name required"}), 400
    
    result = connection.create_group(group_name)
    return jsonify(result)


@app.route('/join_group', methods=['POST'])
def join_group():
    data = request.json
    group_uuid = str(data.get('group_uuid', ''))
    
    if not group_uuid:
        return jsonify({"status": "error", "message": "Group UUID required"}), 400
    
    result = connection.join_group(group_uuid)
    return jsonify(result)


# Message updates for the UI
@app.route('/poll', methods=['GET'])
def poll():
    return jsonify({
        'messages': connection.session.messages,
        'connected': connection.session.is_connected,
        'waiting': connection.session.is_waiting,
        'group_uuid': connection.session.group_uuid,
        'group_name': connection.session.group_name
    })


@app.route('/send', methods=['POST'])
def send():
    data = request.json
    msg = data.get('message', '')
    
    result = connection.send_message(msg)
    return jsonify(result)