import os # to genarate cryptographically secure random secret keys and random numbers.
import json # to serialize data structures into a text format so we can send it.
import base64 # to encode binary data into ASCII strings (readable text).
from dataclasses import dataclass #to create clean , immutable configuration objects.
from typing import Any, Dict, Tuple, Literal #for static type hinting and better code clairity.

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
#we allow these 2 types of AES.
Algo = Literal["AES-128-GCM", "AES-256-GCM"]

#Encodes data to B64 and makes it safe to send.
def to_b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")

#decodes b64 back to original form.
def frm_b64(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))

#orginez message header to keep it always in the same order
def make_aad(header: Dict[str, Any]) -> bytes:
    #sort keys so sender and reciever always see the same text.
    return json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")

@dataclass(frozen=True)
class CipherCNFG:
    #setting for encryption
    algo: Algo = "AES-256-GCM" #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! change algorithm here.
    nonce_len: int = 12 #standart length for random number in gcm

class MesgCphr: #main part of code everything goes in here.

        def __init__(self, config: CipherCNFG):
            self.config = config

        def key_len(self) -> int:
            #choosing key lenth which matches algortighm (128=16, 256=32)
            return 16 if self.config.algo == "AES-128-GCM" else 32

        def new_key(self) -> bytes: #creates a new random key.
            return os.urandom(self.key_len())
        
        def encrypt(self, key: bytes, header: Dict[str, Any], plaintext: bytes) -> Dict[str, Any]:
            #check key size is correct for the chosen algorithm
            if len(key) != self.key_len():
                raise ValueError(f"Wrong key length for {self.config.algo}: expected {self.key_len()} bytes")
            

            #unique random number for every message.
            nonce =  os.urandom(self.config.nonce_len)
            
            #prepare header(sender, name...) to be part of the seal
            aad = make_aad(header)

            aesgcm = AESGCM(key)
            #encrypts message. adds also a digital seal to prevent tampering.
            ciphertext = aesgcm.encrypt(nonce, plaintext, aad)

            #build final packet to send over chat.
            return { "kind": "app", "type": "msg_txt", "algo": self.config.algo, 
                    "header": header, "iv": to_b64(nonce), "cphr_txt": to_b64(ciphertext),}
        
        def decrypt_message(self, key: bytes, packet: Dict[str, Any]) -> Tuple[Dict[str, Any], bytes]:
            #make sure this is a message we know how to handle
            if packet.get("type") != "msg_txt":
                raise ValueError("Unsupported packet type")
                
            
           #turn the B64 text back into bytes, can work on them.
            header = packet["header"]
            nonce = frm_b64(packet["iv"])
            ciphertext = frm_b64(packet["cphr_txt"])

            aesgcm = AESGCM(key)
            aad = make_aad(header)

            try:#try to unlock the message. if key is wrong or , message change it will fail.
                plaintext = aesgcm.decrypt(nonce, ciphertext, aad) 
                
            except InvalidTag as e:
                #this happens the digital is broken or the key is wrong.
                raise InvalidTag("!!!!Security error: message was changed or Wrong key!!!!")
            
            return header, plaintext #Success return the header and the original message.
        
        # --- test block ---
if __name__ == "__main__":
    #setting up
    config = CipherCNFG()
    cipher = MesgCphr(config)
    key = cipher.new_key() # random key
    
    print("--- testing ---")
    user_input = input("Write something to encrypt: ")
    
    # encryption
    header = {}
    packet = cipher.encrypt(key, header, user_input.encode("utf-8"))
    
    print("\n packet which sended (JSON):")
    print(json.dumps(packet, indent=4))
    
    # decrption.
    print("\n decrypt...")
    decoded_header, decoded_text = cipher.decrypt_message(key, packet)
    
    print(f" decrypted message: {decoded_text.decode('utf-8')}")
    print(f" Message header: {decoded_header}")
