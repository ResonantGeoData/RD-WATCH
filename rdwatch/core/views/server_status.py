import datetime
import socket
from typing import Any

import semver
from ninja import Field, Router, Schema

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
    parsed_version = semver.Version.parse(api.version)

    # use pattern "v{base}{distance:+.dev+} ({commit:.7})"
    formatted_version = (
        f'v{parsed_version.major}.{parsed_version.minor}.{parsed_version.patch}'
    )
    if parsed_version.prerelease:
        formatted_version += f'+{parsed_version.prerelease}'
    formatted_version += f' ({parsed_version.build})'

    try:
        smartflow_status = SmartFlowClient().get_health().to_dict()
    except Exception:
        smartflow_status = None

    return ServerStatusSchema(
        uptime=uptime,
        hostname=hostname,
        ip=ip,
        rdwatch_version=formatted_version,
        smartflow=smartflow_status,
    )
