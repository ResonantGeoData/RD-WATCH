from django.contrib.gis.db import models


class EvaluationRun(models.Model):
    uuid = models.CharField(primary_key=True, max_length=255)
    evaluation_phase = models.CharField(max_length=255)
    performer = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    mode = models.CharField(max_length=255)
    increment_start_date = models.DateField(blank=True, null=True)
    increment_end_date = models.DateField(blank=True, null=True)
    dag_run_id = models.CharField(max_length=255, blank=True, null=True)
    start_datetime = models.DateTimeField()
    success = models.BooleanField(blank=True, null=True)
    evaluation_number = models.IntegerField(blank=True, null=True)
    evaluation_run_number = models.IntegerField(blank=True, null=True)
    evaluation_increment_number = models.IntegerField(blank=True, null=True)
    provenance = models.ForeignKey(
        'Provenance', models.DO_NOTHING, blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = 'evaluation_run'
        unique_together = (
            (
                'performer',
                'region',
                'evaluation_number',
                'evaluation_run_number',
                'evaluation_increment_number',
            ),
        )


class Provenance(models.Model):
    test_harness_git_hash = models.CharField(max_length=255)
    small_site_threshold = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'provenance'
