from django.shortcuts import render

# Create your views here.
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Schema
from ninja.pagination import RouterPaginated
import logging

from .models import Observation
logger = logging.getLogger(__name__)


class ScoreObservationSchema(Schema):
    uuid: str = None
    name: str = None
    source: str = None
    sensor: str = None
    phase: str = None
    score: str = None

router = RouterPaginated()


@router.get('/', response=list[ScoreObservationSchema])
def list_regions(request: HttpRequest):

    objects = Observation.objects.all()
    logger.warning(objects)
    return objects