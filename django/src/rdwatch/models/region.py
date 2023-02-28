import iso3166

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from rest_framework.exceptions import ValidationError

from rdwatch.models import lookups
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


def get_or_create_region(region_id: str) -> tuple[Region, bool]:
    countrystr, numstr = region_id.split('_')
    contrynum = iso3166.countries_by_alpha2[countrystr].numeric

    try:
        region_classification = lookups.RegionClassification.objects.get(slug=numstr[0])
    except ObjectDoesNotExist:
        raise ValidationError(f'invalid region classification {numstr[0]}')

    return Region.objects.get_or_create(
        country=int(contrynum),
        classification=region_classification,
        number=None if numstr[1:] == 'xxx' else int(numstr[1:]),
    )
