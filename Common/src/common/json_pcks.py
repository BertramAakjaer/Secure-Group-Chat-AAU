from common.utils import PackageType
import json

# Json Encoding - -

def from_json(packet) -> dict:
    original_structure = json.loads(packet.decode('utf-8'))
    return original_structure

def _to_json(packet):
    json_output = json.dumps(packet, indent=4)
    return json_output.encode('utf-8')



# Json strcuture - -


# Info packets
def new_UUID_packet(UUID): # From server to client with their server givin UUID
    packet = {
        "Type": PackageType.NEW_UUID.value,
        "Payload": {
            "UUID": UUID
        },
    }
    return _to_json(packet)


def user_info_packet(uuid, username):
    packet = {
        "Type": PackageType.USER_INFO.value,
        "Payload": {
            "uuid": uuid,
            "username": username
        },
    }
    return _to_json(packet)







# Group Related packets

def create_group_packet(group_name, admin_uuid):
    packet = {
        "Type": PackageType.CREATE_GROUP.value,
        "Payload": {
            "group_name": group_name,
            "admin_uuid": admin_uuid
        },
    }
    return _to_json(packet)


def join_group_packet(group_uuid, user_uuid, pub_key_b64):
    packet = {
        "Type": PackageType.JOIN_GROUP.value,
        "Payload": {
            "group_uuid": group_uuid,
            "user_uuid": user_uuid,
            "pub_key_b64": pub_key_b64
        },
    }
    return _to_json(packet)


def group_created_packet(group_uuid, group_name): # From server to admin saying the group was created
    packet = {
        "Type": PackageType.GROUP_CREATED.value,
        "Payload": {
            "group_uuid": group_uuid,
            "group_name": group_name
        },
    }
    return _to_json(packet)


def join_requested_packet(): # Send from server to user that their request is waiting for approval
    packet = {
        "Type": PackageType.JOIN_REQUESTED.value,
        "Payload": {},
    }
    return _to_json(packet)

def join_request_to_admin_packet(pub_key_b64, user_uuid, username): # Send from server to admin about a new join request
    packet = {
        "Type": PackageType.JOIN_REQUEST_TO_ADMIN.value,
        "Payload": {
            "pub_key_b64": pub_key_b64,
            "user_uuid": user_uuid,
            "username": username
        },
    }
    return _to_json(packet)


def join_accepted_packet(group_uuid, group_name, welcome_data, accepted_uuid): # From admin to user after accept
    packet = {
        "Type": PackageType.JOIN_ACCEPTED.value,
        "Payload": {
            "group_uuid": group_uuid,
            "group_name": group_name,
            "welcome_data": welcome_data,
            "accepted_uuid": accepted_uuid
        },
    }
    return _to_json(packet)



def join_denied_packet(): # From server to user after deny
    packet = {
        "Type": PackageType.JOIN_DENIED.value,
        "Payload": {},
    }
    return _to_json(packet)





# Regular Message packet

def group_msg_packet(message, sender_uuid, group_uuid, username=None):
    packet = {
        "Type": PackageType.MSG.value,
        "Payload": {
            "encrypted": False,
            "message": message,
            "sender_uuid": sender_uuid,
            "group_uuid": group_uuid,
            "username": username
        },
    }
    return _to_json(packet)





# Rachet packets - - - - -

def commit_packet(guid, commit_data):
    packet = {
        "Type": PackageType.COMMIT.value,
        "Payload": {
            "guid": guid,
            "commit_data": commit_data,
        },
    }
    return _to_json(packet)