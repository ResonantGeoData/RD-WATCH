from ninja import Router
from ninja.pagination import PageNumberPagination, paginate

from django.http import HttpRequest

from rdwatch.scoring.models import EvaluationRun

router = Router()


@router.get('/', response=list[str])
@paginate(PageNumberPagination, page_size=1000)
def list_regions(request: HttpRequest):
    return EvaluationRun.objects.order_by().values_list('region', flat=True).distinct()


@router.get('/details/', response=list[dict])
@paginate(PageNumberPagination, page_size=1000)
def list_region_details(request: HttpRequest):
    regions = (
        EvaluationRun.objects.order_by().values_list('region', flat=True).distinct()
    )
    return [
        {
            'name': region,
            'owner': 'None',
            'value': region,
            'public': True,
            'id': -1,
            'hasGeom': True,
        }
        for region in regions
    ]
