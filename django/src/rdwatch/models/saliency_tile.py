from django.contrib.gis.db import models
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators
from django.contrib.postgres.indexes import OpClass
from django.db.models.lookups import Exact
from rdwatch.db.functions import (
    RasterEnvelope,
    RasterHeight,
    RasterNumBands,
    RasterWidth,
)


class SaliencyTile(models.Model):
    raster = models.RasterField(
        help_text="A 64x64 single-band tile from the full saliency map",
        srid=3857,
    )
    saliency = models.ForeignKey(
        to="Saliency",
        on_delete=models.CASCADE,
        help_text="The saliency map this tile belongs to",
    )

    class Meta:
        indexes = [models.Index(fields=["raster"]), models.Index(fields=["saliency"])]
        constraints = [
            ExclusionConstraint(
                name="exclude_overlapping_raster",
                violation_error_message=(
                    "Tiles for the same raster cannot overlap"
                ),  # type: ignore
                expressions=[
                    (
                        OpClass(RasterEnvelope("raster"), name="gist_geometry_ops_2d"),
                        RangeOperators.OVERLAPS,
                    ),
                    ("saliency", RangeOperators.EQUAL),
                ],
            ),
            models.CheckConstraint(
                name="check_64_height_raster",
                violation_error_message="Tile must be 64 pixels high",
                check=Exact(RasterHeight("raster"), 64),  # type: ignore
            ),
            models.CheckConstraint(
                name="check_64_width_raster",
                violation_error_message="Tile must be 64 pixels wide",
                check=Exact(RasterWidth("raster"), 64),  # type: ignore
            ),
            models.CheckConstraint(
                name="check_1_band_raster",
                violation_error_message="Tile must only have one band",
                check=Exact(RasterNumBands("raster"), 1),  # type: ignore
            ),
        ]
