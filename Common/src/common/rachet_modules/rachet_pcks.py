from enum import Enum
import json, base64


class RachetTypes(str, Enum):
    WELCOME = "WELCOME"
    COMMIT = "COMMIT"


# Packet only handeled by rachet module - - - - - -

def from_rachet_packet(packet):
    base64_data =   base64.b64decode(packet)
    json_data =     base64_data.decode('utf-8')
    dict_data =     json.loads(json_data)
    
    return dict_data
    
    
def _to_rachet_packet(packet):
    json_output =   json.dumps(packet, indent=4)
    bytes =         json_output.encode('utf-8')
    base64_output = base64.b64encode(bytes)
    
    return base64_output

# - - - - - -

def welcome_packet(epoch, tree_state, encrypted_root):
    packet = {
        "Type": RachetTypes.WELCOME.value,
        "Payload": {
            "epoch": epoch,
            "tree_state": tree_state,
            "encrypted_root": encrypted_root,
        },
    }
    return _to_rachet_packet(packet)



def commit_packet(operations, epoch):
    packet = {
        "Type": RachetTypes.COMMIT.value,
        "Payload": {
            "operations": operations,
            "epoch": epoch,
        },
    }
    return _to_rachet_packet(packet)