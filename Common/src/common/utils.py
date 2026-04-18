from enum import Enum

from common.config import GUID_LEN, UUID_LEN

class PackageType(str, Enum):
    # Kun fra admin/Server
    COMMIT = "COMMIT" # Vedtaget Ændring
    WELCOME = "WELCOME" # Tilføjning af ny bruger
    NEW_UUID = "NEW_UUID" # Server sender ny UUID
    
    # Kan sendes af alle (skal accepteres af admin/Server)
    PROPOSAL = "PROPOSAL" # Tilføje/Fjerne Bruger
    
    # Kan sendes af alle
    MSG = "MSG" # Alm besked
    


# Funktioner til at generer tilfældige id til vores brugere
import hashlib, time, random

def random_user_uid(lenght=UUID_LEN) -> str: 
    str = f"{time.time()}{random.random()}"
    hash = hashlib.md5(str.encode()).hexdigest()[:lenght]
    return hash


def random_group_uid(lenght=GUID_LEN) -> str: 
    str = f"{time.time()}{random.random()}"
    hash = hashlib.md5(str.encode()).hexdigest()[:lenght]
    return hash