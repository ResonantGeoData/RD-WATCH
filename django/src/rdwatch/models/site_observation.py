from django.contrib.gis.db.models import MultiPolygonField
from django.contrib.postgres.indexes import GistIndex
from django.db import models


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

    class Meta:
        default_related_name = 'observations'
        indexes = [GistIndex(fields=['timestamp']), GistIndex(fields=['score'])]
