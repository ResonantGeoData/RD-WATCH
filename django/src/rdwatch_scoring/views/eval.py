from ninja.pagination import RouterPaginated

from django.db.models import CharField, Value
from django.db.models.functions import Concat
from django.http import HttpRequest

from rdwatch_scoring.models import EvaluationRun

router = RouterPaginated()


@router.get('/', response=list[str])
def list_evals(request: HttpRequest):
    return (
        EvaluationRun.objects.annotate(
            eval=Concat(
                'evaluation_number',
                Value('.'),
                'evaluation_run_number',
                output_field=CharField(),
            )
        )
        .order_by('-evaluation_number', '-evaluation_run_number')
        .values_list('eval', flat=True)
        .distinct()
    )
