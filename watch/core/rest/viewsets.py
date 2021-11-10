from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rgd.rest.base import ModelViewSet, ReadOnlyModelViewSet

from .. import filters, models, serializers
from ..tasks import jobs


class RegionViewset(ModelViewSet):
    serializer_class = serializers.RegionSerializer
    # lookup_field = 'pk'
    queryset = models.Region.objects.all()


class GoogleCloudRecordViewset(ModelViewSet):
    serializer_class = serializers.GoogleCloudRecordSerializer
    # lookup_field = 'pk'
    queryset = models.GoogleCloudRecord.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GoogleCloudRecordFilter

    # @swagger_auto_schema(
    #     method='POST',
    #     operation_summary='Ingest records using search params.',
    # )
    # @action(detail=True)
    # def ingest(self, request):
    #     queryset = self.get_queryset()
    #     q = super().filter_queryset(queryset)
    #     # HACK: RESTful violation - creating records with a GET endpoint
    #     for record in q.all():
    #         jobs.task_load_google_cloud_record.delay(record.pk)
    #     return q
