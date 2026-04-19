import os
import json
from cryptography.hazmat.primitives.asymmetric import rsa, padding, x25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

class Securehandshake:

    """
    Our goal is to create secure handshake with the help of the RSA+ECDH combination, and to create key for our message encryption.
    """

    def __init__(self):
        # producing rsa keys
        #rsa keys are our id, private one stays public one should be shared.
        self.our_private_rsa = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        self.our_shared_rsa = self.our_private_rsa()

        #temporary key for ECDH.
        self.temporary_dh_key = x25519.X25519PrivateKey.generate()


    def share_key(self):
        """
        This function turns our public key from key pairs into 
        bytes. we should share it to encrypt our key shared secret.
        """
        return self.our_shared_rsa.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )    
    

    """
    now we're going to encode our secret with the other users rsa key.

    """

    def make_envelope_to_user(self, other_users_rsa_key):
#formatting arrival key

        arrival_key = serialization.load_pem_public_key(other_users_rsa_key)

        #formatting our dh key as byte.

        our_dh = self.temporary_dh_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        #Envelope: lets encode our key with others rsa key.
        #noboyd can open this envolope.
        ready_envelope = arrival_key.encrypt(
            our_dh,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256,
                label=None                
            )
            )
        return ready_envelope
    def last_key_create(self, come_envelope):
        """
        we finis handshake and find aes key
        """
        # decrypt envelope with our rsa key
        dh_key_from_another_user = self.our_private_rsa.decrypt(
            come_envelope,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # 2.handshake math (DH)
        #Upload arrival data and match my dh key.
        another_user_dh_public = x25519.X25519PublicKey.from_public_bytes(dh_key_from_another_user)

        shared_secret = self.temporary_dh_key.exchange(another_user_dh_public)

        #3.hashing
        # we turn shared secret into 32 bayt aes key
        #this step blocks unbalancing by turning keys into 32 bayts hashed version.

        final_aes_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"chatting-key",
        ).derive(shared_secret)

        return final_aes_key #ready to be key of our chat encryption.