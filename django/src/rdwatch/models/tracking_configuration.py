from django.contrib.gis.db import models


class TrackingConfiguration(models.Model):
    timestamp = models.DateTimeField(
        help_text="Time when evaluating this tracking configuration was finished"
    )
    threshold = models.FloatField(
        help_text="Threshold for tracking site in time",
    )

    class Meta:
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["threshold"]),
        ]
