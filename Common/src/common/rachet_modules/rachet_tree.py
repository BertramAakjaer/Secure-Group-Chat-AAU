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


    # Tree navigation helper functions - - - -
    def _parent(self, i: int) -> int:
        return (i - 1) // 2 if i > 0 else -1

    def _sibling(self, i: int) -> int:
        if i == 0: return -1
        return i + 1 if i % 2 != 0 else i - 1
    

    # Get the path of node indices form a node to the root (we use it for getting the leaf to root path)
    def _get_direct_path(self, node_index): 
        path = []
        
        current = node_index
        while current >= 0:
            path.append(current) # Saves the current node
            current = self._parent(current) # Goes to the parent
            
        return path # inkluderer leaf
    
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
        
        # Sets data for the local leaf
        my_leaf_index = self.leaf_start_index
        leaf_node = self.tree[my_leaf_index]
        leaf_node.uid = self.my_uid
        
        # Generate initial seed and hash(rachet) up to root
        current_seed = CryptoUtils.gen_seed()
        path = self._get_direct_path(my_leaf_index)
        
        for idx in path:
            self.tree[idx].apply_seed(current_seed) # Saves seed for node and derives pub/pri keys
            
            # Rachet the seed for next level
            if idx != 0:
                current_seed = CryptoUtils.derive_parent_seed(current_seed)



    # The function add a new user to the tree and returns a WELCOME and COMMIT
    def add_member(self, new_uid, new_pub_key):
        new_pub_key_bytes = new_pub_key.public_bytes_raw()
        
        # FInd the first free leaf
        new_leaf_idx = -1
        for i in range(self.leaf_start_index, self.total_nodes):
            if self.tree[i].uid is None:
                new_leaf_idx = i
                break
        
        # If no free leaf
        if new_leaf_idx == -1:
            raise NotImplementedError("Group is full!")
        
        # Populates data
        self.tree[new_leaf_idx].uid = new_uid
        self.tree[new_leaf_idx].pub_key_bytes = new_pub_key_bytes


        # Creates commit package 
        commit_data = self._rotate_keys()

        
        if self.tree[0].seed:
            encrypted_root = CryptoUtils.encrypt_to_pub(new_pub_key_bytes, self.tree[0].seed)
        else:
            encrypted_root = None

        # Serialize the public state of the tree
        tree_state = []
        
        
        # Make a copy of public data
        for node in self.tree:
            tree_state.append({
                "index": node.index,
                "uid": node.uid,
                "pub_key": node.pub_key_bytes.hex() if node.pub_key_bytes else None
            })

        welcome_data = welcome_packet(self.epoch, tree_state, encrypted_root)

        return commit_data, welcome_data




    def join_group(self, welcome_data, my_offline_pri_key):
        welcome_dict = from_rachet_packet(welcome_data)
        welcome_pkg = welcome_dict["Payload"]
        
        self.epoch = welcome_pkg["epoch"]
        
        # Fill the tree information form list
        for node_data in welcome_pkg["tree_state"]:
            idx = node_data["index"]
            self.tree[idx].uid = node_data["uid"]
            if node_data["pub_key"]:
                self.tree[idx].pub_key_bytes = bytes.fromhex(node_data["pub_key"])

        # Decrypt the root secret
        root_seed = CryptoUtils.decrypt_with_pri(my_offline_pri_key, welcome_pkg["encrypted_root"])
        
        # Applying the decryptet root seed
        self.tree[0].apply_seed(root_seed)
        
        

    # Rachet mechanics - - - -
    
    # Rotate keys and creates COMMIT packet
    def _rotate_keys(self):
        
        # Find my leaf
        my_leaf_idx = None
        for i in range(self.leaf_start_index, self.total_nodes):
            if self.tree[i].uid == self.my_uid:
                my_leaf_idx = i
                break
        
        new_seed = CryptoUtils.gen_seed()
        path = self._get_direct_path(my_leaf_idx)
        
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
        
        
        commit_data = commit_packet(commit_operations, self.epoch)
        return commit_data



    # Apply new root collected from commit
    def process_commit(self, commit_data):
        commit_dict = from_rachet_packet(commit_data)
        commit_pkg = commit_dict["Payload"]
        
        self.epoch = commit_pkg["epoch"]
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
            
        # Apllies the decrypted seed to the sibling node
        current_seed = decrypted_seed
        path_to_root = self._get_direct_path(correct_sibling)
        
        # Wipes old data by applying new seeds
        for idx in path_to_root:
            self.tree[idx].apply_seed(current_seed)
            if idx != 0:
                current_seed = CryptoUtils.derive_parent_seed(current_seed)
    
    
    
    def print_tree_structure(self):
        print("Current Tree Structure:")
        for node in self.tree:
            print(f"Index: {node.index}, UID: {node.uid}, PubKey: {node.pub_key_bytes.hex()[:16] if node.pub_key_bytes else None}")





# ==========================================
# EXAMPLE USAGE
# ==========================================
def main():
    print("--- Ratchet Tree Simulation ---")
    
    # 1. Alice creates the group
    alice = RatchetGroup("alice_uid")
    alice.create_group()
    print(f"[Alice] Group created. Root Key: {alice.get_root_key().hex()[:16]}...")

    # 2. Bob generates his offline identity (usually done locally by Bob)
    bob_pri, bob_pub = CryptoUtils.generate_keypair()

    # 3. Alice adds Bob
    commit_pkg, welcome_pkg = alice.add_member("bob_uid", bob_pub)
    commit_dict = from_rachet_packet(commit_pkg)
    
    print(f"\n[Alice] Added Bob. Generated COMMIT (Epoch {commit_dict['Payload']['epoch']}) and WELCOME.")
    print(f"[Alice] New Root Key: {alice.get_root_key().hex()[:16]}...")

    # 4. Bob joins using the Welcome package
    bob = RatchetGroup("bob_uid")
    bob.join_group(welcome_pkg, bob_pri)
    print(f"[Bob] Joined group. Root Key: {bob.get_root_key().hex()[:16]}...")
    #bob.print_tree_structure()
    
    assert alice.get_root_key() == bob.get_root_key(), "Keys do not match!"
    print("-> Keys match successfully!")