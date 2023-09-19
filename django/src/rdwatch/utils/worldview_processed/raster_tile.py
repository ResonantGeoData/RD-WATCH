import logging
import multiprocessing

# We must import this explicitly, it is not imported by the top-level
# multiprocessing module.
import multiprocessing.pool
import time

import rasterio  # type: ignore
from rio_tiler.io.cogeo import COGReader
from rio_tiler.utils import pansharpening_brovey

from rdwatch.utils.worldview_processed.satellite_captures import (
    WorldViewProcessedCapture,
)

logger = logging.getLogger(__name__)

log_timing = False  # used to log the timing


class NoDaemonProcess(multiprocessing.Process):
    # make 'daemon' attribute always return False
    def _get_daemon(self):
        return False

    def _set_daemon(self, value):
        pass

    daemon = property(_get_daemon, _set_daemon)


# We sub-class multiprocessing.pool.Pool instead of multiprocessing.Pool
# because the latter is only a wrapper function, not a proper class.
class MyPool(multiprocessing.pool.Pool):
    Process = NoDaemonProcess


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
                rgb = img.tile(x, y, z, tilesize=512)
        if capture.panuri:
            logger.warning(f'PAN URI: {capture.panuri}')
            with COGReader(input=capture.panuri) as img:
                pan = img.tile(
                    x,
                    y,
                    z,
                    tilesize=512,
                )
                with COGReader(input=capture.uri) as rgbimg:
                    rgb = rgbimg.tile(x, y, z, tilesize=512)
                rgb.data = pansharpening_brovey(rgb.data, pan.data, 0.2, 'uint16')
            rgb.rescale(in_range=((0, 10000),))
        return rgb.render(img_format='WEBP')


def get_cog_image(uri, bbox):
    with COGReader(input=uri) as img:
        return img.part(bbox)


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
        startTime = time.time()
        if not capture.panuri:
            with COGReader(input=capture.uri) as img:
                logger.warning(f'Image URI: {capture.uri}')
                logger.warning(f'Base Info Time: {time.time() - startTime}')
                rgb = img.part(bbox)
                logger.warning(f'RGB Download Time: {time.time() - startTime}')

        if capture.panuri:
            logger.warning(f'Pan URI: {capture.panuri}')
            with COGReader(input=capture.panuri) as img:
                pan = img.part(bbox)
                logger.warning(f'Pan Download Time: {time.time() - startTime}')
                with COGReader(input=capture.uri) as rgbimg:
                    rgb = rgbimg.part(bbox, width=pan.width, height=pan.height)
                    logger.warning(f'RGB Download Time: {time.time() - startTime}')
                logger.warning(f'PanSharpening: {capture.panuri}')
                rgb.data = pansharpening_brovey(rgb.data, pan.data, 0.2, 'uint16')
                logger.warning(f'Pan Sharpening Time: {time.time() - startTime}')

        rgb.rescale(in_range=((0, 10000),))
        return rgb.render(img_format=format)
