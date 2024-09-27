from django.contrib.gis.db import models

from rdwatch.scoring.models import EvaluationRun, Region


class Site(models.Model):
    uuid = models.CharField(primary_key=True, max_length=255)
    site_id = models.CharField(max_length=255)
    region = models.ForeignKey(Region, models.DO_NOTHING)
    evaluation_run_uuid = models.ForeignKey(
        EvaluationRun, models.DO_NOTHING, db_column='evaluation_run_uuid'
    )
    originator = models.CharField(max_length=255)
    version = models.CharField(max_length=255)
    crs = models.CharField(max_length=255, blank=True, null=True)
    mgrs = models.CharField(max_length=255, blank=True, null=True)
    status_annotated = models.CharField(max_length=255, blank=True, null=True)
    predicted_phase = models.CharField(max_length=255, blank=True, null=True)
    predicted_date = models.DateField(blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
    union_geometry = models.TextField(blank=True, null=True)
    union_area = models.FloatField(blank=True, null=True)
    sites = models.TextField(blank=True, null=True)  # This field type is a guess.
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    start_activity = models.DateField(blank=True, null=True)
    end_activity = models.DateField(blank=True, null=True)
    len_activity = models.IntegerField(blank=True, null=True)
    end_observed_activity = models.DateField(blank=True, null=True)
    len_observed_activity = models.IntegerField(blank=True, null=True)
    max_area = models.FloatField(blank=True, null=True)
    first_obs_date = models.DateField(blank=True, null=True)
    last_obs_date = models.DateField(blank=True, null=True)
    confidence_score = models.FloatField(blank=True, null=True)

    point_geometry = models.TextField(blank=True, null=True)
    point_status = models.CharField(max_length=255, blank=True, null=True)
    point_date = models.DateField(blank=True, null=True)
    point_version = models.CharField(max_length=255, blank=True, null=True)
    point_date_version = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        app_label = 'scoring'
        db_table = 'site'
