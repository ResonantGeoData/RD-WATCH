import iso3166
from ninja import Schema
from ninja.pagination import RouterPaginated
from rdwatch_scoring.models import EvaluationRun

from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.models import Region


class RegionSchema(Schema):
    id: int
    name: str


router = RouterPaginated()


@router.get('/', response=list[RegionSchema])
def list_regions(request: HttpRequest):
    unique_regions = EvaluationRun.objects.order_by().values_list('region', flat=True).distinct()

    region_list = [
        {
            'id': idx + 1,
            'name': region
        }
        for idx, region in enumerate(unique_regions)
    ]

    return region_list

