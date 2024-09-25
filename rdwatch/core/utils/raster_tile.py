import logging
from contextlib import ExitStack
from typing import Literal

import rasterio  # type: ignore
from pystac import Asset
from rio_tiler.io.rasterio import Reader
from rio_tiler.io.stac import STACReader

logger = logging.getLogger(__name__)

DEFAULT_RESCALE_RANGE = (1, 10000)


def get_asset_num_bands(asset: Asset) -> int:
    return len(asset.extra_fields.get('eo:bands', []))


def get_read_kwargs_for_reader(reader: Reader | STACReader):
    """Generates the corresponding part()/tile() kwargs depending on the given reader.

    For STACReader:
    - will read out all assets specified in STACReader.include_assets

    For all types of readers:
    - will read all bands for all assets
    """
    if isinstance(reader, STACReader):
        assets = reader.include_assets
        asset_indexes = {
            asset_name: list(
                range(1, get_asset_num_bands(reader.item.assets[asset_name]) + 1)
            )
            for asset_name in assets
        }
        return {
            'assets': assets,
            'asset_indexes': asset_indexes,
        }
    return {'indexes': list(range(1, reader.dataset.count + 1))}


def get_rescale_range_from_reader(reader: Reader | STACReader) -> tuple[float, float]:
    """Get the rescale range from the reader statistics."""
    if isinstance(reader, STACReader):
        all_stats = reader.merged_statistics()
    else:
        all_stats = reader.statistics()

    if len(all_stats) == 0:
        return DEFAULT_RESCALE_RANGE
    # TODO This only gets the "first" band of the "first" asset. Acceptable?
    band_stats = next(iter(all_stats.values()))
    return band_stats['percentile_2'], band_stats['percentile_98']


def get_raster_tile_from_reader(
    reader: Reader | STACReader,
    z: int,
    x: int,
    y: int,
    scale: Literal['default', 'bits'] | list[int] = 'default',
) -> bytes:
    img = reader.tile(x, y, z, tilesize=512)
    if scale == 'default':
        img.rescale(in_range=((0, 10000),))
    elif scale == 'bits':
        low, high = get_rescale_range_from_reader(reader)
        img.rescale(in_range=((low, high),))
    return img.render(img_format='WEBP')


def get_raster_tile(uri: str, z: int, x: int, y: int) -> bytes:
    # logger.warning(f'SITE URI: {uri}')
    with ExitStack() as cxt_stack:
        cxt_stack.enter_context(rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'))

        scale_by = 'default'
        if uri.startswith('https://sentinel-cogs.s3.us-west-2.amazonaws.com'):
            cxt_stack.enter_context(rasterio.Env(AWS_NO_SIGN_REQUEST='YES'))
            uri = 's3://sentinel-cogs/' + uri[49:]
            # rescale S2 data wit hbits
            scale_by = 'bits'

        cog = cxt_stack.enter_context(Reader(input=uri))
        return get_raster_tile_from_reader(cog, z, x, y, scale=scale_by)


def get_raster_bbox_from_reader(
    reader: Reader | STACReader,
    bbox: tuple[float, float, float, float],
    format_='PNG',
    scale: Literal['default', 'bits'] | list[int] = 'bits',
) -> bytes:
    img = reader.part(bbox, **get_read_kwargs_for_reader(reader))
    if scale == 'default':
        img.rescale(in_range=((0, 10000),))
    elif scale == 'bits':
        low, high = get_rescale_range_from_reader(reader)
        img.rescale(in_range=((low, high),))
    elif isinstance(scale, list) and len(scale) == 2:
        img.rescale(in_range=((scale[0], scale[1]),))
    return img.render(img_format=format_)


def get_raster_bbox(
    uri: str,
    bbox: tuple[float, float, float, float],
    format_='PNG',
    scale: Literal['default', 'bits'] | list[int] = 'bits',
) -> bytes:
    with ExitStack() as cxt_stack:
        cxt_stack.enter_context(rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'))

        if uri.startswith('https://sentinel-cogs.s3.us-west-2.amazonaws.com'):
            cxt_stack.enter_context(rasterio.Env(AWS_NO_SIGN_REQUEST='YES'))
            uri = 's3://sentinel-cogs/' + uri[49:]

        cog = cxt_stack.enter_context(Reader(input=uri))
        return get_raster_bbox_from_reader(cog, bbox, format_=format_, scale=scale)
