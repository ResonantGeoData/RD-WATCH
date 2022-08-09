from django.contrib.gis.db import models


class SatelliteImage(models.Model):
    LANDSAT_8 = "L8"
    SENTINEL_2 = "S2"
    SENSOR_CHOICES = [
        (LANDSAT_8, "Landsat 8"),
        (SENTINEL_2, "Sentinel 2"),
    ]
    sensor = models.CharField(max_length=2, choices=SENSOR_CHOICES)
    timestamp = models.DateTimeField()
