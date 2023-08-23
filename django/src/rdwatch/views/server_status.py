import datetime
import socket

from ninja import Field, Router, Schema

from django.http import HttpRequest

router = Router()

SERVER_INSTANCE_EPOCH = datetime.datetime.now()


class UptimeSchema(Schema):
    iso8601: str
    days: int
    seconds: int
    useconds: int = Field(..., alias='microseconds')

    @staticmethod
    def resolve_iso8601(obj: datetime.timedelta):
        return str(obj)


class ServerStatusSchema(Schema):
    uptime: UptimeSchema
    hostname: str
    ip: str


@router.get('/', response=ServerStatusSchema)
def get_status(request: HttpRequest):
    uptime = datetime.datetime.now() - SERVER_INSTANCE_EPOCH
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return ServerStatusSchema(uptime=uptime, hostname=hostname, ip=ip)
