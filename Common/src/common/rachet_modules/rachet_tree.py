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
        
        # Track newly added member for commit encryption
        self._last_added_leaf = None
        self._last_added_pub_key = None
        
        # Store my offline private key for decrypting direct path secrets
        self._my_offline_pri_key = None


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
        
        # Track the newly added member so _rotate_keys can encrypt for them
        self._last_added_leaf = new_leaf_idx
        self._last_added_pub_key = new_pub_key_bytes

        # Creates commit package 
        commit_data = self._rotate_keys()

        
        if self.tree[0].seed:
            encrypted_root = CryptoUtils.encrypt_to_pub(new_pub_key_bytes, self.tree[0].seed)
        else:
            encrypted_root = None

        # Serialize the public state of the tree for welcome packet
        tree_state = self._serialize_tree_state()

        welcome_data = welcome_packet(self.epoch, tree_state, encrypted_root)

        return commit_data, welcome_data

    
    # Remove a user from the tree and rotate keys
    def remove_member(self, uid_to_remove):
        # Find the leaf to remove
        leaf_to_remove_idx = -1
        for i in range(self.leaf_start_index, self.total_nodes):
            if self.tree[i].uid == uid_to_remove:
                leaf_to_remove_idx = i
                break
        
        if leaf_to_remove_idx == -1:
            raise ValueError(f"User {uid_to_remove} not found in group!")
        
        # Clear the leaf data
        self.tree[leaf_to_remove_idx].uid = None
        self.tree[leaf_to_remove_idx].pub_key_bytes = None
        
        # Rotate keys to update the tree
        commit_data = self._rotate_keys()
        return commit_data




    def join_group(self, welcome_data, my_offline_pri_key):
        welcome_dict = from_rachet_packet(welcome_data)
        welcome_pkg = welcome_dict["Payload"]
        
        self.epoch = welcome_pkg["epoch"]
        
        # Store offline key for future use (e.g., decrypting direct path secrets)
        self._my_offline_pri_key = my_offline_pri_key
        
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
        
        # Find my leaf
        my_leaf_idx = None
        for i in range(self.leaf_start_index, self.total_nodes):
            if self.tree[i].uid == self.my_uid:
                my_leaf_idx = i
                break
        
        new_seed = CryptoUtils.gen_seed()
        path = self._get_direct_path(my_leaf_idx)
        path_set = set(path)  # For efficient lookup
        
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
        
        self.epoch = commit_pkg["epoch"]
        
        # Update tree state if provided (for when new members are added)
        if commit_pkg.get("tree_state"):
            for node_data in commit_pkg["tree_state"]:
                idx = node_data["index"]
                self.tree[idx].uid = node_data["uid"]
                if node_data["pub_key"]:
                    self.tree[idx].pub_key_bytes = bytes.fromhex(node_data["pub_key"])
        
        # Check if there's a direct encryption for my leaf
        if commit_pkg.get("direct_path_secrets") and self._my_offline_pri_key:
            direct_secrets = commit_pkg["direct_path_secrets"]
            if not isinstance(direct_secrets, list):
                direct_secrets = [direct_secrets] if direct_secrets else []
            
            # Find my leaf
            my_leaf_idx = None
            for i in range(self.leaf_start_index, self.total_nodes):
                if self.tree[i].uid == self.my_uid:
                    my_leaf_idx = i
                    break
            
            # Look for a direct secret for my leaf
            for direct_secret in direct_secrets:
                if my_leaf_idx is not None and direct_secret["leaf_index"] == my_leaf_idx:
                    try:
                        root_seed = CryptoUtils.decrypt_with_pri(self._my_offline_pri_key, direct_secret["encrypted_root"])
                        self.tree[0].apply_seed(root_seed)
                        return  # Successfully got root from direct secret
                    except Exception:
                        pass  # Decryption failed, continue to regular process
        
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
    print("--- Ratchet Tree Simulation with 5 Users ---\n")
    
    # 1. Alice creates the group
    alice = RatchetGroup("alice_uid")
    alice.create_group()
    print(f"[Alice] Group created. Root Key: {alice.get_root_key().hex()[:16]}...")
    print(f"[Alice] Epoch: {alice.epoch}\n")

    # Store users for later reference
    users = {"alice_uid": alice}

    # 2. Add 4 more users (Bob, Charlie, Diana, Eve)
    user_names = ["bob_uid", "charlie_uid", "diana_uid", "eve_uid"]
    
    for user_name in user_names:
        # Generate offline identity
        pri_key, pub_key = CryptoUtils.generate_keypair()
        
        # Alice adds the member
        commit_pkg, welcome_pkg = alice.add_member(user_name, pub_key)
        commit_dict = from_rachet_packet(commit_pkg)
        
        print(f"[Alice] Added {user_name}. Epoch: {commit_dict['Payload']['epoch']}")
        
        # New user joins
        new_user = RatchetGroup(user_name)
        new_user.join_group(welcome_pkg, pri_key)
        users[user_name] = new_user
        
        print(f"[{user_name.split('_')[0].capitalize()}] Joined group. Root Key: {new_user.get_root_key().hex()[:16]}... Epoch: {new_user.epoch}")
        
        # All other users process the commit
        for other_name, other_user in users.items():
            if other_name != user_name and other_name != "alice_uid":
                other_user.process_commit(commit_pkg)
        
        # Verify everyone has the same key
        alice.process_commit(commit_pkg)
        root_key = alice.get_root_key()
        all_match = all(users[name].get_root_key() == root_key for name in users)
        print(f"-> All keys match: {all_match}\n")

    # 3. Key rotation: Bob rotates the keys
    print("--- Key Rotation: Bob rotates keys ---")
    bob = users["bob_uid"]
    alice = users["alice_uid"]
    commit_pkg = bob._rotate_keys()
    commit_dict = from_rachet_packet(commit_pkg)
    print(f"[Bob] Rotated keys. New Epoch: {commit_dict['Payload']['epoch']}")
    
    # All users process the commit
    for name, user in users.items():
        if name != "bob_uid":
            user.process_commit(commit_pkg)
    
    # Verify everyone has the same key after rotation
    bob_key = bob.get_root_key()
    all_match = all(users[name].get_root_key() == bob_key for name in users)
    print(f"-> Keys match after rotation: {all_match}")
    print(f"-> New shared key: {bob_key.hex()[:16]}... Epoch: {bob.epoch}\n")

    # 4. Another rotation: Charlie rotates the keys
    print("--- Key Rotation: Charlie rotates keys ---")
    alice = users["alice_uid"]
    charlie = users["charlie_uid"]
    commit_pkg = charlie._rotate_keys()
    commit_dict = from_rachet_packet(commit_pkg)
    print(f"[Charlie] Rotated keys. New Epoch: {commit_dict['Payload']['epoch']}")
    
    # All users process the commit
    for name, user in users.items():
        if name != "charlie_uid":
            user.process_commit(commit_pkg)
    
    charlie_key = charlie.get_root_key()
    all_match = all(users[name].get_root_key() == charlie_key for name in users)
    print(f"-> Keys match after rotation: {all_match}")
    print(f"-> New shared key: {charlie_key.hex()[:16]}... Epoch: {charlie.epoch}\n")

    # 5. Remove Eve from the group
    print("--- Removing Eve from the group ---")
    alice = users["alice_uid"]
    eve_key_before = users["eve_uid"].get_root_key()
    print(f"[Eve] Key before removal: {eve_key_before.hex()[:16]}... Epoch: {users['eve_uid'].epoch}")
    
    commit_pkg = alice.remove_member("eve_uid")
    commit_dict = from_rachet_packet(commit_pkg)
    print(f"[Alice] Removed Eve. New Epoch: {commit_dict['Payload']['epoch']}")
    
    # All remaining users process the commit
    for name, user in users.items():
        if name != "eve_uid":
            user.process_commit(commit_pkg)
    
    # Eve's key should now be outdated
    remaining_key = alice.get_root_key()
    all_match = all(users[name].get_root_key() == remaining_key for name in ["alice_uid", "bob_uid", "charlie_uid", "diana_uid"])
    print(f"-> Remaining users' keys match: {all_match}")
    print(f"-> New shared key (Eve excluded): {remaining_key.hex()[:16]}... Epoch: {alice.epoch}")
    print(f"[Eve] Key after removal (outdated): {users['eve_uid'].get_root_key().hex()[:16]}... Epoch: {users['eve_uid'].epoch}")
    print(f"-> Eve's key differs from group: {remaining_key != users['eve_uid'].get_root_key()}\n")

    # 6. Final verification
    print("--- Final Verification ---")
    final_key = alice.get_root_key()
    for name in ["alice_uid", "bob_uid", "charlie_uid", "diana_uid"]:
        key_match = users[name].get_root_key() == final_key
        epoch = users[name].epoch
        print(f"[{name.split('_')[0].capitalize()}] Epoch: {epoch}, Key matches: {key_match}")