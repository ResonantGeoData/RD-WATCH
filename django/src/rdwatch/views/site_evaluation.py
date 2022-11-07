import django_filters

from django.contrib.gis.db.models.aggregates import Collect
from django.contrib.postgres.aggregates import JSONBAgg
from django.core.paginator import Paginator
from django.db.models import Count, Max, Min
from django.db.models.functions import JSONObject  # type: ignore
from django.http import HttpRequest
from rest_framework.decorators import api_view, schema
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.settings import api_settings

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch.models import SiteEvaluation
from rdwatch.serializers import SiteEvaluationListSerializer


class SiteEvaluationsFilter(django_filters.FilterSet):
    timestamp = django_filters.DateTimeFromToRangeFilter()

    class Meta:
        model = SiteEvaluation
        fields = ["timestamp"]


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
    queryset = SiteEvaluationsFilter(
        request.GET,
        queryset=SiteEvaluation.objects.order_by("-timestamp"),
    ).qs

    # Overview
    overview = queryset.annotate(
        timemin=Min("observations__timestamp"),
        timemax=Max("observations__timestamp"),
    ).aggregate(
        count=Count("pk"),
        timerange=JSONObject(
            min=ExtractEpoch(Min("timemin")),
            max=ExtractEpoch(Max("timemax")),
        ),
        bbox=BoundingBox(Collect("geom")),
    )

    # Pagination
    assert api_settings.PAGE_SIZE, "PAGE_SIZE must be set."
    paginator = Paginator(queryset, api_settings.PAGE_SIZE)
    page = paginator.page(request.GET.get("page", 1))

    if page.has_next():
        next_page_query_params = request.GET.copy()
        next_page_query_params["page"] = str(page.next_page_number())
        overview[
            "next"
        ] = f"{request.get_full_path()}?{next_page_query_params.urlencode()}"
    else:
        overview["next"] = None

    if page.has_previous():
        prev_page_query_params = request.GET.copy()
        prev_page_query_params["page"] = str(page.previous_page_number())
        overview[
            "previous"
        ] = f"{request.get_full_path()}?{prev_page_query_params.urlencode()}"
    else:
        overview["previous"] = None

    # Results
    results = page.object_list.annotate(  # type: ignore
        timemin=Min("observations__timestamp"),
        timemax=Max("observations__timestamp"),
    ).aggregate(
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

    serializer = SiteEvaluationListSerializer(overview | results)
    return Response(serializer.data)
