import rasterio  # type: ignore
from rio_tiler.io.cogeo import COGReader

from rdwatch.utils.worldview_processed.satellite_captures import (
    WorldViewProcessedCapture,
)


def get_worldview_processed_visual_tile(
    capture: WorldViewProcessedCapture, z: int, x: int, y: int
) -> bytes:
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',
        GDAL_HTTP_MERGE_CONSECUTIVE_RANGES='YES',
        GDAL_CACHEMAX=200,
        CPL_VSIL_CURL_CACHE_SIZE=20000000,
        GDAL_BAND_BLOCK_CACHE='HASHSET',
        GDAL_HTTP_MULTIPLEX='YES',
        GDAL_HTTP_VERSION=2,
        VSI_CACHE='TRUE',
        VSI_CACHE_SIZE=5000000,
    ):
        with COGReader(input=capture.uri) as img:
            rgb = img.tile(x, y, z, tilesize=512)
        rgb.rescale(in_range=((0, 10000),))
        return rgb.render(img_format='WEBP')


def get_worldview_processed_visual_bbox(
    capture: WorldViewProcessedCapture,
    bbox: tuple[float, float, float, float],
    format='JPEG',
) -> bytes:
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',
        GDAL_HTTP_MERGE_CONSECUTIVE_RANGES='YES',
        GDAL_CACHEMAX=200,
        CPL_VSIL_CURL_CACHE_SIZE=20000000,
        GDAL_BAND_BLOCK_CACHE='HASHSET',
        GDAL_HTTP_MULTIPLEX='YES',
        GDAL_HTTP_VERSION=2,
        VSI_CACHE='TRUE',
        VSI_CACHE_SIZE=5000000,
    ):
        with COGReader(input=capture.uri) as img:
            rgb = img.part(bbox)
        rgb.rescale(in_range=((0, 10000),))
        return rgb.render(img_format=format)
