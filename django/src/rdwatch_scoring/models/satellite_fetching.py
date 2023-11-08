from django.db import models

from rdwatch.models.satellite_fetching import BaseSatelliteFetching


class SatelliteFetching(BaseSatelliteFetching):
    site = models.CharField(max_length=255)
