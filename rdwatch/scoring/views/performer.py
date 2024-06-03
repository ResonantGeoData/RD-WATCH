from ninja.pagination import RouterPaginated

from django.http import HttpRequest

from rdwatch.core.views.performer import PerformerSchema
from rdwatch.scoring.models import EvaluationRun

router = RouterPaginated()


@router.get('/', response=list[PerformerSchema])
def list_performers(request: HttpRequest):
    unique_performers = (
        EvaluationRun.objects.order_by().values_list('performer', flat=True).distinct()
    )
    performers_list = [
        {
            'id': idx + 1,
            'team_name': performer,
            'short_code': performer.lower().replace(' ', '_'),
        }
        for idx, performer in enumerate(unique_performers)
    ]
    return performers_list
