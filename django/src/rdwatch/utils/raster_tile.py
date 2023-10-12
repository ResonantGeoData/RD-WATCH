import logging

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
    uri: str, bbox: tuple[float, float, float, float], format='PNG'
) -> bytes:
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'):
        if uri.startswith('https://sentinel-cogs.s3.us-west-2.amazonaws.com'):
            with rasterio.Env(AWS_NO_SIGN_REQUEST='YES'):
                s3_uri = 's3://sentinel-cogs/' + uri[49:]
                with Reader(input=s3_uri) as cog:
                    img = cog.part(bbox)
                    img.rescale(in_range=((0, 10000),))
                    return img.render(img_format=format)
        with Reader(input=uri) as cog:
            img = cog.part(bbox)
            img.rescale(in_range=((0, 10000),))
            return img.render(img_format=format)
