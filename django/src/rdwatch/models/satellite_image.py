from django.contrib.gis.db import models


class SatelliteImage(models.Model):
    LANDSAT_8 = "L8"
    SENTINEL_2 = "S2"
    SENSOR_CHOICES = [
        (LANDSAT_8, "Landsat 8"),
        (SENTINEL_2, "Sentinel 2"),
    ]
    sensor = models.CharField(
        max_length=2,
        choices=SENSOR_CHOICES,
        help_text="The source satellite sensor",
    )
    timestamp = models.DateTimeField(
        help_text="The time the source imagery was captured",
    )

    def __str__(self):
        return f"SatelliteImage:{self.pk}"

    class Meta:
        indexes = [models.Index(fields=["sensor"]), models.Index(fields=["timestamp"])]
        constraints = [
            models.UniqueConstraint(
                name="unique_satelliteimage",
                fields=["sensor", "timestamp"],
                violation_error_message=(  # type: ignore
                    "Satellite image already exists."
                ),
            ),
        ]
