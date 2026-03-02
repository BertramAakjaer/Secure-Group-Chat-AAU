import math


import util
from nodes import Node_Member, Node_Own

# Returns the depth of the tree and number of leaf nodes
def _get_tree_size(n):
    minimum = 8
    maximum = 16384
    
    leaf_nodes = minimum
    
    while (leaf_nodes < n) and (leaf_nodes * 2 <= maximum):
        leaf_nodes *= 2
        
    return (int(math.log2(leaf_nodes)), leaf_nodes)


class Tree:
    def __init__(self, local_uuid: str, welcome_msg: dict, min_users: int=5):
        self.local_user: str = local_uuid
        self.path_user = []
        
        self.tree_depth: int | None
        self.leaf_nodes: int | None
        
        self.root: Node_Own | None
        
        self.users: dict[str, int] # UID til leaf index fra 0..n fra venstre
        
        # Initalisere data der bruges
        self._init_tree(min_users, welcome_msg)
        
    
    def _init_tree(self, min_users: int, welcome_msg: dict):
        self.tree_depth, self.leaf_nodes = _get_tree_size(min_users)
        
        root_temp = self._create_tree_structure(self.tree_depth)
        if isinstance(root_temp, Node_Own):
            self.root = root_temp
        else:
            raise RuntimeError("Panic: Root is not owned")
        
        self.users[self.local_user] = 0
        
        self.get_node_at(self.tree_depth, 0)
        
        self.path_user = self.get_direct_path(self.users[self.local_user])        
    
    
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
    
    def get_direct_path(self, leaf_index: int):
        path = [] # liste af nodes
        
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
            if index < midpoint:
                current = current.child_a
            else:
                current = current.child_b
                index -= midpoint
                
        path.append(current)
        
        # Vi starter fra leaf..root når keys udregnes
        return reversed(path)
    
    def apply_msg(self, msg):
        pass
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

    def fill_leaf(self, index, client_uid, pub_key):
        if not self.tree_depth:
            raise RuntimeError("Tree Depth: Not assigned")
        
        target_node = self.get_node_at(self.tree_depth, index)
        
        if isinstance(target_node, Node_Member): 
            target_node.client_uid = client_uid
            target_node.set_pub_key(pub_key)