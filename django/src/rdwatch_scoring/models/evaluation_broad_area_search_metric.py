from django.contrib.gis.db import models


class EvaluationBroadAreaSearchMetric(models.Model):
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
    tp_sites = models.IntegerField(blank=True, null=True)
    tp_exact = models.IntegerField(blank=True, null=True)
    tp_under = models.IntegerField(blank=True, null=True)
    tp_under_iou = models.IntegerField(blank=True, null=True)
    tp_under_iot = models.IntegerField(blank=True, null=True)
    tp_over = models.IntegerField(blank=True, null=True)
    fp_sites = models.IntegerField(blank=True, null=True)
    fp_area = models.FloatField(blank=True, null=True)
    ffpa = models.FloatField(blank=True, null=True)
    proposal_area = models.FloatField(blank=True, null=True)
    fpa = models.FloatField(blank=True, null=True)
    fn_sites = models.IntegerField(blank=True, null=True)
    truth_annotations = models.IntegerField(blank=True, null=True)
    truth_sites = models.IntegerField(blank=True, null=True)
    proposed_annotations = models.IntegerField(blank=True, null=True)
    proposed_sites = models.IntegerField(blank=True, null=True)
    total_sites = models.IntegerField(blank=True, null=True)
    truth_slices = models.IntegerField(blank=True, null=True)
    proposed_slices = models.IntegerField(blank=True, null=True)
    precision = models.FloatField(blank=True, null=True)
    recall_pd = models.FloatField(blank=True, null=True)
    f1 = models.FloatField(blank=True, null=True)
    spatial_far = models.FloatField(blank=True, null=True)
    temporal_far = models.FloatField(blank=True, null=True)
    images_far = models.FloatField(blank=True, null=True)
    min_spatial_distance = models.FloatField(blank=True, null=True)
    central_spatial_distance = models.FloatField(blank=True, null=True)
    max_spatial_distance = models.FloatField(blank=True, null=True)
    min_temporal_distance = models.FloatField(blank=True, null=True)
    central_temporal_distance = models.FloatField(blank=True, null=True)
    max_temporal_distance = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        app_label = 'rdwatch_scoring'
        db_table = 'evaluation_broad_area_search_metric'
