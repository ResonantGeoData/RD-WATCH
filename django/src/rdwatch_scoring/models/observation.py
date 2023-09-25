from django.contrib.gis.db import models


class Observation(models.Model):
    uuid = models.CharField(primary_key=True, max_length=255)
    site_uuid = models.ForeignKey('Site', models.DO_NOTHING, db_column='site_uuid')
    date = models.DateField(blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    sensor = models.CharField(max_length=255, blank=True, null=True)
    phase = models.CharField(max_length=255, blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
    crs = models.CharField(max_length=255, blank=True, null=True)
    geometry = models.TextField(blank=True, null=True)
    is_site_boundary = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        app_label = 'rdwatch_scoring'
        db_table = 'observation'
