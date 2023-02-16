from django.contrib.gis.db.models import PolygonField
from django.contrib.postgres.indexes import GistIndex
from django.db import models


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
        help_text='Footprint of site',
        srid=3857,
        spatial_index=True,
    )
    score = models.FloatField(
        help_text='Score of site footprint',
    )

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
