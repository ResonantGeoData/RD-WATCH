import iso3166

from django.contrib.gis.geos import Polygon
from django.core.exceptions import ValidationError


def validate_iso3166(value: int):
    if str(value).zfill(3) not in iso3166.countries_by_numeric:
        raise ValidationError("Invalid country code")


def validate_bbox(value: Polygon):
    if value.num_coords != 4:
        raise ValidationError("Must have exactly four coordinates")
