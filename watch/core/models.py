"""Base classes for raster dataset entries."""
from django.contrib.gis.db import models
from django_extensions.db.models import TimeStampedModel
from rgd.models import DB_SRID, ChecksumFile
from rgd.models.mixins import PermissionPathMixin, TaskEventMixin
from rgd_imagery.models import Raster

from .tasks import jobs as tasks


class PolygonFeature(models.Model):
    class Meta:
        abstract = True

    footprint = models.GeometryField(srid=DB_SRID)
    outline = models.GeometryField(srid=DB_SRID)


class Region(TimeStampedModel, PolygonFeature):
    """Basically a SiteCollection GeoJSON object.

    Reference: https://infrastructure.smartgitlab.com/docs/pages/api_documentation.html#region-model

    We will use this to track what areas of Landsat/Sentinel imagery are ingested.
    """

    region_id = models.CharField(max_length=1000, unique=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    properties = models.JSONField()


class Site(TimeStampedModel, PolygonFeature):
    """Site model for Observations.

    Null Parent Region
    ------------------

    If a site has not been associated to a region, the reserved region ID
    <two-letter country code>_Rxxx may be used. That is, the site declares the
    country that it belongs to (with the location of the centroid determining
    country ownership in the case of a border ambiguity), and it uses the
    literal string Rxxx rather than R followed by three digits.

    """

    parent_region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.CASCADE)
    site_id = models.CharField(max_length=1000, unique=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    properties = models.JSONField()


class Observation(TimeStampedModel, PolygonFeature):
    """Observation annotation model.

    Color hueristics: https://gitlab.kitware.com/smart/watch/-/blob/master/watch/heuristics.py
    https://gitlab.kitware.com/smart/watch/-/blob/master/watch/heuristics.py#L101
    https://gitlab.kitware.com/smart/watch/-/blob/master/watch/cli/kwcoco_to_geojson.py#L139
    https://docs.google.com/presentation/d/1UOK5QraI-HQE7tNEGUK2o6esaz-iWkiS/edit#slide=id.p9

    """

    parent_site = models.ForeignKey(Site, on_delete=models.CASCADE)
    properties = models.JSONField()
    observation_date = models.DateField(null=True, blank=True)


class STACFile(TimeStampedModel, TaskEventMixin, PermissionPathMixin):
    """Catalog STAC Items as files.

    This has an associated task that will ingest the STAC Item.
    """

    file = models.ForeignKey(ChecksumFile, unique=True, on_delete=models.CASCADE, related_name='+')
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
