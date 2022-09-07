from django.contrib.gis.db.models.aggregates import Collect
from django.contrib.gis.db.models.functions import Envelope, Transform
from django.http import HttpRequest
from django.views.decorators.cache import cache_page
from rdwatch.models import SiteEvaluation, SiteObservation
from rdwatch.serializers import SiteEvaluationSerializer, SiteObservationSerializer
from rest_framework.decorators import api_view, schema
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema


class SiteEvaluationsSchema(AutoSchema):
    def get_operation_id(self, *args):
        return "getSiteEvaluations"

    def get_serializer(self, *args):
        return SiteEvaluationSerializer()


class SiteObservationsSchema(AutoSchema):
    def get_operation_id(self, *args):
        return "getSiteObservations"

    def get_serializer(self, *args):
        return SiteObservationSerializer()

    def get_responses(self, *args, **kwargs):
        self.view.action = "list"
        return super().get_responses(*args, **kwargs)


@api_view(["GET"])
@schema(SiteEvaluationsSchema())
def site_evaluations(request: HttpRequest):
    queryset = (
        SiteEvaluation.objects.select_related(
            "configuration",
            "configuration__performer",
            "region",
            "region__classification",
        )
        .defer("geom")
        .annotate(bbox=Transform(Envelope(Collect("observations__geom")), 4326))
    ).order_by("timestamp")
    serializer = SiteEvaluationSerializer(queryset, many=True)
    return Response(serializer.data)


@cache_page(60 * 60 * 24 * 365)
@api_view(["GET"])
@schema(SiteObservationsSchema())
def site_observations(request: HttpRequest, pk: int | None = None):
    if pk is None:
        raise ValueError()
    queryset = (
        SiteObservation.objects.select_related(
            "label",
            "constellation",
            "spectrum",
        )
        .filter(siteeval=pk)
        .defer("geom")
    ).order_by("timestamp")
    serializer = SiteObservationSerializer(queryset, many=True)
    return Response(serializer.data)
