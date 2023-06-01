import iso3166
from ninja import Schema
from ninja.pagination import RouterPaginated

from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.models import Region


class RegionSchema(Schema):
    id: int
    name: str

    @staticmethod
    def resolve_name(obj: Region) -> str:
        country = obj.country
        classification: str = obj.classification.slug
        number = obj.number

        country_numeric = str(country).zfill(3)
        country_code = iso3166.countries_by_numeric[country_numeric].alpha2
        region_number = 'xxx' if number is None else str(number).zfill(3)
        return f'{country_code}_{classification}{region_number}'


router = RouterPaginated()


@router.get('/', response=list[RegionSchema])
def list_regions(request: HttpRequest):
    return Region.objects.all().select_related('classification')


@router.get('/{id}', response=RegionSchema)
def get_performer(request: HttpRequest, id: int):
    return get_object_or_404(
        Region.objects.all().select_related('classification'), id=id
    )
