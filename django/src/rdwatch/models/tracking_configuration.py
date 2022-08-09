from django.contrib.gis.db import models


class TrackingConfiguration(models.Model):
    timestamp = models.DateTimeField()
    threshold = models.FloatField()
