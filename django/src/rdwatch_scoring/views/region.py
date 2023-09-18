from ninja import Schema
from ninja.pagination import RouterPaginated

from django.http import HttpRequest

from rdwatch_scoring.models import EvaluationRun


class RegionSchema(Schema):
    id: int
    name: str


router = RouterPaginated()


@router.get('/', response=list[RegionSchema])
def list_regions(request: HttpRequest):
    unique_regions = (
        EvaluationRun.objects.order_by().values_list('region', flat=True).distinct()
    )

    region_list = [
        {'id': idx + 1, 'name': region} for idx, region in enumerate(unique_regions)
    ]

    return region_list
