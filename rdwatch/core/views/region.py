from ninja import Router
from ninja.pagination import PageNumberPagination, paginate

from django.http import HttpRequest

from rdwatch.models import Region

router = Router()


@router.get('/', response=list[str])
@paginate(PageNumberPagination, page_size=1000)
def list_regions(request: HttpRequest):
    return Region.objects.values_list('name', flat=True)
