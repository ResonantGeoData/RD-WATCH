from datetime import datetime

from typing_extensions import Self

from django.contrib.gis.db.models import MultiPolygonField
from django.contrib.postgres.indexes import GistIndex
from django.db import models

from rdwatch.models import SiteEvaluation, lookups
from rdwatch.schemas import SiteModel


class SiteObservation(models.Model):
    siteeval = models.ForeignKey(
        to='SiteEvaluation',
        on_delete=models.CASCADE,
        help_text='The site evaluation associated with this observation.',
        db_index=True,
    )
    label = models.ForeignKey(
        to='ObservationLabel',
        on_delete=models.PROTECT,
        help_text='Site observation classification label',
        db_index=True,
    )
    score = models.FloatField(
        help_text='Evaluation accuracy',
    )
    geom = MultiPolygonField(
        help_text='Footprint of site observation',
        srid=3857,
        spatial_index=True,
    )
    constellation = models.ForeignKey(
        to='Constellation',
        on_delete=models.PROTECT,
        help_text="The source image's satellite constellation",
        null=True,
        db_index=True,
    )
    spectrum = models.ForeignKey(
        to='CommonBand',
        on_delete=models.PROTECT,
        help_text="The source image's satellite spectrum",
        null=True,
        db_index=True,
    )
    timestamp = models.DateTimeField(
        help_text="The source image's timestamp",
    )

    def __str__(self):
        sit = str(self.siteeval)
        lbl = str(self.label).upper()
        tim = self.timestamp.isoformat()
        return f'{sit}[{lbl}@{tim}]'

    @classmethod
    def bulk_create_from_site_evaluation(
        cls, site_eval: SiteEvaluation, site_model: SiteModel
    ) -> list[Self]:
        site_observations: list[SiteObservation] = []

        label_set: set[str] = {
            '_'.join(feature.properties.current_phase.lower().split(' '))
            for feature in site_model.observation_features
        }
        labels_query = lookups.ObservationLabel.objects.filter(slug__in=label_set)
        label_map = {
            ' '.join(label.slug.split('_')).title(): label for label in labels_query
        }

        constellation_set: set[str] = {
            feature.properties.sensor_name
            for feature in site_model.observation_features
            if feature.properties.sensor_name
        }

        constellations_query = lookups.Constellation.objects.filter(
            description__in=constellation_set
        )
        constellation_map = {
            constellation.description: constellation
            for constellation in constellations_query
        }

        for feature in site_model.observation_features:
            if not feature.properties.observation_date:
                continue

            label = label_map[feature.properties.current_phase]
            constellation = constellation_map.get(feature.properties.sensor_name, None)
            observation_date = datetime.strptime(
                feature.properties.observation_date,
                '%Y-%m-%d',
            )

            site_observations.append(
                cls(
                    siteeval=site_eval,
                    label=label,
                    score=feature.properties.score,
                    geom=feature.geometry,
                    constellation=constellation,
                    spectrum=None,
                    timestamp=observation_date,
                )
            )

        return SiteObservation.objects.bulk_create(site_observations)

    class Meta:
        default_related_name = 'observations'
        indexes = [GistIndex(fields=['timestamp']), GistIndex(fields=['score'])]
