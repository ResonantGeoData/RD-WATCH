from django.db import models


class Region(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    crs = models.CharField(max_length=255, blank=True, null=True)
    mgrs = models.CharField(max_length=255, blank=True, null=True)
    geometry = models.TextField(blank=True, null=True)
    area = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'region'
