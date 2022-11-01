from rio_tiler.io.cogeo import COGReader
from rio_tiler.utils import pansharpening_brovey

from rdwatch.utils.worldview.satellite_captures import WorldViewCapture


def get_worldview_visual_tile(
    capture: WorldViewCapture, z: int, x: int, y: int
) -> bytes:
    with COGReader(input=capture.uri) as img:
        info = img.info()
        red = info.colorinterp.index("red") + 1  # type: ignore
        green = info.colorinterp.index("green") + 1  # type: ignore
        blue = info.colorinterp.index("blue") + 1  # type: ignore
        rgb = img.tile(x, y, z, tilesize=512, indexes=(red, green, blue))

    if capture.image_representation != "RGB" and capture.panuri:
        with COGReader(input=capture.panuri) as img:
            pan = img.tile(x, y, z, tilesize=512)
        rgb.data = pansharpening_brovey(rgb.data, pan.data, 0.2, "uint16")

    if capture.bits_per_pixel != 8:
        max_bits = 2**capture.bits_per_pixel - 1
        rgb.rescale(in_range=((0, max_bits),))

    if capture.image_representation != "RGB":
        rgb.apply_color_formula(
            (
                f"gamma R 1.3 "
                f"gamma G {1 - (0.03 / 3.0)} "
                f"gamma B {1 - 0.03} "
                f"sigmoidal RGB 5 0.2 "
                "saturation 1.2"
            )
        )

    return rgb.render(img_format="WEBP")
