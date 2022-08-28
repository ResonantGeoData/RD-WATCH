from typing import Optional

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rdwatch.db.functions import VectorTile
from rdwatch.models import SiteObservation
from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView


class SiteObservationTileSchema(AutoSchema):
    def get_operation_id(self, *args):
        return "getSiteObservationTile"

    def get_responses(self, *args):
        return {
            "200": {
                "content": "application/x-protobuf",
                "description": "The Map Vector Tile",
            },
            "204": {
                "content": "application/x-protobuf",
                "description": "An empty Map Vector Tile",
            },
        }


class RetrieveSiteObservationTile(APIView):

    permission_classes = [permissions.AllowAny]
    schema = SiteObservationTileSchema()
    action = "retrieve"

    @method_decorator(cache_page(60 * 60 * 24 * 365))
    def get(
        self,
        *args,
        pk: Optional[int] = None,
        z: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ):
        if pk is None or z is None or x is None or y is None:
            raise TypeError()
        if not SiteObservation.objects.filter(pk=pk).exists():
            raise NotFound()
        agg = SiteObservation.objects.filter(pk=pk).aggregate(
            tile=VectorTile("geometry", z, x, y)
        )
        data = agg["tile"]
        status = 200 if data else 204
        return HttpResponse(
            data,
            content_type="application/octet-stream",
            status=status,
        )
