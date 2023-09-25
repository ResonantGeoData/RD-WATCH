from ninja.pagination import RouterPaginated

from django.http import HttpRequest

from rdwatch.models import Region

router = RouterPaginated()


@router.get('/', response=list[str])
def list_regions(request: HttpRequest):
    return Region.objects.values_list('name', flat=True)
