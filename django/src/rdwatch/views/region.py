from ninja import Schema
from ninja.pagination import RouterPaginated

from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rdwatch.models import Region


class RegionSchema(Schema):
    id: int
    name: str


router = RouterPaginated()


@router.get('/', response=list[RegionSchema])
def list_regions(request: HttpRequest):
    return Region.objects.all()


@router.get('/{id}/', response=RegionSchema)
def get_performer(request: HttpRequest, id: int):
    return get_object_or_404(Region, id=id)
