from common.rachet_modules.crypto_engine import crypt_engine

class TreeNode:
    def __init__(self, index: int):
        self.index = index
        self.uid = None # Only for accounts on leaf nodes
        self.pub_key_bytes = None # Public key known by all
        
        # Private data (bruges kun lokalt af sig selv, bliver ikke sendt)
        self.seed = None # 
        self.pri_key = None


    def apply_seed(self, seed: bytes, keep_public_key: bool = False): # Sets a new seed and derives keys
        self.seed = seed
        self.pri_key, pub_key = crypt_engine.asym.derive_keypair(seed)
        if not keep_public_key or self.pub_key_bytes is None:
            self.pub_key_bytes = crypt_engine.asym.get_public_bytes(pub_key)


    def wipe_private_data(self): # When removing an account or changing the root
        self.seed = None
        self.pri_key = None
