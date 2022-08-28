from django.contrib.gis.db import models


class Site(models.Model):
    geometry = models.PolygonField(
        help_text="Footprint of site",
        srid=3857,
    )
    score = models.FloatField(
        help_text="Score of site footprint",
    )

    def __str__(self):
        return f"Site:{self.pk}"

    class Meta:
        indexes = [
            models.Index(fields=["geometry"]),
            models.Index(fields=["score"]),
        ]
