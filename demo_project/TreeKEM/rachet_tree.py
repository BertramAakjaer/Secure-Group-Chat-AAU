import math

import util
from nodes import Node_Member, Node_Own, make_node_owned

# Returns the depth of the tree and number of leaf nodes
def _get_tree_size(n):
    minimum = 8
    maximum = 16384
    
    leaf_nodes = minimum
    
    while (leaf_nodes < n) and (leaf_nodes * 2 <= maximum):
        leaf_nodes *= 2
        
    return (int(math.log2(leaf_nodes)), leaf_nodes)


class Tree:
    def __init__(self, local_uid: str, init_secret, welcome_msg: dict, min_users: int=5):
        self.local_user: str = local_uid
        self.path_user = []
        
        self.tree_depth: int | None
        self.leaf_nodes: int | None
        
        self.root: Node_Own | None
        
        self.users: dict[str, int] = {} # UID til leaf index fra 0..n fra venstre
        
        # Initalisere data der bruges
        self._init_tree(init_secret, min_users, welcome_msg)
        
    
    def _init_tree(self, init_secret, min_users: int, welcome_msg: dict):
        self.tree_depth, self.leaf_nodes = _get_tree_size(min_users)
        
        root_temp = self._create_tree_structure(self.tree_depth)
        if isinstance(root_temp, Node_Own):
            self.root = root_temp
        else:
            raise RuntimeError("Panic: Root node error")
        
        users_data = welcome_msg["users"] # Getting all users and their indecies

        user_found_check: bool = False
        for user_id, index in users_data.items():
            self.fill_leaf(index, user_id)
            self.users[user_id] = index
            
            if self.local_user == user_id:
                user_found_check = True
        
        if not user_found_check:
            raise RuntimeError("Panic: User not in welcome package")
                
        self.path_user = self._set_direct_path_owned(self.users[self.local_user])
        
        if not self.path_user[0].secret:
             if len(self.users) == 1:
                self._init_creator_keys(init_secret)        
    
    
    def _create_tree_structure(self, current_depth: int):
        if current_depth == self.tree_depth:
            node = Node_Own()
        else:
            node = Node_Member()
        
        if not node:
            raise RuntimeError("Panic: Root is not set")
        
        if node:        
            if current_depth == 0:
                node.is_leaf = True
                return node
            
            node.child_a = self._create_tree_structure(current_depth - 1)
            node.child_b = self._create_tree_structure(current_depth - 1)
            
            return node
        
    def _set_direct_path_owned(self, leaf_index: int):
        path = [] # liste af nodes
        choices: list[bool] = []
        
        current = self.root # Starter fra toppen
        target_depth = self.tree_depth # Skal kende dybden
        if not target_depth:
            raise RuntimeError("Panic: Target depth is none")
        
        
        # Går ned af træet, men gemmer alle nodes som er "stien"
        for d in range(target_depth):
            path.append(current)
            
            nodes_at_level = 2 ** (target_depth - d) # Bruges til at beregne den vej næste skridt er
            midpoint = nodes_at_level // 2
            
            if not current:
                raise RuntimeError("Panic: Node is not set")
            
            # Binary search agtig system
            if leaf_index < midpoint:
                choices.append(False)
                current = current.child_a
            else:
                choices.append(True)
                current = current.child_b
                leaf_index -= midpoint
                
        path.append(current)
        
        reversed_path = reversed(path)
        
        new_owned_nodes: list[Node_Own] = []
        
        for index, node in enumerate(reversed_path):
            if index == 0:
                new_node = make_node_owned(node)
                new_owned_nodes.append(new_node)
                continue
            
            choice: bool = choices.pop()
            
            new_node = make_node_owned(node)
            
            if not choice:
                new_node.child_a = new_owned_nodes[-1]
            else:
                new_node.child_b = new_owned_nodes[-1]
                
            new_owned_nodes.append(new_node)
        
        self.root = new_owned_nodes[-1]
        
        # Vi starter fra leaf..root når keys udregnes
        return  new_owned_nodes
        
    def _init_creator_keys(self, secret):
        current_seed = secret
        
        for node in self.path_user:
            current_seed = node.derive_keys(current_seed)
    
    def _get_first_empty_leaf(self):
        if not self.leaf_nodes:
            return -1
        
        for i in range(self.leaf_nodes):
            leaf = self.get_leaf(i)
            if not leaf:
                return -1
            
            if not leaf.client_uid:
                return i # Returns empty client uid
        
        return -1
    
    def _new_key_rotation(self):
        my_node = self.path_user[0]
        
        new_seed = util.gen_new_leaf_seed()
        
        my_node.secret = new_seed
        
        current_seed = new_seed
        for node in self.path_user:
            current_seed = node.derive_keys(current_seed)
            
            
    def add_new_user(self, uid, pub_key):
        index = self._get_first_empty_leaf()
        if (0 > index):
            raise RuntimeError("Panic: Ik plads til flere brugere")
        
        self.users[uid] = index
        self.fill_leaf(index, uid, pub_key)
        
        # MAke a commit and return it to be distrbutet
        

        
        
    # 0 = root, 0 = helt til venstre
    def get_node_at(self, target_depth: int, index: int):
        current = self.root
        
        
        for d in range(target_depth):
            nodes_at_level = 2 ** (target_depth - d)
            midpoint = nodes_at_level // 2
            
            if not current:
                raise RuntimeError("Panic: Root is not set")
            
            if index < midpoint:
                current = current.child_a
            else:
                current = current.child_b
                index -= midpoint
                
        return current
    
    def get_leaf(self, index: int) -> Node_Member | Node_Own | None:
        current = self.root
        depth = self.tree_depth
        
        if not depth:
            raise RuntimeError("Panic: Tree Cooked")
            
        
        for d in range(depth):
            nodes_at_level = 2 ** (depth - d)
            midpoint = nodes_at_level // 2
            
            if not current:
                raise RuntimeError("Panic: Root is not set")
            
            if index < midpoint:
                current = current.child_a
            else:
                current = current.child_b
                index -= midpoint
                
        return current
    
    

    def fill_leaf(self, index, client_uid, pub_key=None):
        if not self.tree_depth:
            raise RuntimeError("Tree Depth: Not assigned")
        
        target_node = self.get_node_at(self.tree_depth, index)
        
        if isinstance(target_node, Node_Member): 
            target_node.client_uid = client_uid
    
    
    
    
    
    
    def apply_msg(self, msg):
        pass
    

    
    
    
    
    def generate_update_packet(self):
        update_packet = []
        
        # Iterate through the Admin's path (excluding the root itself)
        for i in range(len(self.path_user) - 1):
            current_node = self.path_user[i]
            
            # 1. Get the seed meant for the parent node
            parent_seed = util.derive_parent_seed(current_node.secret)
            
            # 2. Find the sibling of the current_node (You will need a helper 
            #    function like _get_path_and_siblings from your old code)
            sibling_node = self._get_sibling_at_level(i)
            
            # 3. Encrypt the parent_seed to the sibling's public key
            if sibling_node and sibling_node.pub_key:
                ephemeral_pub, nonce, ciphertext = util.encrypt_to_pub(
                    sibling_node.pub_key, 
                    parent_seed
                )
                
                # 4. Append to packet
                update_packet.append({
                    "level": i,
                    "ephemeral_pub": ephemeral_pub.hex(), # Hex for JSON serialization
                    "nonce": nonce.hex(),
                    "ciphertext": ciphertext.hex()
                })
                
        return update_packet



    def generate_welcome_packet(self, group_id, new_user_pub_key):
        # 1. Get the newly established root secret
        root_secret = self.root.secret
        
        # 2. Encrypt the root secret directly to the new user's public key
        ephemeral_pub, nonce, ciphertext = util.encrypt_to_pub(
            new_user_pub_key, 
            root_secret
        )
        
        # 3. Build the Welcome dictionary
        welcome_msg = {
            "header": "WELCOME",
            "group_id": group_id,
            "users": self.users, # Send the updated roster
            "encrypted_root": {
                "ephemeral_pub": ephemeral_pub.hex(),
                "nonce": nonce.hex(),
                "ciphertext": ciphertext.hex()
            }
        }
        
        return welcome_msg
    
    
    def process_update_packet(self, update_packet: list[dict]):
        decrypted_seed = None
        intersection_level = -1
        
        # 1. Iterate through the packet to find the layer meant for our branch
        for packet_layer in update_packet:
            level = packet_layer["level"]
            
            # Ensure the level exists in our local path
            if level < len(self.path_user):
                my_node = self.path_user[level]
                
                # We can only decrypt if we own the private key at this level
                if my_node.pri_key:
                    try:
                        # Convert the JSON-friendly hex strings back to raw bytes
                        ephemeral_pub_bytes = bytes.fromhex(packet_layer["ephemeral_pub"])
                        nonce = bytes.fromhex(packet_layer["nonce"])
                        ciphertext = bytes.fromhex(packet_layer["ciphertext"])
                        
                        # Attempt to decrypt the seed using util.py
                        decrypted_seed = util.decrypt_with_pri(
                            my_node.pri_key, 
                            ephemeral_pub_bytes, 
                            nonce, 
                            ciphertext
                        )
                        
                        # If decryption succeeds, the seed is meant for the parent node
                        intersection_level = level + 1 
                        break # Stop searching once we find our seed
                        
                    except Exception:
                        # Decryption failed (wrong key for this layer). 
                        # This is expected; just move to the next layer.
                        continue
                        
        # 2. Safety check: Did we successfully find a key?
        if decrypted_seed is None:
            raise RuntimeError("Failed to decrypt update packet. Key mismatch.")
            
        # 3. Update the tree from the intersection point up to the root
        current_seed = decrypted_seed
        
        for i in range(intersection_level, len(self.path_user)):
            node = self.path_user[i]
            
            # derive_keys() generates the new pri/pub keys and returns the NEXT seed
            current_seed = node.derive_keys(current_seed)
    
    
    
    
    
    
    
    # For debugging purpose
    def print_tree(self, node=None, depth=0):
        # Start from the root if no node is provided initially
        if node is None and depth == 0:
            node = self.root

        # Guard against empty trees or None nodes to satisfy the type checker
        if node is None:
            return

        # Create an indentation based on the current depth
        indent = "\t" * depth
        
        # Retrieve public key, private key, and user ID if available
        pub = node.pub_key if node.pub_key is not None else "None"
        pri = getattr(node, "pri_key", "None") if getattr(node, "pri_key", None) is not None else "None"
        uid = node.client_uid if node.is_leaf and node.client_uid else ""
        
        # Identify the type of the node (Node_Own or Node_Member)
        if isinstance(node, Node_Member):
            node_type = "Member"
        else:
            node_type = "Own"

        # Print the current node's information
        print(f"{indent}({uid}) [{node_type}]: Pub {pub} | Pri {pri}")

        # Recursively print the left and right children if they exist
        if getattr(node, "child_a", None) is not None:
            self.print_tree(node.child_a, depth + 1)
        if getattr(node, "child_b", None) is not None:
            self.print_tree(node.child_b, depth + 1)