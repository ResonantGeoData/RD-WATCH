from django.contrib.gis.db import models


class EvaluationBroadAreaSearchProposal(models.Model):
    id = models.IntegerField(primary_key=True)
    evaluation_run_uuid = models.ForeignKey(
        'EvaluationRun', models.DO_NOTHING, db_column='evaluation_run_uuid'
    )
    activity_type = models.CharField(max_length=255)
    rho = models.FloatField()
    tau = models.FloatField()
    min_area = models.FloatField()
    min_confidence_score = models.FloatField()
    min_spatial_distance_threshold = models.FloatField(blank=True, null=True)
    central_spatial_distance_threshold = models.FloatField(blank=True, null=True)
    max_spatial_distance_threshold = models.FloatField(blank=True, null=True)
    min_temporal_distance_threshold = models.FloatField(blank=True, null=True)
    central_temporal_distance_threshold = models.FloatField(blank=True, null=True)
    max_temporal_distance_threshold = models.FloatField(blank=True, null=True)
    site_proposal = models.CharField(max_length=255)
    site_proposal_area = models.FloatField()
    site_truth_matched = models.TextField(
        blank=True, null=True
    )  # This field type is a guess.
    site_truth_matched_count = models.IntegerField(blank=True, null=True)
    association_status = models.CharField(max_length=255)
    associated = models.BooleanField()
    color_code = models.IntegerField()

    class Meta:
        managed = False
        app_label = 'scoring'
        db_table = 'evaluation_broad_area_search_proposal'
