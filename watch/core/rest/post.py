import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import CreateAPIView, ListAPIView

from .. import filters, models, serializers
from ..tasks import jobs

logger = logging.getLogger(__name__)


class CreateRegion(CreateAPIView):
    queryset = models.Region.objects.all()
    serializer_class = serializers.RegionSerializer


class SearchCreateGoogleCloudRecord(ListAPIView):
    queryset = models.GoogleCloudRecord.objects.all()
    serializer_class = serializers.GoogleCloudRecordSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GoogleCloudRecordFilter

    def filter_queryset(self, queryset):
        q = super().filter_queryset(queryset)
        # HACK: RESTful violation - creating records with a GET endpoint
        for record in q.all():
            jobs.task_load_google_cloud_record.delay(record.pk)
        return q
