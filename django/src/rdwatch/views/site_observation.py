from datetime import datetime

from django.contrib.gis.db.models.aggregates import Collect
from django.contrib.postgres.aggregates import JSONBAgg
from django.db import transaction
from django.db.models import Count, F, Max, Min, RowRange, Window
from django.db.models.functions import JSONObject  # type: ignore
from django.http import HttpRequest
from rest_framework import status
from rest_framework.decorators import api_view, schema
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema

from rdwatch.db.functions import BoundingBox, ExtractEpoch
from rdwatch.models import SatelliteFetching, SiteEvaluation, SiteImage, SiteObservation
from rdwatch.serializers import SiteImageListSerializer, SiteObservationListSerializer
from rdwatch.tasks import get_siteobservations_images


class SiteObservationsSchema(AutoSchema):
    def get_operation_id(self, *args):
        return 'getSiteObservations'

    def get_serializer(self, *args):
        return SiteObservationListSerializer()

    def get_responses(self, *args, **kwargs):
        self.view.action = 'retrieve'
        return super().get_responses(*args, **kwargs)


@api_view(['GET'])
@schema(SiteObservationsSchema())
def site_observations(request: HttpRequest, pk: int):
    if not SiteEvaluation.objects.filter(pk=pk).exists():
        raise NotFound()
    queryset = (
        SiteObservation.objects.order_by('timestamp')
        .filter(siteeval__id=pk)
        .annotate(
            timemin=F('timestamp'),
            timemax=Window(
                expression=Max('timestamp'),
                partition_by=[F('siteeval')],
                frame=RowRange(start=0, end=1),
                order_by='timestamp',  # type: ignore
            ),
        )
        .aggregate(
            count=Count('pk'),
            timerange=JSONObject(
                min=ExtractEpoch(Min('timestamp')),
                max=ExtractEpoch(Max('timestamp')),
            ),
            bbox=BoundingBox(Collect('geom')),
            results=JSONBAgg(
                JSONObject(
                    id='pk',
                    label='label__slug',
                    score='score',
                    constellation='constellation__slug',
                    spectrum='spectrum__slug',
                    timestamp=ExtractEpoch('timestamp'),
                    timerange=JSONObject(
                        min=ExtractEpoch('timemin'),
                        max=ExtractEpoch('timemax'),
                    ),
                    bbox=BoundingBox('geom'),
                )
            ),
        )
    )
    image_queryset = (
        SiteImage.objects.filter(siteeval__id=pk)
        .order_by('timestamp')
        .aggregate(
            count=Count('pk'),
            results=JSONBAgg(
                JSONObject(
                    id='pk',
                    timestamp=ExtractEpoch('timestamp'),
                    image='image',
                    cloudcover='cloudcover',
                    percent_black='percent_black',
                    source='source',
                    siteobs_id='siteobs_id',
                )
            ),
        )
    )

    image_serializer = SiteImageListSerializer(image_queryset)
    serializer = SiteObservationListSerializer(queryset)
    output = serializer.data
    output['images'] = image_serializer.data
    if SatelliteFetching.objects.filter(siteeval=pk).exists():
        retrieved = SatelliteFetching.objects.filter(siteeval=pk).first()
        output['job'] = {
            'status': retrieved.status,
            'error': retrieved.error,
            'timestamp': retrieved.timestamp.timestamp(),
        }
    return Response(output)


@api_view(['POST'])
def get_site_observation_images(request: HttpRequest, pk: int):
    if 'constellation' not in request.GET:
        constellation = 'WV'
    else:
        constellation = request.GET['constellation']

    # Make sure site evaluation actually exists
    siteeval = get_object_or_404(SiteEvaluation, pk=pk)

    with transaction.atomic():
        # Use select_for_update here to lock the SatelliteFetching row
        # for the duration of this transaction in order to ensure its
        # status doesn't change out from under us
        fetching_task = (
            SatelliteFetching.objects.select_for_update()
            .filter(siteeval=siteeval)
            .first()
        )
        if fetching_task is not None:
            # If the task already exists and is running, return a 409 and do not
            # start another one.
            if fetching_task.status == SatelliteFetching.Status.RUNNING:
                return Response(
                    'Image generation already in progress.',
                    status=status.HTTP_409_CONFLICT,
                )
            # Otherwise, if the task exists but is *not* running, set the status
            # to running and kick off the task
            fetching_task.status = SatelliteFetching.Status.RUNNING
            fetching_task.save()
        else:
            fetching_task = SatelliteFetching.objects.create(
                siteeval=siteeval,
                timestamp=datetime.now(),
                status=SatelliteFetching.Status.RUNNING,
            )
        get_siteobservations_images.delay(pk, constellation)
    return Response(status=202)
