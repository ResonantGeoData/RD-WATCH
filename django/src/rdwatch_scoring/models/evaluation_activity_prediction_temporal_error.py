from django.contrib.gis.db import models


class EvaluationActivityPredictionTemporalError(models.Model):
    evaluation_run_uuid = models.ForeignKey(
        'EvaluationRun', models.DO_NOTHING, db_column='evaluation_run_uuid'
    )
    activity_type = models.CharField(max_length=255)
    site = models.CharField(max_length=255)
    metric = models.CharField(max_length=255)
    site_preparation = models.FloatField(blank=True, null=True)
    active_construction = models.FloatField(blank=True, null=True)
    post_construction = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        app_label = 'rdwatch_scoring'
        db_table = 'evaluation_activity_prediction_temporal_error'

