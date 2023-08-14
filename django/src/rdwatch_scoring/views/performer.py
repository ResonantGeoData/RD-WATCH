from ninja import Schema
from ninja.pagination import RouterPaginated

from django.db.models import F
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.models.lookups import Performer
from rdwatch_scoring.models import EvaluationRun

class PerformerSchema(Schema):
    id: int
    team_name: str
    short_code: str


router = RouterPaginated()


@router.get('/', response=list[PerformerSchema])
def list_performers(request: HttpRequest):
    unique_performers = EvaluationRun.objects.order_by().values_list('performer', flat=True).distinct()
    performers_list = [
        {
            'id': idx + 1,
            'team_name': performer,
            'short_code': performer.lower().replace(' ', '_')
        }
        for idx, performer in enumerate(unique_performers)
    ]
    return performers_list

