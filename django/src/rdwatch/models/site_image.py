from django.contrib.postgres.indexes import GistIndex
from django.db import models
from django.dispatch import receiver
from django.contrib.gis.db.models import PolygonField
from django.contrib.postgres.fields import ArrayField


class SiteImage(models.Model):
    siteeval = models.ForeignKey(
        to='SiteEvaluation',
        on_delete=models.CASCADE,
        db_index=True,
    )
    siteobs = models.ForeignKey(
        to='SiteObservation',
        on_delete=models.CASCADE,
        null=True,
        db_index=True,
    )
    timestamp = models.DateTimeField(
        help_text="The source image's timestamp",
    )
    image = models.FileField(null=True, blank=True)
    cloudcover = models.FloatField(
        null=True, help_text='Cloud Cover associated with Image'
    )
    percent_black = models.FloatField(null=True, help_text='NoData coverage on image')
    source = models.CharField(
        max_length=2, blank=True, help_text='WV, S2, L8 imagery source'
    )
    image_bbox = PolygonField(
        help_text='Image Bounding Box',
        srid=4326,
        spatial_index=True,
        null=True,
        blank=True,
    )
    image_dimensions = ArrayField(models.IntegerField(), size=2, null=True)

    def __str__(self):
        time = self.timestamp.isoformat()
        return f'{self.siteeval}.{self.source}@{time}'

    class Meta:
        indexes = [GistIndex(fields=['timestamp'])]


@receiver(models.signals.pre_delete, sender=SiteImage)
def delete_content(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
