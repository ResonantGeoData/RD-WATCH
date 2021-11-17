"""Base classes for raster dataset entries."""
from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django_extensions.db.models import TimeStampedModel
from rgd.models import DB_SRID, ChecksumFile, SpatialEntry
from rgd.models.mixins import PermissionPathMixin, TaskEventMixin
from rgd_imagery.models import Raster
from semantic_version.django_fields import VersionField

from .tasks import jobs as tasks


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


class STACFile(TimeStampedModel, TaskEventMixin, PermissionPathMixin):
    """Catalog STAC Items as files.

    This has an associated task that will ingest the STAC Item.
    """

    file = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE, related_name='+')
    server_modified = models.DateTimeField(null=True, default=None, blank=True)
    processed = models.DateTimeField(null=True, default=None, blank=True)
    outline = models.GeometryField(srid=DB_SRID, null=True, blank=True)

    raster = models.ForeignKey(
        Raster, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )

    task_funcs = (tasks.task_ingest_stac_file,)
    permissions_paths = [('file', ChecksumFile)]

    def _post_delete(self, *args, **kwargs):
        # First delete all the images in the image set
        #  this will cascade to the annotations
        if self.raster:
            images = self.raster.image_set.images.all()
            for image in images:
                # This should cascade to the Image and the ImageMeta
                image.file.delete()
            # Now delete the empty image set
            self.raster.image_set.delete()
        # Additionally, delete the JSON file
        try:
            self.file.delete()
        except ChecksumFile.DoesNotExist:
            pass


class GoogleCloudCatalog(TimeStampedModel):
    index = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE, related_name='+')


class GoogleCloudRecord(TimeStampedModel, TaskEventMixin):
    catalog = models.ForeignKey(GoogleCloudCatalog, on_delete=models.CASCADE)
    base_url = models.TextField(unique=True)
    cloud_cover = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    product_id = models.TextField()
    sensor_id = models.TextField()
    sensing_time = models.DateTimeField()
    outline = models.PolygonField()
