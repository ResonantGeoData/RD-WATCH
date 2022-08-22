from typing import Optional

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rdwatch.db.functions import RasterTile
from rdwatch.models import Saliency, SaliencyTile
from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView


class SaliencyTileSchema(AutoSchema):
    def get_operation_id(self, *args):
        return "getSaliencyTile"

    def get_responses(self, *args):
        return {
            "200": {
                "content": "image/png",
                "description": "The raster tile",
            },
        }


class RetrieveSaliencyTile(APIView):

    permission_classes = [permissions.AllowAny]
    schema = SaliencyTileSchema()
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
        if not Saliency.objects.filter(pk=pk).exists():
            raise NotFound()
        agg = SaliencyTile.objects.filter(saliency=pk).aggregate(
            tile=RasterTile("raster", z, x, y)
        )
        data = agg["tile"]
        return HttpResponse(data, content_type="image/png", status=200)
