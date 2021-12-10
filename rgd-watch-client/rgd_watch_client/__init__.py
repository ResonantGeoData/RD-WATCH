from pkg_resources import DistributionNotFound, get_distribution
from rgd_client.client import RgdClient

from .plugin import WATCHPlugin  # noqa

try:
    __version__ = get_distribution('rgd_watch_client').version
except DistributionNotFound:
    # package is not installed
    __version__ = None


class WATCHClient(RgdClient):
    watch = WATCHPlugin


__all__ = ['WATCHClient', 'WATCHPlugin']
