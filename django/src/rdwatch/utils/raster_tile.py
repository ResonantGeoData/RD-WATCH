import rasterio  # type: ignore
from rio_tiler.io.cogeo import COGReader


def get_raster_tile(uri: str, z: int, x: int, y: int) -> bytes:
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'):
        if uri.startswith('https://sentinel-cogs.s3.us-west-2.amazonaws.com'):
            with rasterio.Env(AWS_NO_SIGN_REQUEST='YES'):
                s3_uri = 's3://sentinel-cogs/' + uri[49:]
                with COGReader(input=s3_uri) as cog:
                    return cog.tile(x, y, z, tilesize=512).render(img_format='WEBP')
        with COGReader(input=uri) as cog:
            return cog.tile(x, y, z, tilesize=512).render(img_format='WEBP')


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
