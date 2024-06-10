from ninja import Router
from ninja.pagination import PageNumberPagination, paginate

from django.http import HttpRequest

from rdwatch.core.models import Region

router = Router()


@router.get('/', response=list[str])
@paginate(PageNumberPagination, page_size=1000)
def list_regions(request: HttpRequest):
    return Region.objects.values_list('name', flat=True)


@router.get('/details', response=list[dict])
@paginate(PageNumberPagination, page_size=1000)
def list_region_details(request: HttpRequest):
    regions = Region.objects.values_list('name', 'owner__username', 'public')
    return [
        {
            'name': region[0],
            'owner': region[1] if region[1] is not None else 'None',
            'public': region[2],
        }
        for region in regions
    ]
