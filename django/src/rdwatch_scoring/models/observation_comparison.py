from django.contrib.gis.db import models
from rdwatch_scoring.models import Observation


class ObservationComparison(models.Model):
    observation_truth_uuid = models.ForeignKey(
        Observation,
        models.DO_NOTHING,
        related_name='comparison_truth_uuid',
        db_column='observation_truth_uuid',
    )
    observation_proposal_uuid = models.ForeignKey(
        Observation,
        models.DO_NOTHING,
        related_name='comparison_proposal_uuid',
        db_column='observation_proposal_uuid',
        blank=True,
        null=True,
    )
    intersection_geometry = models.TextField(blank=True, null=True)
    union_geometry = models.TextField(blank=True, null=True)
    intersection_area = models.FloatField(blank=True, null=True)
    union_area = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        app_label = 'rdwatch_scoring'
        db_table = 'observation_comparison'
