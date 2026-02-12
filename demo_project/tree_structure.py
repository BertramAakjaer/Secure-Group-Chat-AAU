import math, hashlib


class Node:
    def __init__(self):
        self.child_a = None
        self.child_b = None
        
        self.pub_key = None
        self.pri_key = None
        self.secret = None # Privat secret
        
        self.is_leaf = False
        self.client_uid = None
        

    def derive_keys(self, seed):
        self.secret = seed
        # Vi kunne bruge Elliptic Curves (bruges sha-256 som demo)
        self.pri_key = hashlib.sha256(seed + b"pri").hexdigest()[:8] 
        self.pub_key = hashlib.sha256(self.pri_key.encode()).hexdigest()[:8]
        
        # Retunerer et "seed" til næste node
        return hashlib.sha256(seed + b"parent").digest() # b"parent" som "salt"
    
    def blank_out(self):
        self.pub_key = None
        self.pri_key = None
        self.secret = None
        self.client_uid = None


# Returns the depth of the tree and number of leaf nodes
def _get_tree_size(n):
    minimum = 8
    maximum = 16384
    
    leaf_nodes = minimum
    
    while (leaf_nodes < n) and (leaf_nodes * 2 <= maximum):
        leaf_nodes *= 2
        
    return (math.log2(leaf_nodes), leaf_nodes)


class Tree:
    def __init__(self, min_users):
        self.tree_depth, self.leaf_nodes = _get_tree_size(min_users)
        self.tree_depth = int(self.tree_depth)
        
        self.root = self.create_tree_structure(self.tree_depth)
    
    def create_tree_structure(self, current_depth):
        node = Node()
        
        if current_depth == 0:
            node.is_leaf = True
            return node
        
        node.child_a = self.create_tree_structure(current_depth - 1)
        node.child_b = self.create_tree_structure(current_depth - 1)
        
        return node
    
    # 0 = root, 0 = helt til venstre
    def get_node_at_position(self, target_depth, index):
        current = self.root
        
        for d in range(target_depth):
            nodes_at_level = 2 ** (target_depth - d)
            midpoint = nodes_at_level // 2
            
            if index < midpoint:
                current = current.child_a
            else:
                current = current.child_b
                index -= midpoint
                
        return current
    

    def fill_leaf(self, index, client_uid, pub_key):
        target_node = self.get_node_at_position(self.tree_depth, index)
        
        target_node.client_uid = client_uid
        target_node.pub_key = pub_key
        
        
        
    def print_tree(self, node=None, depth=0):
        if node is None and depth == 0: # Sørger for at funktion kan kaldes uden start "node"
            node = self.root

        indent = "\t" * depth
        
        pub = node.pub_key if node.pub_key is not None else "None"
        pri = node.pri_key if node.pri_key is not None else "None"
        uid = node.client_uid if node.is_leaf and node.client_uid else ""

        print(f"{indent}({uid}): Pub {pub} | Pri {pri}")

        if node.child_a:
            self.print_tree(node.child_a, depth + 1)
        if node.child_b:
            self.print_tree(node.child_b, depth + 1)