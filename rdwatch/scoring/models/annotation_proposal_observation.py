from django.contrib.gis.db import models

from rdwatch.scoring.models import AnnotationProposalSet, AnnotationProposalSite


class AnnotationProposalObservation(models.Model):
    annotation_proposal_set_uuid = models.ForeignKey(
        AnnotationProposalSet,
        models.DO_NOTHING,
        db_column='annotation_proposal_set_uuid',
    )
    annotation_proposal_site_uuid = models.ForeignKey(
        AnnotationProposalSite,
        models.DO_NOTHING,
        db_column='annotation_proposal_site_uuid',
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
        app_label = 'rdwatch.scoring'
        db_table = 'annotation_proposal_observation'
