import math

from common.rachet_modules.node import TreeNode
from common.rachet_modules.rachet_pcks import welcome_packet, commit_packet, from_rachet_packet
from common.rachet_modules.crypto import CryptoUtils

from common.config import MAX_GROUP_MEMBERS


# Returns the depth of the tree and number of leaf nodes
def _get_tree_size(n):
    minimum = 8
    maximum = 16384
    
    leaf_nodes = minimum
    
    while (leaf_nodes < n) and (leaf_nodes * 2 <= maximum):
        leaf_nodes *= 2
    
    # Returns (tree_depth, num_leaves)
    return (int(math.log2(leaf_nodes)), leaf_nodes)



class RatchetGroup:    
    def __init__(self, my_uid, max_members = MAX_GROUP_MEMBERS):
        self.my_uid = my_uid
        self.epoch = 0
        
        # Tree size calculated from max size
        self.tree_depth, self.num_leaves = _get_tree_size(max_members)
        self.total_nodes = (2 * self.num_leaves) - 1
        
        self.cached_keys = {} # stored like {epoch: root_key}
        
        # Empty tree initialization (as a flat array)
        self.tree = []
        for i in range(self.total_nodes):
            self.tree.append(TreeNode(i))
            
        self.leaf_start_index = self.num_leaves - 1
        
        # Store my offline private key for decrypting direct path secrets
        self._my_offline_pri_key = None


    # Tree navigation helper functions - - - -
    def _parent(self, i: int) -> int:
        return (i - 1) // 2 if i > 0 else -1

    def _sibling(self, i: int) -> int:
        if i == 0: return -1
        return i + 1 if i % 2 != 0 else i - 1
    

    # Get the path from a node to root (including root and node indecies)
    def _get_direct_path(self, node_index): 
        path = []
        
        current = node_index
        while current >= 0:
            path.append(current) # Saves the current node
            current = self._parent(current) # Goes to the parent
            
        return path # inkluderer leaf

    # UID to leaf, if None then returns first empty leaf
    def _find_leaf_by_uid(self, uid):
        for i in range(self.leaf_start_index, self.total_nodes):
            if self.tree[i].uid == uid:
                return i
        return -1

    # Applies a tree state, (both for commit and welcome)
    def _apply_tree_state(self, tree_state):
        for node_data in tree_state:
            index = node_data["index"]
            
            self.tree[index].uid = node_data["uid"] # Copies uid
            
            if node_data["pub_key"]: # Copies pub_key
                self.tree[index].pub_key_bytes = bytes.fromhex(node_data["pub_key"])
            else:
                self.tree[index].pub_key_bytes = None

    # Takes seed and a start node index and rachet all the way to the root
    def _apply_seed_to_path(self, start_index, initial_seed):
        current_seed = initial_seed
        path = self._get_direct_path(start_index)
        
        for index in path: # Goes index by index (starting at node and ending at root)
            self.tree[index].apply_seed(current_seed)
            if index != 0:
                current_seed = CryptoUtils.derive_parent_seed(current_seed)
                
    
    # Get the root key for encryption to actual messages
    def get_root_key(self, epoch=None) -> bytes:
        if epoch is None:
            epoch = self.epoch
            
        if epoch in self.cached_keys:
            return self.cached_keys[epoch]
        
        root_seed = self.tree[0].seed
        if not root_seed:
            raise ValueError("Root secret is not established yet!")
        
        root_key = CryptoUtils.derive_application_key(root_seed)
        self.cached_keys[epoch] = root_key
        return root_key


    # Functions for group management - - - -
    
    # Inits a group with this user as admin 
    def create_group(self):
        
        my_leaf_index = self.leaf_start_index # First index in leafs
        self.tree[my_leaf_index].uid = self.my_uid
        
        current_seed = CryptoUtils.gen_seed() # Generates 32-bytes seed
        self._apply_seed_to_path(my_leaf_index, current_seed) # Rachet new seeds up



    # The function add a new user to the tree and returns a WELCOME and COMMIT
    def add_member(self, new_uid, new_pub_key):
        new_pub_key_bytes = new_pub_key.public_bytes_raw()
        
        # Find the first free leaf
        new_leaf_idx = self._find_leaf_by_uid(None)
        if new_leaf_idx == -1:
            raise NotImplementedError("Group is full!")
        
        
        # Populates data
        self.tree[new_leaf_idx].uid = new_uid
        self.tree[new_leaf_idx].pub_key_bytes = new_pub_key_bytes
        

        # Creates commit package 
        commit_data = self._rotate_keys()

        
        encrypted_root = None
        if self.tree[0].seed:
            encrypted_root = CryptoUtils.encrypt_to_pub(new_pub_key_bytes, self.tree[0].seed)

        # Serialize the public state of the tree for welcome packet
        tree_state = self._serialize_tree_state()
        welcome_data = welcome_packet(self.epoch, tree_state, encrypted_root)

        return commit_data, welcome_data

    
    # Remove a user from the tree and rotate keys
    def remove_member(self, uid_to_remove):
        leaf_to_remove_idx = self._find_leaf_by_uid(uid_to_remove)
        
        # If not UID is found
        if leaf_to_remove_idx == -1:
            raise ValueError(f"User {uid_to_remove} not found in group!")
        
        # Clear the leaf data
        self.tree[leaf_to_remove_idx].uid = None
        self.tree[leaf_to_remove_idx].pub_key_bytes = None
        
        # Rotate keys to update the tree
        return self._rotate_keys()



    def join_group(self, welcome_data, my_offline_pri_key):
        welcome_dict = from_rachet_packet(welcome_data)
        welcome_pkg = welcome_dict["Payload"]
        
        # Store current epoch
        self.epoch = welcome_pkg["epoch"]
        
        # Store priv key
        self._my_offline_pri_key = my_offline_pri_key
        
        # Fill the tree information form list
        self._apply_tree_state(welcome_pkg["tree_state"])

        # Decrypt the root secret
        root_seed = CryptoUtils.decrypt_with_pri(my_offline_pri_key, welcome_pkg["encrypted_root"])
        
        # Applying the decryptet root seed
        self.tree[0].apply_seed(root_seed)
        
        

    # Rachet mechanics - - - -
    
    # Serialize the public state of the tree
    def _serialize_tree_state(self):
        tree_state = []
        for node in self.tree:
            tree_state.append({
                "index": node.index,
                "uid": node.uid,
                "pub_key": node.pub_key_bytes.hex() if node.pub_key_bytes else None
            })
        return tree_state
    
    # Rotate keys and creates COMMIT packet
    def _rotate_keys(self):
        
        # Recieving my leaf
        my_leaf_idx = self._find_leaf_by_uid(self.my_uid)
        
        new_seed = CryptoUtils.gen_seed()
        path = self._get_direct_path(my_leaf_idx)
        path_set = set(path)  # Faster index search
        
        commit_operations = []
        current_seed = new_seed

        # Applies new seeds up the path and prepares the commit operations for siblings
        for index in path:
            self.tree[index].apply_seed(current_seed)
            
            if index != 0: # If not root, prepare the seed for the parent
                parent_index = self._parent(index)
                sibling_index = self._sibling(index)
                next_seed = CryptoUtils.derive_parent_seed(current_seed)
                
                # Encrypt this next_seed for the sibling (so the sibling's subtree can learn the parent's seed)
                sibling_node = self.tree[sibling_index] # Gets node from index
                
                if sibling_node.pub_key_bytes: # Only encrypts if sibling exists
                    encrypted_data = CryptoUtils.encrypt_to_pub(sibling_node.pub_key_bytes, next_seed)
                    
                    commit_operations.append({
                        "target_node": parent_index, # The node this seed enables access to
                        "encrypt_for": sibling_index, # The node that is able to decrypt it
                        "encrypted_data": encrypted_data
                    })
                
                current_seed = next_seed # Starts next iteration
        
        
        self.epoch += 1 # Epoch changed
        
        # Create direct path secrets for members not on the rotation path
        direct_path_secrets = []
        root_seed = self.tree[0].seed
        
        if root_seed:
            # Find all active members and send them direct path secrets if they're not on this path
            for leaf_idx in range(self.leaf_start_index, self.total_nodes):
                leaf_uid = self.tree[leaf_idx].uid
                
                # If user is not touched by path
                if leaf_uid and leaf_idx not in path_set and self.tree[leaf_idx].pub_key_bytes:
                    encrypted_root = CryptoUtils.encrypt_to_pub(self.tree[leaf_idx].pub_key_bytes, root_seed)
                    direct_path_secrets.append({
                        "leaf_index": leaf_idx,
                        "encrypted_root": encrypted_root
                    })
        
        # Include tree state in commit so all members can synchronize
        tree_state = self._serialize_tree_state()
        commit_data = commit_packet(commit_operations, self.epoch, tree_state, direct_path_secrets if direct_path_secrets else None)
        return commit_data



    # Apply new root collected from commit
    def process_commit(self, commit_data):
        commit_dict = from_rachet_packet(commit_data)
        commit_pkg = commit_dict["Payload"]
        
        self.epoch = commit_pkg["epoch"] # Used for updating the new root key to the cache
        
        
        # Updates tree state = Sørger for at alle træer har samme struktur
        # Og at de samme leaf noder med 
        if commit_pkg.get("tree_state"):
            self._apply_tree_state(commit_pkg["tree_state"])
        
        # Sørger for at nye leafs også har en krypteret nøgle
        # Tjekker om den eksisterer
        if commit_pkg.get("direct_path_secrets") and self._my_offline_pri_key:
            
            direct_secrets = commit_pkg["direct_path_secrets"]
            
            if not isinstance(direct_secrets, list):
                direct_secrets = [direct_secrets] if direct_secrets else []
            
            # Find my leaf
            my_leaf_index = self._find_leaf_by_uid(self.my_uid)
            
            # Look for a direct secret for my leaf (if this uses has just joined)
            for direct_secret in direct_secrets:
                if my_leaf_index is not None and direct_secret["leaf_index"] == my_leaf_index:
                    
                    # Hvis vores nøgle ikke er korrekt vil koden fejle
                    try:
                        root_seed = CryptoUtils.decrypt_with_pri(self._my_offline_pri_key, direct_secret["encrypted_root"])
                        self.tree[0].apply_seed(root_seed)
                        return  # Successfully got root from direct secret
                    
                    except Exception:
                        pass  # Decryption failed, continue to regular process
        
        
        # Looking for sibling with encrypted key
        decrypted_seed = None
        correct_sibling = -1

        # Find an encrypted seed we can decrypt
        for operation in commit_pkg["operations"]:
            target_index = operation["target_node"]
            encrypt_for_index = operation["encrypt_for"]
            
            # Checks the sibling node to see if we have the correct key
            my_node = self.tree[encrypt_for_index]
            if my_node.pri_key:
                try:
                    decrypted_seed = CryptoUtils.decrypt_with_pri(my_node.pri_key, operation["encrypted_data"])
                    correct_sibling = target_index
                    break
                except Exception:
                    continue # Key doesn't match

        if decrypted_seed is None:
            return 
            
        # Apply the decrypted seed and wipe old data up the path
        self._apply_seed_to_path(correct_sibling, decrypted_seed)
        
        # Caches the current key
        self.get_root_key() 
    
    
    
    def print_tree_structure(self):
        print("Current Tree Structure:")
        for node in self.tree:
            print(f"Index: {node.index}, UID: {node.uid}, PubKey: {node.pub_key_bytes.hex()[:16] if node.pub_key_bytes else None}")