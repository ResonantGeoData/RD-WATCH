from ninja import Schema
from ninja.pagination import RouterPaginated

from django.db.models import F
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.models import Performer


class PerformerSchema(Schema):
    id: int
    team_name: str
    short_code: str


router = RouterPaginated()


@router.get('/', response=list[PerformerSchema])
def list_performers(request: HttpRequest):
    return Performer.objects.defer('description', 'slug').annotate(
        team_name=F('description'),
        short_code=F('slug'),
    )


@router.get('/{id}/', response=PerformerSchema)
def get_performer(request: HttpRequest, id: int):
    return get_object_or_404(
        Performer.objects.defer('description', 'slug').annotate(
            team_name=F('description'),
            short_code=F('slug'),
        ),
        id=id,
    )
