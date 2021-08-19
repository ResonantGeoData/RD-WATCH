"""Base classes for raster dataset entries."""
from django.contrib.gis.db import models
from django_extensions.db.models import TimeStampedModel
from rgd.models import SpatialEntry
from rgd.models.mixins import TaskEventMixin


class Region(TimeStampedModel, SpatialEntry, TaskEventMixin):
    """Basically a FeatureCollection GeoJSON object.

    Reference: https://infrastructure.smartgitlab.com/docs/pages/api_documentation.html#region-model

    We will use this to track what areas of Landsat/Sentinel imagery are ingested.
    """

    properties = models.JSONField(null=True, blank=True)


class Feature(TimeStampedModel, SpatialEntry):
    parent_region = models.ForeignKey(Region, on_delete=models.CASCADE)

    properties = models.JSONField()
    start_date = models.DateField()
    end_date = models.DateField()
