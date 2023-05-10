import rasterio  # type: ignore
from rio_tiler.io.cogeo import COGReader
from rio_tiler.models import ImageData
import logging
import numpy as np

logger = logging.getLogger(__name__)

nodata_value = -9999
def rescale(image: ImageData):
    # Calculate the percentiles for each band
    img = image.data
    low_percentile = 2
    high_percentile = 98

    img_masked = np.ma.masked_equal(img, nodata_value)

    min_values = np.percentile(img_masked, low_percentile, axis=(1, 2))
    max_values = np.percentile(img_masked, high_percentile, axis=(1, 2))
    # Rescale the image using the calculated percentiles
    logger.warning(f'Max: {max_values}, Min: {min_values}')
    img_8bit = np.zeros_like(img, dtype=np.uint8)
    for band in range(img.shape[0]):
        img_8bit[band] = np.ma.filled(
            ((img_masked[band] - min_values[band]) * 255 / (max_values[band] - min_values[band])).clip(0, 255).astype(np.uint8),
            fill_value=nodata_value,
        )    # Save the rescaled image
    image.data = img_8bit
    return image

def get_raster_tile(uri: str, z: int, x: int, y: int) -> bytes:
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'):
        if uri.startswith('https://sentinel-cogs.s3.us-west-2.amazonaws.com'):
            with rasterio.Env(AWS_NO_SIGN_REQUEST='YES'):
                s3_uri = 's3://sentinel-cogs/' + uri[49:]
                with COGReader(input=s3_uri, nodata=nodata_value) as cog:
                    # stats = cog.statistics()
                    # info = cog.info()
                    # logger.warning(info.dict())
                    # for key in stats.keys():
                    #     min_val = stats[key].dict().get('min', False)
                    #     max_val = stats[key].dict().get('max', False)
                    #     high = stats[key].dict().get('percentile_98', False)
                    #     low = stats[key].dict().get('percentile_2', False)
                    #     logger.warning(f'Low: {low} High: {high}')
                    #     logger.warning(f'Min: {min_val} Max: {max_val}')
                    img = cog.tile(x, y, z, tilesize=512)
                    img = rescale(img)
                    return img.render(img_format='WEBP')
        with COGReader(input=uri, nodata=nodata_value) as cog:
            # stats = cog.statistics()
            # info = cog.info()
            # logger.warning(info.dict())
            # for key in stats.keys():
            #     min_val = stats[key].dict().get('min', False)
            #     max_val = stats[key].dict().get('max', False)
            #     high = stats[key].dict().get('percentile_98', False)
            #     low = stats[key].dict().get('percentile_2', False)
            #     logger.warning(f'Low: {low} High: {high}')
            #     logger.warning(f'Min: {min_val} Max: {max_val}')
            img = cog.tile(x, y, z, tilesize=512)
            img = rescale(img)
            return img.render(img_format='WEBP')


def get_raster_bbox(
    uri: str, bbox: tuple[float, float, float, float], format='JPEG'
) -> bytes:
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'):
        if uri.startswith('https://sentinel-cogs.s3.us-west-2.amazonaws.com'):
            with rasterio.Env(AWS_NO_SIGN_REQUEST='YES'):
                s3_uri = 's3://sentinel-cogs/' + uri[49:]
                with COGReader(input=s3_uri) as cog:
                    return cog.part(bbox).render(img_format=format)
        with COGReader(input=uri) as cog:
            return cog.part(bbox).render(img_format=format)
