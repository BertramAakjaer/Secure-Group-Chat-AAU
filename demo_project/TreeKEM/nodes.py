import util

    

class Node_Own:
    def __init__(self):
        self.child_a: Node_Member | Node_Own | None = None
        self.child_b: Node_Member | Node_Own | None = None

        self.is_leaf: bool = False
        self.client_uid: str | None = None
        
        self.pub_key = None
        self.pri_key = None
        self.secret = None # Privat secret
        
        

    def derive_keys(self, seed):
        self.secret = seed
        # Opretter key-pair
        self.pri_key, self.pub_key = util.derive_keypair_from_seed(seed)
        # Returns seed for the next node
        return util.derive_parent_seed(seed)
    
    def blank_out(self):
        self.pub_key = None
        self.pri_key = None
        self.secret = None
        self.client_uid = None


class Node_Member:
    def __init__(self):
        self.child_a: Node_Member | Node_Own | None = None
        self.child_b: Node_Member | Node_Own | None = None
        
        self.is_leaf: bool = False
        self.client_uid: str | None = None
        
        self.pub_key = None
        

    def set_pub_key(self, pub_key):
        self.pub_key = pub_key
    
    def blank_out(self):
        self.pub_key = None
        self.client_uid = None
        
        
        
def make_node_owned(node_src: Node_Own | Node_Member) -> Node_Own:
    new_node = Node_Own()
    
    new_node.child_a = node_src.child_a
    new_node.child_b = node_src.child_b
    
    new_node.client_uid = node_src.client_uid
    new_node.is_leaf = node_src.is_leaf
    
    new_node.pub_key = node_src.pub_key
    
    if isinstance(node_src, Node_Own):
        new_node.pri_key = node_src.pri_key
        new_node.secret = node_src.secret
    
    return new_node    