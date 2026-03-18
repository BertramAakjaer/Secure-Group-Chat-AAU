import json

import util

from rachet_tree import Tree

class GroupChat:
    def __init__(self):
        self.tree: None | Tree = None
        self.initial_secret = util.gen_new_leaf_seed()
            
    def welcome_tree(self, welcome_msg, user_id):
        self.tree = Tree(user_id, self.initial_secret, welcome_msg)


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
    
    
    def _init_group(self, gid):
        self.group_chats[gid] = GroupChat()
        
    def request_join_group(self, gid):
        self._init_group(gid)
        _, pub_key = util.derive_keypair_from_seed(self.group_chats[gid].initial_secret)
        self.ds.request_to_join(gid, self.uid, pub_key)
    
    
    def add_new_user(self, gid, new_uid, pub_key):
        tree = self.group_chats[gid].tree
        
        if tree:
            tree.add_new_user(new_uid, pub_key)


    def process_msg(self, msg):
        match msg["header"]:
            case "WELCOME":
                self.group_chats[msg["group_id"]].welcome_tree(msg, self.uid)
            case _:
                print("Header not defined!!")