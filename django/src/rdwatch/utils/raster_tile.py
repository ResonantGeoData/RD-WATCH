import rasterio  # type: ignore
from rio_tiler.io.cogeo import COGReader
from rio_tiler.io.stac import STACReader


def get_raster_tile(uri: str, z: int, x: int, y: int) -> bytes:
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="YES",
        CPL_VSIL_CURL_CACHE_SIZE="200000000",
    ):
        if uri.startswith("https://sentinel-cogs.s3.us-west-2.amazonaws.com"):
            with rasterio.Env(AWS_NO_SIGN_REQUEST="YES"):
                s3_uri = "s3://sentinel-cogs/" + uri[49:]
                with COGReader(input=s3_uri) as cog:
                    return cog.tile(x, y, z, tilesize=512).render(img_format="WEBP")
        with COGReader(input=uri) as cog:
            return cog.tile(x, y, z, tilesize=512).render(img_format="WEBP")


def get_rgb_image_tile(stac_item_uri: str, z: int, x: int, y: int) -> bytes:
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="YES",
        CPL_VSIL_CURL_CACHE_SIZE="200000000",
    ):
        with STACReader(
            input=stac_item_uri,
            include_assets={"red", "green", "blue"},
        ) as stac:
            r = stac.tile(
                x,
                y,
                z,
                assets={"red", "green", "blue"},
            )
            return r
