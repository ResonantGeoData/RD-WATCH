import logging
from typing import Literal

import rasterio  # type: ignore
import sentry_sdk
from rio_tiler.io.rasterio import Reader
from rio_tiler.models import ImageData
from rio_tiler.utils import pansharpening_brovey

from rdwatch.core.utils.worldview_nitf.satellite_captures import WorldViewNITFCapture

logger = logging.getLogger(__name__)


def find_channels(colorinterp):
    rgb_indexes = {}

    # Define the channels to look for
    channels = ['red', 'green', 'blue', 'gray']

    for index, channel in enumerate(colorinterp):
        if channel in channels:
            rgb_indexes[channel] = index

    # Return indexes as a tuple, band indexes are 1 BASED
    red = rgb_indexes.get('red', -1) + 1
    green = rgb_indexes.get('green', -1) + 1
    blue = rgb_indexes.get('blue', -1) + 1
    gray = rgb_indexes.get('gray', -1) + 1
    if red > 0 and green > 0 and blue > 0:
        return (red, green, blue)
    elif gray > 0:
        return gray
    else:
        raise ValueError(
            f'colorInterp: {colorinterp} for files does not have RGB or Gray channels'
        )


def get_worldview_nitf_tile(
    capture: WorldViewNITFCapture, z: int, x: int, y: int
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
        with Reader(input=capture.uri) as vis_img:
            information = vis_img.info()
            rgb_channels = find_channels(information.colorinterp)
            rgb = vis_img.tile(x, y, z, tilesize=512, indexes=rgb_channels)
        return rgb.render(img_format='WEBP')


def get_worldview_nitf_bbox(
    capture: WorldViewNITFCapture,
    bbox: tuple[float, float, float, float],
    format='PNG',
    scale: Literal['default', 'bits'] = 'bits',
) -> bytes:
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',
        GDAL_HTTP_MERGE_CONSECUTIVE_RANGES='YES',
        GDAL_HTTP_MULTIPLEX='YES',
        GDAL_HTTP_VERSION=2,
        CPL_VSIL_CURL_CHUNK_SIZE=524288,
    ):
        logger.info(f'Downloading WorldView NITF bbox: {bbox} scale: {scale}')
        with Reader(input=capture.uri) as vis_img:
            pan_chip = None
            if capture.panuri is not None:
                with Reader(input=capture.panuri) as pan_img:
                    try:
                        pan_chip = pan_img.part(bbox=bbox, dst_crs='epsg:4326')
                    except ValueError as e:
                        logger.info(f'Value Error: {e} - {capture.panuri}')
                        sentry_sdk.capture_exception(e)
                        return None
            size = (
                {'width': pan_chip.width, 'height': pan_chip.height} if pan_chip else {}
            )
            information = vis_img.info()
            rgb_channels = find_channels(information.colorinterp)
            if all(
                channel is not None for channel in rgb_channels
            ):  # Ensure all RGB channels exist
                try:
                    vis_chip = vis_img.part(
                        bbox=bbox,
                        dst_crs='epsg:4326',
                        indexes=rgb_channels,
                        **size,
                    )
                except ValueError as e:
                    logger.info(f'Value Error: {e} - {capture.uri}')
                    sentry_sdk.capture_exception(e)
                    return None
                if pan_chip:
                    final_chip = ImageData(
                        pansharpening_brovey(
                            vis_chip.data, pan_chip.data, 0.2, 'uint16'
                        )
                    )
                else:
                    final_chip = vis_chip

                statistics = list(final_chip.statistics().values())
                if scale == 'default':
                    in_range = tuple((item.min, item.max) for item in statistics)
                elif scale == 'bits':
                    in_range = tuple(
                        (item['percentile_2'], item['percentile_98'])
                        for item in statistics
                    )
                elif (
                    isinstance(scale, list) and len(scale) == 2
                ):  # scale is an integeter range
                    in_range = tuple((scale[0], scale[1]) for item in statistics)
                final_chip.rescale(in_range=in_range)
                return final_chip.render(img_format=format)
    return None
