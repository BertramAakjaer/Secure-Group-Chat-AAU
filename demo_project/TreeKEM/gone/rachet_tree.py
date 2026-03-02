import os
import util
from tree_structure import Tree


class RatchetTree:
    def __init__(self, creator_uid):
        self.inner_tree = Tree(min_users=5)
        self.users = {} # UID til leaf index fra 0..n fra venstre
        self.owner_uid = creator_uid
        
        # Ejeren af gruppen bliver på index 0
        self.add_user(creator_uid, index=0)
        
        
    # Henter hele den "sti" der er mellem en leaf node og root
    def _get_path_and_siblings(self, index):
        path = [] # liste af nodes
        siblings = [] # liste af siblings
        current = self.inner_tree.root # Starter fra toppen
        target_depth = self.inner_tree.tree_depth
        
        # Går ned af træet, men gemmer alle nodes som er "stien"
        for d in range(target_depth):
            path.append(current)
            
            nodes_at_level = 2 ** (target_depth - d) # Bruges til at beregne den vej næste skridt er
            midpoint = nodes_at_level // 2
            
            # Binary search agtig system
            if index < midpoint:
                siblings.append(current.child_b)
                current = current.child_a
            else:
                siblings.append(current.child_a)
                current = current.child_b
                index -= midpoint
                
        path.append(current)
        siblings.append(None) # Laver array til samme længde
        
        # Vi starter fra leaf..root når keys udregnes
        return (reversed(path)), list(reversed(siblings))

    def generate_update_packet(self, leaf_index):
        new_seed = os.urandom(32)
        path, siblings = self._get_path_and_siblings(leaf_index)
        
        update_packet = []
        current_seed = new_seed
        
        for i in range(len(path) - 1): # Stop before root
            node = path[i]
            sibling = siblings[i]
            
            # Derive the keys for my node
            node.derive_keys(current_seed)
            parent_seed = util.derive_parent_seed(current_seed)
            
            # Encrypt the parent_seed for the sibling's public key
            if sibling and sibling.pub_key:
                ephemeral_pub, nonce, ciphertext = util.encrypt_to_pub(sibling.pub_key, parent_seed)
                update_packet.append({
                    "level": i,
                    "ephemeral_pub": ephemeral_pub,
                    "nonce": nonce,
                    "ciphertext": ciphertext
                })
            
            current_seed = parent_seed
            
        return update_packet
    
    def process_update_packet(self, packet, my_leaf_index):
        """
        1. A receiving user finds the encryption meant for their side of the tree.
        2. Decrypts the parent seed.
        3. Updates their local tree from that point up to the root.
        """
        # Note: In a full implementation, you find the exact intersection level.
        # This is simplified logic assuming the user knows which packet level applies to them.
        
        # Example of decrypting if this packet was meant for me:
        # my_pri_key = self._get_my_private_key(my_leaf_index)
        # decrypted_seed = util.decrypt_with_pri(my_pri_key, p["ephemeral_pub"], p["nonce"], p["ciphertext"])
        
        # Once decrypted_seed is acquired, loop through the rest of the path to root:
        # parent.derive_keys(decrypted_seed)
        pass
    
    
    # Henter hele den "sti" der er mellem en leaf node og root
    def _get_path_to_root(self, index):
        path = [] # liste af nodes
        current = self.inner_tree.root # Starter fra toppen
        target_depth = self.inner_tree.tree_depth
        
        # Går ned af træet, men gemmer alle nodes som er "stien"
        for d in range(target_depth):
            path.append(current)
            
            nodes_at_level = 2 ** (target_depth - d) # Bruges til at beregne den vej næste skridt er
            midpoint = nodes_at_level // 2
            
            # Binary search agtig system
            if index < midpoint:
                current = current.child_a
            else:
                current = current.child_b
                index -= midpoint
                
        path.append(current)
        
        # Vi starter fra leaf..root når keys udregnes
        return reversed(path)
        
        
    # Opdatere alle nøgler fra en user til root
    def _update_keys_on_path(self, leaf_index, new_seed=None):
        if new_seed is None:
            new_seed = os.urandom(32)
            
        path = self._get_path_to_root(leaf_index)
        current_seed = new_seed
        
        for node in path:
            current_seed = node.derive_keys(current_seed)

    def add_user(self, uid, index=None):
        if index is None:
            index = len(self.users)
            
        self.users[uid] = index
        self.inner_tree.fill_leaf(index, uid, "empty") 
        self._update_keys_on_path(index)
        #print(f"User {uid} added at index {index}. Root key rotated.")
        

    def remove_user(self, uid):
        if uid not in self.users: return
        
        # Sletter person fra liste over index og UID,
        # men gemmer deres index til mere udregning
        idx = self.users.pop(uid)
        target = self.inner_tree.get_node_at_position(self.inner_tree.tree_depth, idx)
        
        target.blank_out() # Function der "rengør" node
        
        # Nøgler skal ændres af en person,
        # så vi bruger ejeren til at ændre nøgler,
        # så den person der forlod ikke kan læse nye beskeder
        if self.users:
            self.rotate_root(self.owner_uid)
            

    def rotate_root(self, uid):
        self._update_keys_on_path(self.users[uid])
        
        
        
if __name__ == "__main__":
    group = RatchetTree("Alice")
    group.inner_tree.print_tree()

    group.add_user("Bob")
    group.inner_tree.print_tree()
    
    group.remove_user("Bob")
    group.inner_tree.print_tree()