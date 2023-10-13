import logging
import time
from typing import Literal

import rasterio  # type: ignore
from rio_tiler.io.rasterio import Reader
from rio_tiler.utils import pansharpening_brovey

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
            with Reader(input=capture.uri) as img:
                rgb = img.tile(x, y, z, tilesize=512)
        if capture.panuri:
            logger.warning(f'PAN URI: {capture.panuri}')
            with Reader(input=capture.panuri) as img:
                pan = img.tile(
                    x,
                    y,
                    z,
                    tilesize=512,
                )
                with Reader(input=capture.uri) as rgbimg:
                    rgb = rgbimg.tile(x, y, z, tilesize=512)
                    rgb = rgb.from_array(
                        pansharpening_brovey(rgb.data, pan.data, 0.2, 'uint16')
                    )
            rgb.rescale(in_range=((0, 10000),))
        return rgb.render(img_format='WEBP')


def get_cog_image(uri, bbox):
    with Reader(input=uri) as img:
        return img.part(bbox)


def get_worldview_processed_visual_bbox(
    capture: WorldViewProcessedCapture,
    bbox: tuple[float, float, float, float],
    format='PNG',
    scale: Literal['default', 'bits'] = 'default',
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
            with Reader(input=capture.uri) as img:
                logger.warning(f'Image URI: {capture.uri}')
                logger.warning(f'Base Info Time: {time.time() - startTime}')
                rgb = img.part(bbox)
                logger.warning(f'RGB Download Time: {time.time() - startTime}')

        if capture.panuri:
            logger.warning(f'Pan URI: {capture.panuri}')
            with Reader(input=capture.panuri) as img:
                pan = img.part(bbox)
                logger.warning(f'Pan Download Time: {time.time() - startTime}')
                with Reader(input=capture.uri) as rgbimg:
                    rgb = rgbimg.part(bbox, width=pan.width, height=pan.height)
                    logger.warning(f'RGB Download Time: {time.time() - startTime}')
                    logger.warning(f'PanSharpening: {capture.panuri}')
                    rgb = rgb.from_array(
                        pansharpening_brovey(rgb.data, pan.data, 0.2, 'uint16')
                    )
                    logger.warning(f'Pan Sharpening Time: {time.time() - startTime}')

        if scale == 'default':
            rgb.rescale(in_range=((0, 10000),))
        elif scale == 'bits':
            if capture.bits_per_pixel != 8:
                max_bits = 2**capture.bits_per_pixel - 1
                rgb.rescale(in_range=((0, max_bits),))
        elif len(scale) == 2:  # scale is an integeter range
            rgb.rescale(in_range=((scale[0], scale[1]),))

        return rgb.render(img_format=format)
