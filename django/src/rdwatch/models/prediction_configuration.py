from django.contrib.gis.db import models


class PredictionConfiguration(models.Model):
    slug = models.SlugField(max_length=8)
    timestamp = models.DateTimeField(
        help_text="Time when evaluating this prediction configuration was finished"
    )

    def __str__(self):
        return f"PredictionConfiguration:{self.pk}"

    class Meta:
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["timestamp"]),
        ]
