from django.contrib.gis.db import models


class PredictionConfiguration(models.Model):
    timestamp = models.DateTimeField(
        help_text="Time when evaluating this prediction configuration was finished"
    )

    def __str__(self):
        return f"PredictionConfiguration:{self.pk}"

    class Meta:
        indexes = [models.Index(fields=["timestamp"])]
