from django.contrib.gis.db.models.aggregates import Collect
from django.contrib.postgres.aggregates import JSONBAgg
from django.db.models import Count, Max, Min
from django.db.models.functions import JSONObject  # type: ignore
from django.http import HttpRequest
from rest_framework.decorators import api_view, schema
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch.models import SiteEvaluation
from rdwatch.serializers import SiteEvaluationListSerializer


class SiteEvaluationsSchema(AutoSchema):
    def get_operation_id(self, *args):
        return "getSiteEvaluations"

    def get_serializer(self, *args):
        return SiteEvaluationListSerializer()

    def get_responses(self, *args, **kwargs):
        self.view.action = "retrieve"
        return super().get_responses(*args, **kwargs)


@api_view(["GET"])
@schema(SiteEvaluationsSchema())
def site_evaluations(request: HttpRequest):
    queryset = (
        SiteEvaluation.objects.order_by("-timestamp")
        .annotate(
            timemin=Min("observations__timestamp"),
            timemax=Max("observations__timestamp"),
        )
        .aggregate(
            count=Count("pk"),
            timerange=JSONObject(
                min=ExtractEpoch(Min("timemin")),
                max=ExtractEpoch(Max("timemax")),
            ),
            bbox=BoundingBox(Collect("geom")),
            results=JSONBAgg(
                JSONObject(
                    id="pk",
                    site=JSONObject(
                        region=JSONObject(
                            country="region__country",
                            classification="region__classification__slug",
                            number="region__number",
                        ),
                        number="number",
                    ),
                    configuration="configuration__parameters",
                    performer=JSONObject(
                        team_name="configuration__performer__description",
                        short_code="configuration__performer__slug",
                    ),
                    score="score",
                    bbox=BoundingBox("geom"),
                    timestamp=ExtractEpoch("timestamp"),
                    timerange=JSONObject(
                        min=ExtractEpoch("timemin"),
                        max=ExtractEpoch("timemax"),
                    ),
                )
            ),
        )
    )
    serializer = SiteEvaluationListSerializer(queryset)
    return Response(serializer.data)
