import iso3166
from ninja.errors import ValidationError

from django.contrib.gis.db.models import PolygonField
from django.contrib.gis.geos import Polygon
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction

from rdwatch_scoring.models import lookups
from rdwatch.validators import validate_iso3166


class Region(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    crs = models.CharField(max_length=255, blank=True, null=True)
    mgrs = models.CharField(max_length=255, blank=True, null=True)
    geom = models.TextField(blank=True, null=True)
    area = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        app_label = 'rdwatch_scoring'
        db_table = 'region'

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
