from django.contrib.gis.db import models


class EvaluationActivityClassificationPhase(models.Model):
    evaluation_run_uuid = models.ForeignKey(
        'EvaluationRun', models.DO_NOTHING, db_column='evaluation_run_uuid'
    )
    activity_type = models.CharField(max_length=255)
    date = models.DateField()
    site_truth = models.CharField(max_length=255)
    site_proposal = models.CharField(max_length=255)
    site_truth_phase = models.TextField(
        blank=True, null=True
    )  # This field type is a guess.
    site_proposal_phase = models.TextField(
        blank=True, null=True
    )  # This field type is a guess.

    class Meta:
        managed = False
        app_label = 'rdwatch_scoring'
        db_table = 'evaluation_activity_classification_phase'

