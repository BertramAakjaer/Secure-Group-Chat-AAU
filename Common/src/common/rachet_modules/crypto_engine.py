import os
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple, Literal, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

# Seed generator
class SeedGenerator(ABC):
    @abstractmethod
    def generate(self, length: int = 32) -> bytes:
        pass

# Bruges normalt til "tilfældig" værdi
class OSSeedGenerator(SeedGenerator):
    def generate(self, length: int = 32) -> bytes:
        return os.urandom(length)
    
###################################################

# Symmetric encryption
class SymmetricCipher(ABC):
    @property
    @abstractmethod
    def key_length(self) -> int:
        pass

    @abstractmethod
    def encrypt(self, key: bytes, plaintext: bytes, header: Optional[Dict[str, Any]] = None) -> dict:
        pass

    @abstractmethod
    def decrypt(self, key: bytes, packet: dict) -> Tuple[Optional[Dict[str, Any]], bytes]:
        pass

# AES del
class AESGCMCipher(SymmetricCipher):
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Tager fra din del @Harun XD
    
    def __init__(self, algo: Literal["AES-128-GCM", "AES-256-GCM"] = "AES-256-GCM", nonce_len: int = 12):
        self.algo = algo
        self.nonce_len = nonce_len
        self._key_len = 16 if algo == "AES-128-GCM" else 32

    @property
    def key_length(self) -> int:
        return self._key_len

    def _make_aad(self, header: Optional[Dict[str, Any]]) -> bytes:
        if not header:
            return b""
        return json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def encrypt(self, key: bytes, plaintext: bytes, header: Optional[Dict[str, Any]] = None) -> dict:
        if len(key) != self.key_length:
            raise ValueError(f"Key must be exactly {self.key_length} bytes for {self.algo}")
            
        nonce = os.urandom(self.nonce_len)
        aad = self._make_aad(header)
        
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, aad)

        return {
            "algo": self.algo,
            "header": header or {},
            "nonce": nonce.hex(),
            "ciphertext": ciphertext.hex()
        }

    def decrypt(self, key: bytes, packet: dict) -> Tuple[Optional[Dict[str, Any]], bytes]:
        if len(key) != self.key_length:
            raise ValueError(f"Key must be exactly {self.key_length} bytes for {self.algo}")

        nonce = bytes.fromhex(packet["nonce"])
        ciphertext = bytes.fromhex(packet["ciphertext"])
        header = packet.get("header")
        aad = self._make_aad(header)
        
        aesgcm = AESGCM(key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
        except InvalidTag:
            raise ValueError("Security error: message was changed or wrong key!")
            
        return header, plaintext

########################################################################

# Pub+Priv key 

class AsymmetricCipher(ABC):
    # Generates a random keypair (for direct encryption)
    @abstractmethod
    def generate_keypair(self) -> Tuple[Any, Any]:
        pass
        
    # Derive keypair from seed (for chat messages)
    @abstractmethod
    def derive_keypair(self, seed: bytes) -> Tuple[Any, Any]:
        pass

    # Take a key object and returns the bytes of the pub key
    @abstractmethod
    def get_public_bytes(self, public_key: Any) -> bytes:
        pass
    
    # Reverse og the message above
    @abstractmethod
    def load_public_key(self, data: bytes) -> Any:
        pass
    
    # Encrypts a secret with a "Peers" public key
    @abstractmethod
    def encapsulate_secret(self, my_private_key: Any, peer_public_key: Any, secret: bytes) -> dict:
        pass

    # Decrypts a secret encrypted for my pub key
    @abstractmethod
    def decapsulate_secret(self, my_private_key: Any, encrypted_data: dict) -> bytes:
        pass


# Elliptic Curve Version
class X25519Cipher(AsymmetricCipher):
    def generate_keypair(self):
        pri_key = x25519.X25519PrivateKey.generate()
        return pri_key, pri_key.public_key()

    def derive_keypair(self, seed: bytes):
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"node_keypair")
        key_bytes = hkdf.derive(seed)
        pri_key = x25519.X25519PrivateKey.from_private_bytes(key_bytes)
        return pri_key, pri_key.public_key()


    def get_public_bytes(self, public_key: Any) -> bytes:
        return public_key.public_bytes_raw()


    def load_public_key(self, data: bytes) -> Any:
        return x25519.X25519PublicKey.from_public_bytes(data)

    
    def encapsulate_secret(self, my_private_key: Any, peer_public_key: Any, secret: bytes) -> dict:
        # Elliptic Curve shared secret finder
        ephemeral_pri = x25519.X25519PrivateKey.generate()
        ephemeral_pub = ephemeral_pri.public_key()
        shared_secret = ephemeral_pri.exchange(peer_public_key)

        # USES AES GCM to encryot key
        derived_key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"encryption").derive(shared_secret)
        aesgcm = AESGCM(derived_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, secret, None)

        return {
            "eph_pub": ephemeral_pub.public_bytes_raw().hex(),
            "nonce": nonce.hex(),
            "ciphertext": ciphertext.hex()
        }

    def decapsulate_secret(self, my_private_key: Any, encrypted_data: dict) -> bytes:
        ephemeral_pub = x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(encrypted_data["eph_pub"]))
        shared_secret = my_private_key.exchange(ephemeral_pub)

        derived_key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"encryption").derive(shared_secret)
        aesgcm = AESGCM(derived_key)
        return aesgcm.decrypt(bytes.fromhex(encrypted_data["nonce"]), bytes.fromhex(encrypted_data["ciphertext"]), None)


# Overall object for handeling all "crypto functions"

class CryptoEngine:    
    def __init__(
        self,
        seed_generator: SeedGenerator = OSSeedGenerator(),
        symmetric_cipher: SymmetricCipher = AESGCMCipher(algo="AES-256-GCM"),
        asymmetric_cipher: AsymmetricCipher = X25519Cipher()
    ):
        self.seed_gen = seed_generator
        self.sym = symmetric_cipher
        self.asym = asymmetric_cipher

    def gen_seed(self) -> bytes:
        return self.seed_gen.generate()

    def derive_parent_seed(self, child_seed: bytes) -> bytes:
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"parent_seed")
        return hkdf.derive(child_seed)

    # Find the root shared secret
    def derive_application_key(self, secret: bytes, info: bytes = b"app_messaging_key") -> bytes:
        hkdf = HKDF(algorithm=hashes.SHA256(), length=self.sym.key_length, salt=None, info=info)
        return hkdf.derive(secret)

    # Uses the specified funtions for encryotion/decryption
    def encrypt_message(self, key: bytes, plaintext: str, header: Optional[Dict[str, Any]] = None) -> dict:
        return self.sym.encrypt(key, plaintext.encode('utf-8'), header)

    def decrypt_message(self, key: bytes, encrypted_data: dict) -> Tuple[Optional[Dict[str, Any]], str]:
        header, plaintext_bytes = self.sym.decrypt(key, encrypted_data)
        return header, plaintext_bytes.decode('utf-8')

# What to be imported into other files
crypt_engine = CryptoEngine()