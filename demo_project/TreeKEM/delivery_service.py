import json
import util

from _client import Client

def _get_new_group_data(admin_id: str, group_id: str):
    welcome_msg = {
        "header": "WELCOME",
        "group_id": group_id,
        "users": {
            admin_id: 0,
            }
        }
    return welcome_msg

class GroupChat:
    def __init__(self, admin_id: str, group_id: str):
        self.admin_id: str = admin_id # User ID
        self.group_id: str = group_id
        
        self.epoch_counter: int
        
        
class DeliveryService:
    def __init__(self):
        self._username_n_uid: dict[str, str]
        self.connected_clients: dict[str, Client]
        self.group_chats: dict[str, GroupChat]
        
    def add_new_group(self, admin_id):
        temp_group_id = util.gen_random_gid()
        self.group_chats[temp_group_id] = GroupChat(admin_id, temp_group_id)
        self.connected_clients[admin_id].process_msg(_get_new_group_data(admin_id, temp_group_id))
    
    def add_new_client(self, client_name):
        temp_user_id = util.gen_random_uid()
        self._username_n_uid[client_name] = temp_user_id
        self.connected_clients[temp_user_id] = Client(client_name, temp_user_id, self)
    
    def get_user_id(self, username: str) -> str:
        return self._username_n_uid[username]
        