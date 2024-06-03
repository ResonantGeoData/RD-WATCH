from datetime import datetime

from django.contrib.gis.db import models

from rdwatch.scoring.models import AnnotationProposalSet, Region


class AnnotationProposalSiteLog(models.Model):
    annotation_proposal_set_uuid = models.ForeignKey(
        AnnotationProposalSet,
        models.DO_NOTHING,
        db_column='annotation_proposal_set_uuid',
    )
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
    uuid = models.CharField(max_length=255, null=False)
    proposal_status = models.CharField(max_length=255, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=False, default=datetime.utcnow())
    serial_id = models.AutoField(blank=True, primary_key=True)

    class Meta:
        managed = False
        app_label = 'rdwatch_scoring'
        db_table = 'annotation_proposal_site_log'
