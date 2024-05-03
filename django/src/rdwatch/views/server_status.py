import datetime
import socket
from typing import Any

from ninja import Field, Router, Schema

from django.http import HttpRequest

from rdwatch.utils.smartflow import smartflow

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
    rdwatch_version: str
    smartflow: dict[str, Any]


@router.get('/', response=ServerStatusSchema)
def get_status(request: HttpRequest):
    from rdwatch.api import api

    uptime = datetime.datetime.now() - SERVER_INSTANCE_EPOCH
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    smartflow_status = smartflow.get_health().to_dict()

    return ServerStatusSchema(
        uptime=uptime,
        hostname=hostname,
        ip=ip,
        rdwatch_version=api.version,
        smartflow=smartflow_status,
    )
