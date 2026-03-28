import json
import time
import hashlib
from typing import Any, Dict

def wrap_message( 
    version: str,      # Versionsnummer 
    msg_type: str,     # Type af besked 
    group_id: str,     # ID på gruppen  
    sender_id: str,    # Afsenderens ID  
    payload: Any       # Selve beskeden
) -> str: #Returnerer en JSON string da den pakkede besked er i JSON-format.
    """
    WRAPPING:
    Konverterer en Python dictionary til en JSON string 
    """ 

    # Epoch = antal sekunder siden 1. januar 1970
    epoch = int(time.time()) # Laver et timestamp (Epoch). Dette kan bruges til at sortere beskeder/se hvornår de blev sendt.

    # Opretter en Python dictionary med alle krævede felter.
    message_dict: Dict[str, Any] = { 
        "Version": version,      # Version af protokollen. 
        "Type": msg_type,        # Type af besked. 
        "GroupID": group_id,     # Gruppe ID. 
        "SenderID": sender_id,   # Afsender ID. 
        "Epoch": epoch,          # Timestamp. 
        "Payload": payload,      # Selve beskeden. 
        "Signature": None        # Signatur indsættes senere.
    } 

    # Konverterer payload til JSON string for at lave en SHA-256 signatur
    payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    signature = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    message_dict["Signature"] = signature

    # WRAPPING:
    # Konverterer hele beskeden til en JSON string 
    json_message = json.dumps(message_dict, ensure_ascii=False)
    return json_message

# unwrap_message konverterer en JSON string tilbage til en Python dictionary
def unwrap_message(json_message: str) -> Dict[str, Any]:
    """
    UNWRAPPING:
    Konverterer en JSON string tilbage til en Python dictionary
    """

    # UNWRAPPING:
    # Konverterer JSON string til Python dictionary
    message_dict = json.loads(json_message)

    # Liste over felter som skal eksistere i beskeden 
    required_fields = [
        "Version",
        "Type",
        "GroupID",
        "SenderID",
        "Epoch",
        "Payload",
        "Signature"
    ]

    # Går igennem alle krævede felter
    for field in required_fields:

        # Hvis et felt mangler i beskeden → fejl
        if field not in message_dict:
            raise ValueError(f"Mangler felt i JSON: {field}")
        
    # Returnerer den unwrapped Python dictionary
    return message_dict


# Test / eksempel
# Denne kode kører kun hvis man kører filen direkte
if __name__ == "__main__":

    # Vi laver en besked (wrap)
    wrapped = wrap_message(
        version="1.0",
        msg_type="msg",
        group_id="gruppe1",
        sender_id="alice",
        payload={"text": "Hej fra JSON wrapping"}
    )

    # Udskriv JSON string
    print("WRAPPED JSON:")
    print(wrapped)
    print()

    # Vi pakker JSON ud igen (unwrap)
    unwrapped = unwrap_message(wrapped)

    # Udskriv Python dictionary
    print("UNWRAPPED PYTHON DICT:")
    print(unwrapped)
    print()

    # Brug payload
    print("MESSAGE TEXT:")
    print(unwrapped["Payload"]["text"])
