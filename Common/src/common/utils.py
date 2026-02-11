#
#   Enum for vores package typer
#
from enum import Enum
class PackageType(str, Enum):
    # MLS Standards
    WELCOME = "WELCOME" # Tilføjning af ny bruger
    COMMIT = "COMMIT" # Opdaterer gruppe nøgler
    PROPOSAL = "PROPOSAL" # Forandring for gruppe træet
    
    # Ikke standard, men bruges til at sende
    MSG = "MSG" # Standard encrypted chat message
    

#
#   Funktion til at generer tilfældige id til vores brugere
#
import hashlib, time, random
def gen_random_uid(lenght=10) -> str: 
    
    str = f"{time.time()}{random.random()}" # Opretter en streng af den nuværende tid i ms + en tilfældig kommatal
    hash_id = hashlib.md5(str.encode()).hexdigest()[:lenght] # Laver strengen om til en hash med en given længde
    
    return hash_id