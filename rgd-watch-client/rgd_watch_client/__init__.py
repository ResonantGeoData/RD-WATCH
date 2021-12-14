from typing import List, Optional, Type

from pkg_resources import DistributionNotFound, get_distribution
from rgd_client.client import RgdClient, create_rgd_client

from .plugin import WATCHPlugin  # noqa

try:
    __version__ = get_distribution('rgd_watch_client').version
except DistributionNotFound:
    # package is not installed
    __version__ = None


PROD_WATCH_API = 'https://watch.resonantgeodata.com/api/'


class WATCHClient(RgdClient):
    watch = WATCHPlugin


def create_watch_client(
    api_url: str = PROD_WATCH_API,
    username: Optional[str] = None,
    password: Optional[str] = None,
    save: Optional[bool] = True,
    extra_plugins: Optional[List[Type]] = None,
):
    return create_rgd_client(api_url, username, password, save, extra_plugins)


__all__ = ['WATCHClient', 'WATCHPlugin', 'create_watch_client']
