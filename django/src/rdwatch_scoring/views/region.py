from ninja.pagination import RouterPaginated

from django.http import HttpRequest

from rdwatch_scoring.models import EvaluationRun

router = RouterPaginated()


@router.get('/', response=list[str])
def list_regions(request: HttpRequest):
    return EvaluationRun.objects.order_by().values_list('region', flat=True).distinct()
