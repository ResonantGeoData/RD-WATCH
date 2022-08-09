from django.contrib.gis.db import models


class Saliency(models.Model):
    configuration = models.ForeignKey(
        to="PredictionConfiguration",
        on_delete=models.CASCADE,
    )
    source = models.ForeignKey(to="SatelliteImage", on_delete=models.PROTECT)
