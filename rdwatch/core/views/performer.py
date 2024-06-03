from ninja import Schema
from ninja.pagination import RouterPaginated

from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.core.models import Performer


class PerformerSchema(Schema):
    id: int
    team_name: str
    short_code: str


class PerformerCreateSchema(Schema):
    team_name: str
    short_code: str


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


@router.post('/', response={201: PerformerSchema, 409: str})
def create_performer(request: HttpRequest, payload: PerformerCreateSchema):
    if Performer.objects.filter(
        Q(team_name=payload.team_name) | Q(short_code=payload.short_code)
    ).exists():
        return 409, 'Performer already exists'

    return 201, Performer.objects.create(**payload.dict())
