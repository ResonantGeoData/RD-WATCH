from django.contrib.gis.db import models
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators
from django.db.models.lookups import Exact
from rdwatch.db.functions import (
    RasterHeight,
    RasterNumBands,
    RasterWidth,
    RasterXRange,
    RasterYRange,
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

    def __str__(self):
        return f"SaliencyTile:{self.pk}"

    class Meta:
        indexes = [models.Index(fields=["raster"]), models.Index(fields=["saliency"])]
        constraints = [
            ExclusionConstraint(
                name="exclude_overlapping_raster",
                violation_error_message=(  # type: ignore
                    "Tiles for the same raster cannot overlap"
                ),
                expressions=[
                    (RasterXRange("raster"), RangeOperators.OVERLAPS),
                    (RasterYRange("raster"), RangeOperators.OVERLAPS),
                    ("saliency", RangeOperators.EQUAL),
                ],
            ),
            models.CheckConstraint(
                name="check_64_height_raster",
                violation_error_message="Tile must be 64 pixels high",  # type: ignore
                check=Exact(RasterHeight("raster"), 64),  # type: ignore
            ),
            models.CheckConstraint(
                name="check_64_width_raster",
                violation_error_message="Tile must be 64 pixels wide",  # type: ignore
                check=Exact(RasterWidth("raster"), 64),  # type: ignore
            ),
            models.CheckConstraint(
                name="check_1_band_raster",
                violation_error_message="Tile must only have one band",  # type: ignore
                check=Exact(RasterNumBands("raster"), 1),  # type: ignore
            ),
        ]
