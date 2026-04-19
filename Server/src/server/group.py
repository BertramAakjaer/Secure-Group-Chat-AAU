from common.json_pcks import group_created_packet, join_requested_packet, join_accepted_packet, join_denied_packet, group_msg_packet, join_request_to_admin_packet, commit_packet
from common.utils import random_group_uid
from common.network_utils import send_big


# groups: group_uuid -> {'admin': uuid, 'name': str, 'members': set(uuids), 'pending': set(uuids)}
# admin = den der styrer gruppen
# name = gruppens navn
# members = siger sig selv
# pending = brugere der har anmodet om at blive medlem
groups = {}

# clients: uuid -> (conn, addr, group_uuid, username)
# Kopi heraf bruges også i connection.py (de refererer til hinanden)
clients = {}


# Helper functions - - - -

# Send packet to specific uuid
def _send_to_uuid(target_uuid, packet):
    if target_uuid not in clients:
        return False

    conn = clients[target_uuid][0]
    try:
        send_big(conn, packet)
        return True
    except Exception:
        print(f"[ERROR] Failed to send packet to {target_uuid}")
        return False

    

# Group related functions - - - -


def create_group(group_name, admin_uuid):
    group_uuid = random_group_uid()
    groups[group_uuid] = {
        'admin': admin_uuid,
        'name': group_name,
        'members': {admin_uuid},
        'pending': set()
    }
    clients[admin_uuid] = (clients[admin_uuid][0], clients[admin_uuid][1], group_uuid, clients[admin_uuid][3])
    
    # Send confirmation to admin
    packet = group_created_packet(group_uuid, group_name)
    _send_to_uuid(admin_uuid, packet)
    print(f"[GROUP CREATED] {group_name} ({group_uuid}) by {admin_uuid}")



def request_join_group(group_uuid, user_uuid, pub_key_b64):
    
    # If group is not found = just insta deny
    if group_uuid not in groups:
        packet = join_denied_packet()
        _send_to_uuid(user_uuid, packet)
        return
    
    # Add user as pending to the group
    groups[group_uuid]['pending'].add(user_uuid)
    clients[user_uuid] = (clients[user_uuid][0], clients[user_uuid][1], None, clients[user_uuid][3])
    
    # Send request confirmation to user requesting to join
    packet = join_requested_packet()
    _send_to_uuid(user_uuid, packet)
    
    # Sending the request to the admin
    admin_uuid = groups[group_uuid]['admin']
    
    if admin_uuid in clients:
        request_join_packet = join_request_to_admin_packet(pub_key_b64, user_uuid, clients[user_uuid][3])
        _send_to_uuid(admin_uuid, request_join_packet)
    
    print(f"[JOIN REQUEST] {user_uuid} requested to join {group_uuid}")



def accept_join(group_uuid, target_uuid, admin_uuid, welcome_data):
    # If group exists and admin is actual admin
    if group_uuid not in groups or groups[group_uuid]['admin'] != admin_uuid:
        return False
    
    
    if target_uuid in groups[group_uuid]['pending']:
        groups[group_uuid]['pending'].remove(target_uuid)
        groups[group_uuid]['members'].add(target_uuid)
        clients[target_uuid] = (clients[target_uuid][0], clients[target_uuid][1], group_uuid, clients[target_uuid][3])
        
        # Send accept to user
        packet = join_accepted_packet(group_uuid, groups[group_uuid]['name'], welcome_data, target_uuid)
        _send_to_uuid(target_uuid, packet)
        
        # Send join message to group
        broadcast_to_group(group_uuid, f"User {target_uuid} joined the group.", "SYSTEM")
        print(f"[JOIN ACCEPTED] {target_uuid} joined {group_uuid}")
        return True
    return False



def deny_join(group_uuid, target_uuid, admin_uuid):
    if group_uuid not in groups or groups[group_uuid]['admin'] != admin_uuid:
        return False
    
    if target_uuid in groups[group_uuid]['pending']:
        groups[group_uuid]['pending'].remove(target_uuid)
        
        # Send denial to user
        packet = join_denied_packet()
        _send_to_uuid(target_uuid, packet)
        
        print(f"[JOIN DENIED] {target_uuid} denied for {group_uuid}")
        return True
    return False



def broadcast_to_group(group_uuid, message, sender_uuid, epoch=None):
    if group_uuid not in groups:
        return
    
    username = ""

    # Chekcs if senders is in the group
    if sender_uuid != "SYSTEM":
        if sender_uuid not in groups[group_uuid]['members']:
            return
        if sender_uuid not in clients or clients[sender_uuid][2] != group_uuid:
            return
        
        if sender_uuid in clients:
            username = clients[sender_uuid][3]
    else:
        username = "SYSTEM"
        
    # Sends packet to all members
    packet = group_msg_packet(message, sender_uuid, group_uuid, epoch, username)
    for member_uuid in groups[group_uuid]['members']:
        if member_uuid == sender_uuid:
            continue
        if member_uuid in clients and clients[member_uuid][2] == group_uuid:
            _send_to_uuid(member_uuid, packet)


# Admin command handling - - - -

# Done with !command arg
def handle_admin_command(message, sender_uuid):
    parts = message.strip().split()
    if len(parts) < 2:
        return False
    
    command = parts[0].lower()
    target_uuid = parts[1]
    
    # Find the group where sender is admin
    sender_group = None
    for g_uuid, g_data in groups.items():
        if g_data['admin'] == sender_uuid:
            sender_group = g_uuid
            break
    
    if not sender_group:
        return False
    
    elif command == "!deny":
        deny_join(sender_group, target_uuid, sender_uuid)
        return True
    
    return False


# Helper function to remove client
def remove_client(uuid):
    if uuid in clients:
        group_uuid = clients[uuid][2]
        if group_uuid and group_uuid in groups:
            if uuid in groups[group_uuid]['members']:
                groups[group_uuid]['members'].remove(uuid)
                broadcast_to_group(group_uuid, f"User {uuid} left the group.", "SYSTEM")
            elif uuid in groups[group_uuid]['pending']:
                groups[group_uuid]['pending'].remove(uuid)
        del clients[uuid]
        
        
        
# Rachet commit handling - - - -
def handle_commit(guid, commit_data, sender_uuid):
    for group_uuid, group_data in groups.items():
        if guid == group_uuid:
            admin = group_data['admin']
            if sender_uuid != admin:
                return
            
            for member_uuid in group_data['members']:
                if member_uuid == sender_uuid:
                    continue
                if member_uuid in clients and clients[member_uuid][2] == group_uuid:
                    packet = commit_packet(guid, commit_data)
                    _send_to_uuid(member_uuid, packet)