from dataclasses import dataclass, field

from common.config import SERVER_PORT

@dataclass
class SessionInfo:
    server_ip: str | None = None
    server_port: int = SERVER_PORT
    
    username: str | None = None
    uuid: str | None = None
    
    group_uuid: str | None = None
    group_name: str | None = None
    
    messages: list[str] = field(default_factory=list)    
    
    is_connected: bool = False
    is_waiting: bool = False