from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field

import rasterio
from pystac.item import Item
from rio_tiler.io.base import BaseReader, MultiBaseReader
from rio_tiler.io.rasterio import Reader
from rio_tiler.io.stac import STACReader


class AbstractCapture(ABC):
    @abstractmethod
    def open_reader(self) -> Generator[BaseReader | MultiBaseReader]:
        raise NotImplementedError

    @property
    def uris(self) -> list[str]:
        """A list of URIs that make up the capture."""
        raise NotImplementedError


@dataclass
class URICapture(AbstractCapture):
    uri: str

    @contextmanager
    def open_reader(self) -> Generator[Reader]:
        uri = self.uri
        with ExitStack() as cxt_stack:
            cxt_stack.enter_context(
                rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR')
            )

            if uri.startswith('https://sentinel-cogs.s3.us-west-2.amazonaws.com'):
                cxt_stack.enter_context(rasterio.Env(AWS_NO_SIGN_REQUEST='YES'))
                uri = 's3://sentinel-cogs/' + uri[49:]

            cog = cxt_stack.enter_context(Reader(input=uri))
            yield cog

    @property
    def uris(self):
        return [self.uri]


@dataclass
class STACCapture(AbstractCapture):
    stac_item: Item
    stac_assets: set[str]
    s3_requester_pays: bool = field(kw_only=True, default=False)

    @contextmanager
    def open_reader(self) -> Generator[STACReader]:
        with ExitStack() as cxt_stack:
            reader = cxt_stack.enter_context(
                STACReader(None, item=self.stac_item, include_assets=self.stac_assets)
            )
            if self.s3_requester_pays:
                cxt_stack.enter_context(rasterio.Env(AWS_REQUEST_PAYER='requester'))
            yield reader

    @property
    def uris(self):
        """Get URIs for each asset in included in the STACReader."""
        return [self.stac_item.assets[name].href for name in self.stac_assets]
