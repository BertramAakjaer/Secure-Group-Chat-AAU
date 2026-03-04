import json

import util

from rachet_tree import Tree

class GroupChat:
    def __init__(self, welcome_msg: dict, user_id: str):
        self.group_id: str = welcome_msg["group_id"]
        self.tree: None | Tree
        
        self._init_gc_variables(welcome_msg, user_id)
    
    def _init_gc_variables(self, welcome_msg, user_id):
        self.tree = Tree(user_id, welcome_msg)


class Client:
    def __init__(self, name: str, uid: str, ds):
        self.name: str = name
        self.uid: str = uid
        self.ds = ds
        
        self.group_chats: dict[str, GroupChat] = {}

        
    def send_group_message(self, plaintext):
        pass
    
    def recieve_group_message(self, ciphertext):
        pass


    def process_welcome(self, msg):
        match msg["header"]:
            case "WELCOME":
                self.group_chats[msg["group_id"]] = GroupChat(msg, self.uid)
            case _:
                print("Header not defined!!")