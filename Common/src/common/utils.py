from enum import Enum

from common.config import GUID_LEN, UUID_LEN

class PackageType(str, Enum):
    # Sendt til users
    CREATE_GROUP = "CREATE_GROUP" # Create new group
    
    JOIN_GROUP = "JOIN_GROUP" # Request to join group
    ACCEPT_JOIN = "ACCEPT_JOIN"
    DENY_JOIN = "DENY_JOIN" 
    
    NEW_UUID = "NEW_UUID" # Server sender ny UUID
    USER_INFO = "USER_INFO" # Client sends username
    
    # Sendes til admin
    JOIN_REQUESTED = "JOIN_REQUESTED"
    GROUP_CREATED = "GROUP_CREATED" # Group created successfully
    
    # Sendt til users
    JOIN_DENIED = "JOIN_DENIED"
    JOIN_ACCEPTED = "JOIN_ACCEPTED"
    MSG = "MSG" # Alm besked
    
    # Ikke implementeret endnu
    PROPOSAL = "PROPOSAL" # Tilføje/Fjerne Bruger
    COMMIT = "COMMIT" # Vedtaget Ændring
    WELCOME = "WELCOME" # Tilføjning af ny bruger
    

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