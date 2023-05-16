import logging

import numpy as np
import rasterio  # type: ignore
from rio_tiler.io.cogeo import COGReader
from rio_tiler.models import ImageData

logger = logging.getLogger(__name__)

base_scale_value = 128


def process_image(cog: COGReader, img: ImageData):
    stats = cog.statistics()
    info = cog.info()
    img_data = img.data
    # Get the nodata value from the COG object or set it to -9999 if not present
    nodata_type = getattr(info, 'nodata_type', None)
    nodata_value = getattr(info, 'nodata', 1) if nodata_type is not None else -9999

    # check std deviation values
    std_total = 0
    for key in stats.keys():
        std_total += stats[key].std
    std_total / len(stats.keys())
    min_values = np.array(
        [stats[str(i + 1)].percentile_2 for i in range(img_data.shape[0])]
    )
    max_values = np.array(
        [stats[str(i + 1)].percentile_98 for i in range(img_data.shape[0])]
    )
    img_masked = np.ma.masked_equal(img_data, nodata_value)
    # is8bit = img_data.dtype == np.uint8
    # logger.warning(f'STD Val AVG: {std_val}')
    # logger.warning(f'MinValues: {min_values}')
    # logger.warning(f'MaxValues: {max_values}')
    # logger.warning(f'NoDataType: {nodata_type}')
    # logger.warning(f'NoDataValue: {nodata_value}')
    # logger.warning(f'is8bit: {is8bit}')

    if not np.array_equal(min_values, np.array([1.0, 1.0, 1.0])):
        return img

    # Check if any min_values is equal to nodata_value and
    # replace with the minimum of the corresponding band
    for i, min_value in enumerate(min_values):
        if min_value == nodata_value:
            min_values[i] = base_scale_value

    logger.warning(f'UpdatedMin: {min_values}')

    # Rescale the image using the calculated percentiles
    img_8bit = np.zeros_like(img_data, dtype=np.uint8)
    for band in range(img_data.shape[0]):
        img_8bit[band] = np.ma.filled(
            (
                (img_masked[band] - min_values[band])
                * 255
                / (max_values[band] - min_values[band])
            )
            .clip(0, 255)
            .astype(np.uint8),
            fill_value=nodata_value,
        )

    # Save the rescaled image
    img.data = img_8bit

    return img


def get_raster_tile(uri: str, z: int, x: int, y: int) -> bytes:
    # logger.warning(f'SITE URI: {uri}')
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'):
        if uri.startswith('https://sentinel-cogs.s3.us-west-2.amazonaws.com'):
            with rasterio.Env(AWS_NO_SIGN_REQUEST='YES'):
                s3_uri = 's3://sentinel-cogs/' + uri[49:]
                with COGReader(input=s3_uri) as cog:
                    img = cog.tile(x, y, z, tilesize=512)
                    img = process_image(cog, img)
                    return img.render(img_format='WEBP')
        with COGReader(input=uri) as cog:
            img = cog.tile(x, y, z, tilesize=512)
            img = process_image(cog, img)
            return img.render(img_format='WEBP')


def get_raster_bbox(
    uri: str, bbox: tuple[float, float, float, float], format='JPEG'
) -> bytes:
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'):
        if uri.startswith('https://sentinel-cogs.s3.us-west-2.amazonaws.com'):
            with rasterio.Env(AWS_NO_SIGN_REQUEST='YES'):
                s3_uri = 's3://sentinel-cogs/' + uri[49:]
                with COGReader(input=s3_uri) as cog:
                    img = cog.part(bbox)
                    img = process_image(cog, img)
                    return img.render(img_format=format)
        with COGReader(input=uri) as cog:
            img = cog.part(bbox)
            img = process_image(cog, img)
            return img.render(img_format=format)
