import datetime
import socket
from typing import Any

from ninja import Field, Router, Schema
from parver import Version

from django.http import HttpRequest

from rdwatch.smartflow.utils import SmartFlowClient

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
    smartflow: dict[str, Any] | None


@router.get('/', response=ServerStatusSchema)
def get_status(request: HttpRequest):
    from rdwatch.core.api import api

    uptime = datetime.datetime.now() - SERVER_INSTANCE_EPOCH
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)

    parsed_version = Version.parse(api.version)

    version = 'v'
    version += '.'.join(str(v) for v in parsed_version.release)

    # If this is a pre-release version, include the pre-release version string
    post_num: int | None = parsed_version.post
    if post_num is not None:
        version += f'.post{post_num}+{parsed_version.local}'

    try:
        smartflow_status = SmartFlowClient().get_health().to_dict()
    except Exception:
        smartflow_status = None

    return ServerStatusSchema(
        uptime=uptime,
        hostname=hostname,
        ip=ip,
        rdwatch_version=version,
        smartflow=smartflow_status,
    )
