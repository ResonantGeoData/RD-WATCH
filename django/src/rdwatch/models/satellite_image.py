from django.contrib.gis.db.models import PolygonField
from django.contrib.postgres.indexes import GistIndex
from django.core.validators import URLValidator
from django.db import models
from rdwatch.validators import validate_bbox


class SatelliteImage(models.Model):
    constellation = models.ForeignKey(
        to="Constellation",
        on_delete=models.PROTECT,
        help_text="The source satellite constellation",
        db_index=True,
    )
    spectrum = models.ForeignKey(
        to="CommonBand",
        on_delete=models.PROTECT,
        help_text="The spectrum range this raster captures",
        db_index=True,
    )
    level = models.ForeignKey(
        to="ProcessingLevel",
        on_delete=models.PROTECT,
        help_text="The processing level of the imagery",
        db_index=True,
    )
    timestamp = models.DateTimeField(
        help_text="The time the imagery was captured",
    )
    bbox = PolygonField(
        help_text="The spatial extent of the image",
        srid=3857,
        spatial_index=True,
        validators=[validate_bbox],
    )
    uri = models.CharField(
        help_text="The URI of the raster",
        max_length=200,
        validators=[URLValidator(schemes=["http", "https", "s3"])],
        unique=True,
    )

    def __str__(self):
        sat = self.constellation
        lvl = self.level
        bnd = self.spectrum
        tim = self.timestamp.isoformat()
        return f"{sat}.{lvl}[{bnd}]@{tim}"

    class Meta:
        default_related_name = "satellite_images"
        indexes = [GistIndex(fields=["timestamp"])]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "constellation",
                    "spectrum",
                    "level",
                    "timestamp",
                ],
                name="uniq_satimg",
                violation_error_message="Image already exists.",  # type: ignore
            ),
        ]
