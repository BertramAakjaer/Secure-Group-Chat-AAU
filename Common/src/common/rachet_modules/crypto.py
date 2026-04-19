import os

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class CryptoUtils:
    @staticmethod
    def gen_seed() -> bytes:
        return os.urandom(32)

    @staticmethod
    def derive_keypair(seed: bytes) -> tuple[x25519.X25519PrivateKey, x25519.X25519PublicKey]:
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"node_keypair")
        key_bytes = hkdf.derive(seed)
        pri_key = x25519.X25519PrivateKey.from_private_bytes(key_bytes)
        return pri_key, pri_key.public_key()

    @staticmethod
    def generate_keypair():
        pri_key = x25519.X25519PrivateKey.generate()
        pub_key = pri_key.public_key()
        return pri_key, pub_key
    
    @staticmethod
    def from_bytes_get_pub_key(raw_bytes):
        pub_key = x25519.X25519PublicKey.from_public_bytes(raw_bytes)
        return pub_key

    @staticmethod
    def derive_parent_seed(child_seed: bytes) -> bytes:
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"parent_seed")
        return hkdf.derive(child_seed)

    @staticmethod
    def derive_application_key(secret: bytes, info: bytes = b"app_messaging_key", length: int = 32) -> bytes:
        hkdf = HKDF(algorithm=hashes.SHA256(), length=length, salt=None, info=info)
        return hkdf.derive(secret)

    @staticmethod
    def encrypt_to_pub(recipient_pub_key_bytes: bytes, secret: bytes) -> dict:
        recipient_pub = x25519.X25519PublicKey.from_public_bytes(recipient_pub_key_bytes)
        ephemeral_pri = x25519.X25519PrivateKey.generate()
        ephemeral_pub = ephemeral_pri.public_key()
        shared_secret = ephemeral_pri.exchange(recipient_pub)

        derived_key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"encryption").derive(shared_secret)
        aesgcm = AESGCM(derived_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, secret, None)

        return {
            "eph_pub": ephemeral_pub.public_bytes_raw().hex(),
            "nonce": nonce.hex(),
            "ciphertext": ciphertext.hex()
        }

    @staticmethod
    def decrypt_with_pri(my_pri_key: x25519.X25519PrivateKey, encrypted_data: dict) -> bytes:
        ephemeral_pub = x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(encrypted_data["eph_pub"]))
        shared_secret = my_pri_key.exchange(ephemeral_pub)

        derived_key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"encryption").derive(shared_secret)
        aesgcm = AESGCM(derived_key)
        return aesgcm.decrypt(bytes.fromhex(encrypted_data["nonce"]), bytes.fromhex(encrypted_data["ciphertext"]), None)
    
    
    
    @staticmethod
    def encrypt_message(key, plaintext):
        if len(key) != 32:
            raise ValueError("Key must be exactly 32 bytes for AES-256")
            
        aesgcm = AESGCM(key)
        nonce = os.urandom(12) # 96-bit nonce recommended for GCM
        plaintext_bytes = plaintext.encode('utf-8')
        ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None)

        return {
            "nonce": nonce.hex(),
            "ciphertext": ciphertext.hex()
        }
        
        
    @staticmethod
    def decrypt_string(key: bytes, encrypted_data: dict) -> str:
        if len(key) != 32:
            raise ValueError("Key must be exactly 32 bytes for AES-256")
            
        aesgcm = AESGCM(key)
        nonce = bytes.fromhex(encrypted_data["nonce"])
        ciphertext = bytes.fromhex(encrypted_data["ciphertext"])
        
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext_bytes.decode('utf-8')