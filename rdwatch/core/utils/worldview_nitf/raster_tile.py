import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Literal
from urllib.parse import urlparse

import boto3
import rasterio  # type: ignore
from rio_tiler.io.rasterio import Reader

from rdwatch.core.utils.worldview_nitf.satellite_captures import WorldViewNITFCapture

logger = logging.getLogger(__name__)


@contextmanager
def _download_nitf_image(uri: str) -> Generator[str, None, None]:
    s3 = boto3.client('s3')

    parsed_url = urlparse(uri)

    s3_bucket = parsed_url.netloc
    s3_path = parsed_url.path.lstrip('/')

    with NamedTemporaryFile(suffix='.nitf') as f:
        startTime = time.time()
        logger.info(f'Image URI: {uri}')
        logger.info(f'Base Info Time: {time.time() - startTime}')
        s3.download_fileobj(s3_bucket, s3_path, f)
        logger.info(f'RGB Download Time: {time.time() - startTime}')
        yield f.name


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
        with Reader(input=capture.uri) as img:
            rgb = img.tile(x, y, z, tilesize=512)
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
        GDAL_CACHEMAX=200,
        CPL_VSIL_CURL_CACHE_SIZE=20000000,
        GDAL_BAND_BLOCK_CACHE='HASHSET',
        GDAL_HTTP_MULTIPLEX='YES',
        GDAL_HTTP_VERSION=2,
        VSI_CACHE='TRUE',
        VSI_CACHE_SIZE=5000000,
    ):
        with _download_nitf_image(capture.uri) as nitf_filepath:
            with Reader(input=nitf_filepath) as img:
                rgb = img.part(bbox)

        if scale == 'default':
            rgb.rescale(in_range=((0, 10000),))
        elif scale == 'bits':
            if capture.bits_per_pixel != 8:
                max_bits = 2**capture.bits_per_pixel - 1
                rgb.rescale(in_range=((0, max_bits),))
        elif isinstance(scale, list) and len(scale) == 2:  # scale is an integeter range
            rgb.rescale(in_range=((scale[0], scale[1]),))

        return rgb.render(img_format=format)
