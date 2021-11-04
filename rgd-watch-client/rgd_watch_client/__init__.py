from rgd_client.client import RgdClient

from .plugin import WATCHPlugin  # noqa

__version__ = '0.0.0'  # noqa


class WATCHClient(RgdClient):
    watch = WATCHPlugin


__all__ = ['WATCHClient', 'WATCHPlugin']
