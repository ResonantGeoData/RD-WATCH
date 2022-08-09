from django.contrib.gis.db import models


class SaliencyTile(models.Model):
    raster = models.RasterField()
    saliency = models.ForeignKey(to="Saliency", on_delete=models.CASCADE)
