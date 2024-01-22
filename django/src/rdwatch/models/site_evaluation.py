from datetime import datetime
from typing import Self
from uuid import uuid4

from django_extensions.db.models import CreationDateTimeField

from django.contrib.gis.db.models import PolygonField
from django.contrib.gis.geos import MultiPolygon
from django.contrib.postgres.indexes import GistIndex
from django.db import models, transaction

from rdwatch.models import ModelRun, lookups
from rdwatch.models.region import get_or_create_region
from rdwatch.schemas import RegionModel, SiteModel
from rdwatch.schemas.region_model import RegionFeature, SiteSummaryFeature
from rdwatch.schemas.site_model import SiteFeature


class SiteEvaluation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    timestamp = CreationDateTimeField()
    # This is not an auto-field, and is used for cache invalidation.
    # it must be manually set when SiteEvaluation is edited
    modified_timestamp = models.DateTimeField(
        help_text='Timestamp of the last modification',
    )
    configuration = models.ForeignKey(
        to='ModelRun',
        on_delete=models.PROTECT,
        help_text='The hyper parameters used this site evaluation.',
        db_index=True,
    )
    region = models.ForeignKey(
        to='Region',
        on_delete=models.PROTECT,
        help_text='The region this site belongs to',
        db_index=True,
    )
    number = models.IntegerField(help_text='The site number', db_index=True)
    start_date = models.DateTimeField(
        help_text='Start date in geoJSON',
        null=True,
    )
    end_date = models.DateTimeField(
        help_text='end date in geoJSON',
        null=True,
    )
    geom = PolygonField(
        help_text="Polygon from this site's Site Feature",
        srid=3857,
        spatial_index=True,
    )
    label = models.ForeignKey(
        to='ObservationLabel',
        on_delete=models.PROTECT,
        help_text='Site feature classification label',
        db_index=True,
    )
    score = models.FloatField(
        help_text='Score of site footprint',
    )
    version = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Version of annotations',
    )
    notes = models.TextField(null=True, blank=True)

    validated = models.BooleanField(blank=True, null=True)

    class Status(models.TextChoices):
        PROPOSAL = (
            'PROPOSAL'  # proposal is a proposal awaiting Adjudication/Confirmation
        )
        APPROVED = 'APPROVED'  # proposal is approved and merged into ground truth
        REJECTED = 'REJECTED'  # proposal is rejected

    status = models.CharField(
        max_length=255,  # If we need future states
        blank=True,
        null=True,
        help_text='Fetching Status',
        choices=Status.choices,
    )
    cache_originator_file = models.CharField(
        max_length=2048,
        blank=True,
        null=True,
        help_text='Name of source file for proposals',
    )
    cache_timestamp = models.DateTimeField(
        help_text='Cache timestamp for proposals',
        null=True,
    )
    cache_commit_hash = models.CharField(
        max_length=2048,
        blank=True,
        null=True,
        help_text='Hash of the file for proposals',
    )

    @classmethod
    def bulk_create_from_site_model(
        cls, site_model: SiteModel, configuration: ModelRun
    ):
        from rdwatch.models import SiteObservation

        site_feature = site_model.site_feature
        assert isinstance(site_feature.properties, SiteFeature)
        status = None
        modified = False
        if (
            configuration.ground_truth is False
            and site_feature.properties.validated
            and site_feature.properties.originator in ('te', 'iMERIT')
        ):
            configuration.ground_truth = True
            modified = True
        # If a Site has a number of 9999 it is a proposal
        # https://smartgitlab.com/TE/annotations/-/wikis/Submitting-Proposals-for-New-Sites
        if configuration.proposal or site_feature.properties.site_number == 9999:
            status = SiteEvaluation.Status.PROPOSAL
            configuration.proposal = ModelRun.ProposalStatus.PROPOSAL
            modified = True
        if modified:
            configuration.save()
        with transaction.atomic():
            region = get_or_create_region(site_feature.properties.region_id)[0]
            label = lookups.ObservationLabel.objects.get(
                slug=site_feature.properties.status
            )
            cache_originator_file = None
            cache_timestamp = None
            cache_commit_hash = None
            if site_feature.properties.cache:
                cache_originator_file = site_feature.properties.cache.originator_file
                cache_timestamp = site_feature.properties.cache.timestamp
                cache_commit_hash = site_feature.properties.cache.commit_hash

            site_eval = cls.objects.create(
                configuration=configuration,
                region=region,
                version=site_feature.properties.version,
                number=site_feature.properties.site_number,
                start_date=site_feature.properties.start_date,
                end_date=site_feature.properties.end_date,
                geom=site_feature.parsed_geometry,
                label=label,
                score=site_feature.properties.score,
                status=status,
                validated=site_feature.properties.validated,
                cache_originator_file=cache_originator_file,
                cache_timestamp=cache_timestamp,
                cache_commit_hash=cache_commit_hash,
                modified_timestamp=datetime.now(),
            )

            SiteObservation.bulk_create_from_site_evaluation(site_eval, site_model)

        return site_eval

    @classmethod
    def bulk_create_from_region_model(
        cls, region_model: RegionModel, configuration: ModelRun
    ) -> list[Self]:
        region_feature = region_model.region_feature
        assert isinstance(region_feature.properties, RegionFeature)

        label_set: set[str] = {
            '_'.join(feature.properties.status.lower().split(' '))
            for feature in region_model.site_summary_features
        }
        label_set.add('unknown')

        labels_query = lookups.ObservationLabel.objects.filter(slug__in=label_set)
        label_map = {label.slug: label for label in labels_query}

        site_evals: list[SiteEvaluation] = []
        with transaction.atomic():
            region = get_or_create_region(
                region_feature.properties.region_id, region_feature.parsed_geometry
            )[0]

            for feature in region_model.site_summary_features:
                assert isinstance(feature.properties, SiteSummaryFeature)

                geometry = feature.parsed_geometry
                if isinstance(geometry, MultiPolygon):
                    geometry = geometry.convex_hull

                site_eval = cls(
                    configuration=configuration,
                    region=region,
                    number=feature.properties.site_number,
                    geom=geometry,
                    label=label_map[feature.properties.status],
                    score=feature.properties.score,
                    modified_timestamp=datetime.now(),
                )
                site_evals.append(site_eval)

            created = cls.objects.bulk_create(site_evals)

        return created

    @property
    def site_id(self):
        return f'{self.region}_{str(self.number).zfill(4)}'

    def __str__(self):
        prf = str(self.configuration.performer)
        tim = self.timestamp.isoformat()
        return f'{self.site_id}.{prf}@{tim}'

    class Meta:
        default_related_name = 'evaluations'
        indexes = [GistIndex(fields=['timestamp']), GistIndex(fields=['score'])]


class SiteEvaluationTracking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    edited = models.DateTimeField()
    evaluation = models.ForeignKey(
        to='SiteEvaluation',
        on_delete=models.CASCADE,
        db_index=True,
    )
    start_date = models.DateTimeField(
        help_text='Start date in geoJSON',
        null=True,
    )
    end_date = models.DateTimeField(
        help_text='end date in geoJSON',
        null=True,
    )
    label = models.ForeignKey(
        to='ObservationLabel',
        on_delete=models.PROTECT,
        help_text='Site feature classification label',
        db_index=True,
    )
    score = models.FloatField(
        help_text='Score of site footprint',
    )
    notes = models.TextField(null=True, blank=True)
