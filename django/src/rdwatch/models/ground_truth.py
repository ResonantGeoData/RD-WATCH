from django.contrib.gis.db import models


class GroundTruth(models.Model):
    geometry = models.PolygonField(
        help_text="Footprint of ground truth",
        srid=3857,
    )

    def __str__(self):
        return f"GroundTruth:{self.pk}"

    class Meta:
        indexes = [
            models.Index(fields=["geometry"]),
        ]
