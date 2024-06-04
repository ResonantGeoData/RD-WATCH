import logging
from typing import Literal

import rasterio  # type: ignore
from rio_tiler.io.rasterio import Reader

logger = logging.getLogger(__name__)


def get_raster_tile(uri: str, z: int, x: int, y: int) -> bytes:
    # logger.warning(f'SITE URI: {uri}')
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'):
        if uri.startswith('https://sentinel-cogs.s3.us-west-2.amazonaws.com'):
            with rasterio.Env(AWS_NO_SIGN_REQUEST='YES'):
                s3_uri = 's3://sentinel-cogs/' + uri[49:]
                with Reader(input=s3_uri) as cog:
                    img = cog.tile(x, y, z, tilesize=512)
                    img.rescale(in_range=((0, 10000),))
                    return img.render(img_format='WEBP')
        with Reader(input=uri) as cog:
            img = cog.tile(x, y, z, tilesize=512)
            img.rescale(in_range=((0, 10000),))
            return img.render(img_format='WEBP')


def get_raster_bbox(
    uri: str,
    bbox: tuple[float, float, float, float],
    format='PNG',
    scale: Literal['default', 'bits'] | list[int] = 'default',
) -> bytes:
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'):
        if uri.startswith('https://sentinel-cogs.s3.us-west-2.amazonaws.com'):
            with rasterio.Env(AWS_NO_SIGN_REQUEST='YES'):
                s3_uri = 's3://sentinel-cogs/' + uri[49:]
                with Reader(input=s3_uri) as cog:
                    img = cog.part(bbox)
                    if scale == 'default':
                        img.rescale(in_range=((0, 10000),))
                    elif scale == 'bits':
                        stats = cog.statistics()
                        low = 0
                        high = 10000
                        if 'b1' in stats.keys():
                            stats_json = stats['b1']
                            low = stats_json['percentile_2']
                            high = stats_json['percentile_98']
                        img.rescale(in_range=((low, high),))
                    elif isinstance(scale, list) and len(scale) == 2:
                        img.rescale(in_range=((scale[0], scale[1]),))
                    return img.render(img_format=format)
        with Reader(input=uri) as cog:
            img = cog.part(bbox)
            if scale == 'default':
                img.rescale(in_range=((0, 10000),))
            elif scale == 'bits':
                stats = cog.statistics()
                low = 0
                high = 10000
                if 'b1' in stats.keys():
                    stats_json = stats['b1']
                    low = stats_json['percentile_2']
                    high = stats_json['percentile_98']
                img.rescale(in_range=((low, high),))
            elif isinstance(scale, list) and len(scale) == 2:
                img.rescale(in_range=((scale[0], scale[1]),))
            return img.render(img_format=format)
