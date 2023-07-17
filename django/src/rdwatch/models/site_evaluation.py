from datetime import datetime

from typing_extensions import Self

from django.contrib.gis.db.models import PolygonField
from django.contrib.gis.geos import MultiPolygon
from django.contrib.postgres.indexes import GistIndex
from django.db import models, transaction

from rdwatch.models import HyperParameters, lookups
from rdwatch.models.region import get_or_create_region
from rdwatch.schemas import RegionModel, SiteModel
from rdwatch.schemas.region_model import RegionFeature, SiteSummaryFeature
from rdwatch.schemas.site_model import SiteFeature


class SiteEvaluation(models.Model):
    configuration = models.ForeignKey(
        to='HyperParameters',
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
    number = models.PositiveSmallIntegerField(
        help_text='The site number',
        db_index=True,
    )
    timestamp = models.DateTimeField(
        help_text='Time when this evaluation was finished',
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

    @classmethod
    def bulk_create_from_site_model(
        cls, site_model: SiteModel, configuration: HyperParameters
    ):
        from rdwatch.models import SiteObservation

        site_feature = site_model.site_feature
        assert isinstance(site_feature.properties, SiteFeature)
        with transaction.atomic():
            region = get_or_create_region(site_feature.properties.region_id)[0]
            label = lookups.ObservationLabel.objects.get(
                slug=site_feature.properties.status
            )
            site_eval = cls.objects.create(
                configuration=configuration,
                region=region,
                version=site_feature.properties.version,
                number=site_feature.properties.site_number,
                timestamp=datetime.now(),
                geom=site_feature.geometry,
                label=label,
                score=site_feature.properties.score,
            )

            SiteObservation.bulk_create_from_site_evaluation(site_eval, site_model)

        return site_eval

    @classmethod
    def bulk_create_from_from_region_model(
        cls, region_model: RegionModel, configuration: HyperParameters
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
                region_feature.properties.region_id, region_feature.geometry
            )[0]

            for feature in region_model.site_summary_features:
                assert isinstance(feature.properties, SiteSummaryFeature)

                geometry = feature.geometry
                if isinstance(geometry, MultiPolygon):
                    geometry = geometry.convex_hull

                site_eval = cls(
                    configuration=configuration,
                    region=region,
                    number=feature.properties.site_number,
                    timestamp=datetime.now(),
                    geom=geometry,
                    label=label_map[feature.properties.status],
                    score=feature.properties.score,
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
        constraints = [
            models.UniqueConstraint(
                name='unique_siteeval',
                fields=[
                    'configuration',
                    'region',
                    'number',
                ],
                violation_error_message=(  # type: ignore
                    'Site evaluation already exists.'
                ),
            ),
        ]
