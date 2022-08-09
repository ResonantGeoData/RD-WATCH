from django.contrib.gis.db import models


class PredictionConfiguration(models.Model):
    timestamp = models.DateTimeField()
