from uuid import uuid4

from django_extensions.db.models import CreationDateTimeField

from django.contrib.auth.models import User
from django.contrib.gis.db.models import PolygonField
from django.db import models

from rdwatch.core.db.functions import BoundingBoxPolygon


class ModelRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    created = CreationDateTimeField()
    title = models.CharField(max_length=1000)
    performer = models.ForeignKey(
        to='Performer',
        on_delete=models.PROTECT,
        help_text='The team that produced this evaluation',
        db_index=True,
    )
    parameters = models.JSONField(
        help_text='The hyper parameters for an ML task',
        db_index=True,
    )
    evaluation = models.IntegerField(blank=True, null=True)
    evaluation_run = models.IntegerField(blank=True, null=True)
    expiration_time = models.DurationField(
        null=True,
        blank=True,
        help_text='Time relative to creation that this model run should be deleted.',
    )

    region = models.ForeignKey(
        to='Region',
        on_delete=models.PROTECT,
        help_text='The region this model run belongs to',
        db_index=True,
        related_name='model_runs',
    )

    class ProposalStatus(models.TextChoices):
        PROPOSAL = (
            'PROPOSAL'  # proposal is a proposal awaiting Adjudication/Confirmation
        )
        APPROVED = 'APPROVED'  # proposal is approved and merged into ground truth

    proposal = models.CharField(
        max_length=255,  # If we need future states
        blank=True,
        null=True,
        help_text='Fetching Status',
        choices=ProposalStatus.choices,
    )
    ground_truth = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    public = models.BooleanField(default=True)

    # The below fields are the denormalized aggregate statistics for this model run.
    cached_numsites = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text='The number of distinct evaluations for this model run',
    )
    cached_score = models.FloatField(
        blank=True,
        null=True,
        help_text='The average score of all evaluations for this model run',
    )
    cached_timestamp = models.DateTimeField(
        blank=True,
        null=True,
        help_text='The timestamp of the most recent evaluation for this model run',
    )
    cached_timerange_min = models.DateTimeField(
        blank=True,
        null=True,
        help_text='The earliest timestamp of any evaluation for this model run',
    )
    cached_timerange_max = models.DateTimeField(
        blank=True,
        null=True,
        help_text='The latest timestamp of any evaluation for this model run',
    )
    cached_bbox = PolygonField(
        srid=4326,
        blank=True,
        null=True,
        help_text='The bounding box of all evaluations for this model run',
        spatial_index=False,
    )

    def __str__(self) -> str:
        return str(self.pk)

    def compute_aggregate_stats(self):
        """
        Compute denormalized aggregate stats and persist them on this model run.

        Many of the fields we report for each model run are expensive to compute, and need to be
        returned to the client often. Calling this will perform the expensive computations and
        persist the results on the model run for fast retrieval.

        This should be called whenever a model run is fully ingested, and again whenever any of the
        underlying data corresponding to the model changes such that these summary statistics might
        be affected.
        """
        stats = ModelRun.objects.filter(pk=self.pk).aggregate(
            cached_bbox=BoundingBoxPolygon('evaluations__geom'),
            cached_numsites=models.Count('evaluations__pk', distinct=True),
            cached_score=models.Avg('evaluations__score'),
            cached_timerange_min=models.Min('evaluations__start_date'),
            cached_timerange_max=models.Max('evaluations__end_date'),
            cached_timestamp=models.Max('evaluations__timestamp'),
        )
        self.cached_bbox = stats['cached_bbox']
        self.cached_numsites = stats['cached_numsites']
        self.cached_score = stats['cached_score']
        self.cached_timerange_min = stats['cached_timerange_min']
        self.cached_timerange_max = stats['cached_timerange_max']
        self.cached_timestamp = stats['cached_timestamp']

        self.save(
            update_fields=[
                'cached_bbox',
                'cached_numsites',
                'cached_score',
                'cached_timerange_min',
                'cached_timerange_max',
                'cached_timestamp',
            ]
        )

    @classmethod
    def compute_all_aggregate_stats(cls, recompute_all: bool = False):
        """
        Computes aggregate stats on all model runs that are missing them.

        If `recompute_all` is True, all model runs will have their aggregate stats recomputed
        regardless of whether they are already populated.
        """
        if recompute_all:
            qs = cls.objects.all()
        else:
            qs = cls.objects.filter(cached_numsites=None)

        # Unfortunately, Django ORM doesn't support joins in update queries, so doing this in a
        # single join query would require raw SQL that would be a pain to maintain.
        # Since this should only rarely run, we don't mind looping here.
        for model_run in qs.iterator(chunk_size=1000):
            model_run.compute_aggregate_stats()
