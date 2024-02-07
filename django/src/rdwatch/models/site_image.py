from __future__ import annotations

from abc import abstractmethod

from django.contrib.gis.db.models import PolygonField
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GistIndex
from django.db import models
from django.dispatch import receiver


class BaseSiteImage(models.Model):
    class Meta:
        abstract = True

    @property
    @abstractmethod
    def site(self):
        raise NotImplementedError()

    @property
    @abstractmethod
    def observation(self):
        raise NotImplementedError()

    timestamp = models.DateTimeField(
        help_text="The source image's timestamp",
    )
    image = models.FileField(null=True, blank=True)
    image_embedding = models.FileField(null=True, blank=True)
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
    aws_location = models.CharField(
        max_length=2048,
        blank=True,
        help_text='S3 Link to base file used to download this image',
    )

    def __str__(self) -> str:
        time = self.timestamp.isoformat()
        return f'{self.site}.{self.source}@{time}'


@receiver(models.signals.pre_delete, sender=BaseSiteImage)
def delete_content(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
    if instance.image_embedding:
        instance.image_embedding.delete(save=False)



class SiteImage(BaseSiteImage):
    class Meta:
        indexes = [GistIndex(fields=['timestamp'])]

    site = models.ForeignKey(
        to='SiteEvaluation',
        on_delete=models.CASCADE,
        db_index=True,
    )
    observation = models.ForeignKey(
        to='SiteObservation',
        on_delete=models.CASCADE,
        null=True,
        db_index=True,
    )
