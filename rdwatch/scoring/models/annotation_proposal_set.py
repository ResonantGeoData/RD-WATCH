from django.contrib.gis.db import models

from rdwatch_scoring.models import Region


class AnnotationProposalSet(models.Model):
    uuid = models.CharField(primary_key=True, max_length=255)
    region_id = models.ForeignKey(Region, models.DO_NOTHING, db_column='region_id')
    originator = models.CharField(max_length=255, blank=True, null=True)
    create_datetime = models.DateTimeField(blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        app_label = 'rdwatch_scoring'
        db_table = 'annotation_proposal_set'
