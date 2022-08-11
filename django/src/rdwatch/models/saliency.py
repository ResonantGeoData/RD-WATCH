from django.contrib.gis.db import models


class Saliency(models.Model):
    configuration = models.ForeignKey(
        to="PredictionConfiguration",
        on_delete=models.CASCADE,
        help_text="The configuration profile used to generate this saliency map",
    )
    source = models.ForeignKey(
        to="SatelliteImage",
        on_delete=models.PROTECT,
        help_text="The source satellite imagery this saliency map was evaluated on",
    )

    class Meta:
        indexes = [
            models.Index(fields=["configuration"]),
            models.Index(fields=["source"]),
        ]
