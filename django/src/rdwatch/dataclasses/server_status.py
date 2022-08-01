from dataclasses import dataclass
from datetime import timedelta


@dataclass
class ServerStatus:

    uptime: timedelta
    hostname: str
    ip: str
