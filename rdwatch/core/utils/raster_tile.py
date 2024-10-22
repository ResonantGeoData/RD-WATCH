import logging
from collections.abc import Sequence
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


def get_rescale_range_from_reader(
    reader: Reader | STACReader,
) -> Sequence[tuple[float, float]]:
    """Get the rescale range from the reader statistics.

    Returns a sequence of ranges, with each range corresponding to a band.
    """
    if isinstance(reader, STACReader):
        all_stats = reader.merged_statistics(assets=reader.include_assets)
        bands: list[str] = []
        for asset_name in reader.include_assets:
            for band_idx in range(
                1, get_asset_num_bands(reader.item.assets[asset_name]) + 1
            ):
                bands.append(f'{asset_name}_b{band_idx}')
    else:
        all_stats = reader.statistics()
        bands = [f'b{band_idx}' for band_idx in range(1, reader.dataset.count + 1)]

    if len(all_stats) == 0:
        return (DEFAULT_RESCALE_RANGE,)

    ranges: Sequence[tuple[float, float]] = []
    for band in bands:
        band_stats = all_stats[band]
        ranges.append((band_stats['percentile_2'], band_stats['percentile_98']))
    return ranges


def get_raster_tile_from_reader(
    reader: Reader | STACReader,
    z: int,
    x: int,
    y: int,
    scale: Literal['default', 'bits'] | list[int] = 'default',
) -> bytes:
    img = reader.tile(x, y, z, tilesize=512)
    if scale == 'default':
        img.rescale(in_range=(DEFAULT_RESCALE_RANGE,))
    elif scale == 'bits':
        band_ranges = get_rescale_range_from_reader(reader)
        img.rescale(in_range=band_ranges)
    return img.render(img_format='WEBP')


def get_raster_tile(uri: str, z: int, x: int, y: int) -> bytes:
    # logger.info(f'SITE URI: {uri}')
    with ExitStack() as cxt_stack:
        cxt_stack.enter_context(rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'))

        scale_by = 'default'
        if uri.startswith('https://sentinel-cogs.s3.us-west-2.amazonaws.com'):
            cxt_stack.enter_context(rasterio.Env(AWS_NO_SIGN_REQUEST='YES'))
            uri = 's3://sentinel-cogs/' + uri[49:]
            # rescale S2 data with bits
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
        img.rescale(in_range=(DEFAULT_RESCALE_RANGE,))
    elif scale == 'bits':
        band_ranges = get_rescale_range_from_reader(reader)
        img.rescale(in_range=band_ranges)
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
