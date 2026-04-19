from dataclasses import dataclass, field

from common.config import SERVER_PORT
from common.rachet_modules.rachet_tree import RatchetGroup

@dataclass
class SessionInfo:
    server_ip: str | None = None
    server_port: int = SERVER_PORT
    
    username: str | None = None
    uuid: str | None = None
    
    group_uuid: str | None = None
    group_name: str | None = None
    
    messages: list[str] = field(default_factory=list)    
    
    waiting_requests: dict[str, str] = field(default_factory=dict) # user_uuid -> pub_key_b64
    
    is_connected: bool = False
    is_waiting: bool = False
    
    rachet_group: RatchetGroup | None = None