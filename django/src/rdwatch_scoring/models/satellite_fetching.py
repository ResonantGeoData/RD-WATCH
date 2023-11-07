from django.db import models

from rdwatch.models.satellite_fetching import BaseSatelliteFetching


class SatelliteFetching(BaseSatelliteFetching):
    site = models.CharField(max_length=255)
    model_run_uuid = models.CharField(max_length=255, blank=True, null=True)
