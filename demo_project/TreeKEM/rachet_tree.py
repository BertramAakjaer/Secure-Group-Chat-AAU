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
    def __init__(self, local_uid: str, welcome_msg: dict, min_users: int=5):
        self.local_user: str = local_uid
        self.path_user = []
        
        self.tree_depth: int | None
        self.leaf_nodes: int | None
        
        self.root: Node_Own | None
        
        self.users: dict[str, int] = {} # UID til leaf index fra 0..n fra venstre
        
        # Initalisere data der bruges
        self._init_tree(min_users, welcome_msg)
        
    
    def _init_tree(self, min_users: int, welcome_msg: dict):
        self.tree_depth, self.leaf_nodes = _get_tree_size(min_users)
        
        root_temp = self._create_tree_structure(self.tree_depth)
        if isinstance(root_temp, Node_Own):
            self.root = root_temp
        else:
            raise RuntimeError("Panic: Root node error")
        
        users_data = welcome_msg["users"] # Getting all users and their indecies

        user_found_check: bool = False
        for user_id, index in users_data.items():
            self.fill_leaf_uid(index, user_id)
            self.users[user_id] = index
            
            if self.local_user == user_id:
                user_found_check = True
        
        if not user_found_check:
            raise RuntimeError("Panic: User not in welcome package")
                
        self.path_user = self.set_direct_path_owned(self.users[self.local_user])
        
    
    
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
    
    
    def set_direct_path_owned(self, leaf_index: int):
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
    
    
    
    
    def apply_msg(self, msg):
        pass
    
    
    
    
    
    
    
    
    
    

    def fill_leaf_uid(self, index, client_uid):
        if not self.tree_depth:
            raise RuntimeError("Tree Depth: Not assigned")
        
        target_node = self.get_node_at(self.tree_depth, index)
        
        if isinstance(target_node, Node_Member): 
            target_node.client_uid = client_uid

    
    
    
    
    
    
    
    
    
    
    
    
    
    
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