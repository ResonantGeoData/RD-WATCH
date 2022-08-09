from django.contrib.gis.db import models


class Site(models.Model):
    ACTIVE_CONSTRUCTION = "AC"
    SITE_PREPERATION = "SP"
    LABEL_CHOICES = [
        (ACTIVE_CONSTRUCTION, "Active Construction"),
        (SITE_PREPERATION, "Site Preperation"),
    ]
    configuration = models.ForeignKey(
        to="TrackingConfiguration",
        on_delete=models.CASCADE,
    )
    saliency = models.ForeignKey(to="Saliency", on_delete=models.CASCADE)
    label = models.CharField(max_length=2, choices=LABEL_CHOICES)
    score = models.FloatField()
    geometry = models.MultiPolygonField()
