import rasterio  # type: ignore
from rio_tiler.io.cogeo import COGReader
from rio_tiler.utils import pansharpening_brovey
from rasterio.enums import Resampling
import logging
from rdwatch.utils.worldview_processed.satellite_captures import (
    WorldViewProcessedCapture,
)

logger = logging.getLogger(__name__)


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
        if not capture.panuri:
            with COGReader(input=capture.uri) as img:
                logger.warning(f"Image URI: {capture.uri}")
                info = img.info()
                logger.warning(info)
                rgb = img.tile(x, y, z, tilesize=512)
        if capture.panuri:
            logger.warning(f"PAN URI: {capture.panuri}")
            with COGReader(input=capture.panuri) as img:
                logger.warning(f"Extracting PAN PART: {capture.panuri}")
                pan = img.tile(x, y, z, tilesize=512,)
                with COGReader(input=capture.uri) as rgbimg:
                    rgb = rgbimg.tile(x, y, z, tilesize=512)
                logger.warning(f"PanSharpening: {capture.panuri}")
                rgb.data = pansharpening_brovey(rgb.data, pan.data, 0.2, 'uint16')
        if capture.bits_per_pixel != 8:
            max_bits = 2**capture.bits_per_pixel - 1
            rgb.rescale(in_range=((0, max_bits),))
        return rgb.render(img_format='WEBP')

        with COGReader(input=capture.uri) as img:
            rgb = img.tile(x, y, z, tilesize=512)
        rgb.rescale(in_range=((0, 10000),))
        return rgb.render(img_format='WEBP')


def get_worldview_processed_visual_bbox(
    capture: WorldViewProcessedCapture,
    bbox: tuple[float, float, float, float],
    format='PNG',
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
        if not capture.panuri:
            with COGReader(input=capture.uri) as img:
                logger.warning(f"Image URI: {capture.uri}")
                info = img.info()
                logger.warning(info)
                rgb = img.part(bbox)
        if capture.panuri:
            logger.warning(f"PAN URI: {capture.panuri}")
            with COGReader(input=capture.panuri) as img:
                logger.warning(f"Extracting PAN PART: {capture.panuri}")
                pan = img.part(bbox)
                with COGReader(input=capture.uri) as rgbimg:
                    rgb = rgbimg.part(bbox, width=pan.width, height=pan.height)
                logger.warning(f"PanSharpening: {capture.panuri}")
                rgb.data = pansharpening_brovey(rgb.data, pan.data, 0.2, 'uint16')
        if capture.bits_per_pixel != 8:
            max_bits = 2**capture.bits_per_pixel - 1
            rgb.rescale(in_range=((0, max_bits),))
        return rgb.render(img_format=format)
