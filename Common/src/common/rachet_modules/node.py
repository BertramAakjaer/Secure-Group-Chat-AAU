from common.rachet_modules.crypto import CryptoUtils

class TreeNode:
    def __init__(self, index: int):
        self.index = index
        self.uid = None # Only for accounts on leaf nodes
        self.pub_key_bytes = None # Public key known by all
        
        # Private data (bruges kun lokalt af sig selv, bliver ikke sendt)
        self.seed = None # 
        self.pri_key = None


    def apply_seed(self, seed: bytes): # Sets a new seed and derives keys
        self.seed = seed
        self.pri_key, pub_key = CryptoUtils.derive_keypair(seed)
        self.pub_key_bytes = pub_key.public_bytes_raw()


    def wipe_private_data(self): # When removing an account or changing the root
        self.seed = None
        self.pri_key = None
