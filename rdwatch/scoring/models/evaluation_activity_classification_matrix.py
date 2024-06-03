from django.contrib.gis.db import models


class EvaluationActivityClassificationMatrix(models.Model):
    evaluation_run_uuid = models.ForeignKey(
        'EvaluationRun', models.DO_NOTHING, db_column='evaluation_run_uuid'
    )
    activity_type = models.CharField(max_length=255)
    site = models.CharField(max_length=255)
    phase_truth = models.CharField(max_length=255)
    phase_proposal_no_activity = models.IntegerField(blank=True, null=True)
    phase_proposal_site_preparation = models.IntegerField(blank=True, null=True)
    phase_proposal_active_construction = models.IntegerField(blank=True, null=True)
    phase_proposal_post_construction = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        app_label = 'rdwatch_scoring'
        db_table = 'evaluation_activity_classification_matrix'
