import iso3166
from ninja.errors import ValidationError

from django.contrib.gis.db.models import PolygonField
from django.contrib.gis.geos import Polygon
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction

from rdwatch_scoring.models import lookups
from rdwatch.validators import validate_iso3166


class Region(models.Model):
    country = models.PositiveSmallIntegerField(
        help_text='The numeric country identifier as specified by ISO 3166',
        db_index=True,
        validators=[validate_iso3166],
    )
    classification = models.ForeignKey(
        to='RegionClassification',
        on_delete=models.PROTECT,
        help_text='Region classification code',
        db_index=True,
    )
    number = models.PositiveSmallIntegerField(
        help_text='The region number',
        null=True,
        db_index=True,
    )
    geom = PolygonField(
        help_text='Polygon from the associated Region Feature',
        srid=3857,
        spatial_index=True,
        null=True,
        blank=True,
    )

    def __str__(self):
        cty = iso3166.countries_by_numeric[str(self.country).zfill(3)].alpha2
        rcls = self.classification.slug
        num = str(self.number).zfill(3)
        return f'{cty}_{rcls}{num}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='uniq_region',
                fields=[
                    'country',
                    'classification',
                    'number',
                ],
                violation_error_message='Region already exists.',  # type: ignore
            ),
        ]


def get_or_create_region(
    region_id: str,
    region_polygon: Polygon | None = None,
) -> tuple[Region, bool]:
    countrystr, numstr = region_id.split('_')
    contrynum = iso3166.countries_by_alpha2[countrystr].numeric

    try:
        region_classification = lookups.RegionClassification.objects.get(slug=numstr[0])
    except ObjectDoesNotExist:
        raise ValidationError(f'invalid region classification {numstr[0]}')

    with transaction.atomic():
        region, created = Region.objects.select_for_update().get_or_create(
            country=int(contrynum),
            classification=region_classification,
            number=None if numstr[1:] == 'xxx' else int(numstr[1:]),
        )
        if region.geom is None and region_polygon is not None:
            region.geom = region_polygon
            region.save()
        return region, created
