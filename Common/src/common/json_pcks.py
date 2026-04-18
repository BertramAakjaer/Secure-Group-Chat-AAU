from common.utils import PackageType
import json


def new_UUID_packet(UUID):
    packet = {
        "Type": PackageType.NEW_UUID.value,
        "Payload": {"UUID": UUID},
    }
    
    json_output = json.dumps(packet, indent=4)
    return json_output.encode('utf-8')


def from_json(json_msg) -> dict:
    original_structure = json.loads(json_msg)
    return original_structure