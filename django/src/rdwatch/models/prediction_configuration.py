from django.contrib.gis.db import models


class PredictionConfiguration(models.Model):
    timestamp = models.DateTimeField(
        help_text="Time when evaluating this prediction configuration was finished"
    )

    class Meta:
        indexes = [models.Index(fields=["timestamp"])]
