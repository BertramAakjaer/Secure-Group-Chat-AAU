import hashlib, time, random, os, json


from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM



def gen_random_uid(length=12) -> str: 
    string_val = f"{time.time()}{random.random()}" 
    return hashlib.md5(string_val.encode()).hexdigest()[:length]

def gen_random_gid(length=6) -> str: 
    string_val = f"{time.time()}{random.random()}" 
    return hashlib.md5(string_val.encode()).hexdigest()[:length]



def to_json(data: dict) -> str:
    json_output = json.dumps(data, indent=4)
    return json_output

def from_json(json_msg: str) -> dict:
    original_structure = json.loads(json_msg)
    return original_structure



def gen_new_leaf_seed():
    return os.urandom(32)


def derive_keypair_from_seed(seed: bytes):
    # HKDF safely expands the seed into 32 bytes suitable for X25519
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"node_keypair")
    key_bytes = hkdf.derive(seed)
    
    pri_key = x25519.X25519PrivateKey.from_private_bytes(key_bytes)
    pub_key = pri_key.public_key()
    return pri_key, pub_key

def derive_parent_seed(seed: bytes) -> bytes:
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"parent_seed")
    return hkdf.derive(seed)




def encrypt_to_pub(recipient_pub_key: x25519.X25519PublicKey, secret_to_encrypt: bytes):
    """Encrypts a payload so only the owner of the private key can read it."""
    # 1. Generate an ephemeral (temporary) keypair
    ephemeral_pri = x25519.X25519PrivateKey.generate()
    ephemeral_pub = ephemeral_pri.public_key()
    
    # 2. Derive a shared secret
    shared_secret = ephemeral_pri.exchange(recipient_pub_key)
    
    # 3. Create a symmetric AES-GCM key from the shared secret
    derived_key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"encryption").derive(shared_secret)
    aesgcm = AESGCM(derived_key)
    
    # 4. Encrypt the secret
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, secret_to_encrypt, None)
    
    return ephemeral_pub.public_bytes_raw(), nonce, ciphertext


def decrypt_with_pri(my_pri_key: x25519.X25519PrivateKey, ephemeral_pub_bytes: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    """Decrypts a payload received from another user."""
    ephemeral_pub = x25519.X25519PublicKey.from_public_bytes(ephemeral_pub_bytes)
    shared_secret = my_pri_key.exchange(ephemeral_pub)
    
    derived_key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"encryption").derive(shared_secret)
    aesgcm = AESGCM(derived_key)
    
    return aesgcm.decrypt(nonce, ciphertext, None)