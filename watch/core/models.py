"""Base classes for raster dataset entries."""
from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile, SpatialEntry
from rgd.models.mixins import TaskEventMixin
from semantic_version.django_fields import VersionField


class Region(TimeStampedModel, SpatialEntry, TaskEventMixin):
    """Basically a FeatureCollection GeoJSON object.

    Reference: https://infrastructure.smartgitlab.com/docs/pages/api_documentation.html#region-model

    We will use this to track what areas of Landsat/Sentinel imagery are ingested.
    """

    properties = models.JSONField(null=True, blank=True)
    version = VersionField(null=True, blank=True)


class Feature(TimeStampedModel, SpatialEntry):
    parent_region = models.ForeignKey(Region, on_delete=models.CASCADE)

    properties = models.JSONField()
    start_date = models.DateField()
    end_date = models.DateField()


class GoogleCloudCatalog(TimeStampedModel):
    index = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE, related_name='+')


class GoogleCloudRecord(TimeStampedModel, TaskEventMixin):
    catalog = models.ForeignKey(GoogleCloudCatalog, on_delete=models.CASCADE)
    base_url = models.TextField(unique=True)
    cloud_cover = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    product_id = models.TextField()
    sensor_id = models.TextField()
    sensing_time = models.DateTimeField()
    bbox = models.PolygonField()
