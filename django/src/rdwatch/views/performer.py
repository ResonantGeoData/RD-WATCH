from ninja import Field, Schema
from ninja.pagination import RouterPaginated

from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.models.lookups import Performer


class PerformerSchema(Schema):
    id: int
    team_name: str = Field(alias='description')
    short_code: str = Field(alias='slug')


router = RouterPaginated()


@router.get('/', response=list[PerformerSchema])
def list_performers(request: HttpRequest):
    return Performer.objects.all()


@router.get('/{id}/', response=PerformerSchema)
def get_performer(request: HttpRequest, id: int):
    return get_object_or_404(
        Performer.objects.all(),
        id=id,
    )
