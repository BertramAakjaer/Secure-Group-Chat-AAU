from dataclasses import dataclass, field


@dataclass
class SessionInfo:
    server_ip: str | None = None
    server_port: int = 5555
    
    username: str | None = None
    user_uuid: str | None = None
    
    group_uuid: str | None = None
    group_name: str | None = None
    
    messages: list[str] = field(default_factory=list)    
    
    is_connected: bool = False