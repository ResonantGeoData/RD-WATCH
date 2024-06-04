from django.db import models


class Performer(models.Model):
    id = models.IntegerField(primary_key=True)
    performer_name = models.CharField(max_length=255, null=False)
    performer_code = models.CharField(max_length=255, null=False)

    class Meta:
        managed = False
        app_label = 'scoring'
        db_table = 'performer_code_mapping'
