from django.contrib.gis.db import models

from rdwatch.scoring.models import Region


class AnnotationGroundTruthSite(models.Model):
    site_id = models.CharField(max_length=255, blank=True, null=True)
    region_id = models.ForeignKey(Region, models.DO_NOTHING, db_column='region_id')
    mgrs = models.CharField(max_length=255, blank=True, null=True)
    version = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    originator = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    validated = models.BooleanField(blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
    geometry = models.TextField(blank=True, null=True)
    uuid = models.CharField(max_length=255, primary_key=True)

    class Meta:
        managed = False
        app_label = 'rdwatch_scoring'
        db_table = 'annotation_ground_truth_site'
