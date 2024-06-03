from django.contrib.gis.db import models

from rdwatch.scoring.models import AnnotationGroundTruthSite


class AnnotationGroundTruthObservation(models.Model):
    annotation_ground_truth_site_uuid = models.ForeignKey(
        AnnotationGroundTruthSite,
        models.DO_NOTHING,
        db_column='annotation_ground_truth_site_uuid',
    )
    site_id = models.CharField(max_length=255, blank=True, null=True)
    observation_date = models.DateField(blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    sensor_name = models.CharField(max_length=255, blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
    current_phase = models.CharField(max_length=255, blank=True, null=True)
    is_occluded = models.CharField(max_length=255, blank=True, null=True)
    is_site_boundary = models.CharField(max_length=255, blank=True, null=True)
    geometry = models.TextField(blank=True, null=True)
    uuid = models.CharField(max_length=255, primary_key=True)

    class Meta:
        managed = False
        app_label = 'rdwatch_scoring'
        db_table = 'annotation_ground_truth_observation'
