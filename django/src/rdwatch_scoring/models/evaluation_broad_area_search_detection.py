from django.contrib.gis.db import models


class EvaluationBroadAreaSearchDetection(models.Model):
    id = models.IntegerField(primary_key=True)
    evaluation_run_uuid = models.ForeignKey(
        'EvaluationRun', models.DO_NOTHING, db_column='evaluation_run_uuid'
    )
    activity_type = models.CharField(max_length=255)
    rho = models.FloatField()
    tau = models.FloatField()
    min_area = models.FloatField()
    site_truth = models.CharField(max_length=255)
    site_truth_type = models.CharField(max_length=255)
    site_truth_area = models.FloatField()
    site_proposal_matched = models.TextField(
        blank=True, null=True
    )  # This field type is a guess.
    site_proposal_matched_count = models.IntegerField(blank=True, null=True)
    detection_score = models.FloatField(blank=True, null=True)
    spatial_overlap = models.FloatField(blank=True, null=True)
    temporal_iot = models.FloatField(blank=True, null=True)
    temporal_iop = models.FloatField(blank=True, null=True)
    association_status = models.CharField(max_length=255)
    associated = models.BooleanField()
    color_code = models.IntegerField()

    class Meta:
        managed = False
        app_label = 'rdwatch_scoring'
        db_table = 'evaluation_broad_area_search_detection'

