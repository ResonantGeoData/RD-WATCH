from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView, RetrieveAPIView

from .. import filters, models, serializers


class GetRegion(RetrieveAPIView):
    serializer_class = serializers.RegionSerializer
    lookup_field = 'pk'
    queryset = models.Region.objects.all()


class GetGoogleCloudRecord(RetrieveAPIView):
    serializer_class = serializers.GoogleCloudRecordSerializer
    lookup_field = 'pk'
    queryset = models.GoogleCloudRecord.objects.all()


class SearchGoogleCloudRecord(ListAPIView):
    queryset = models.GoogleCloudRecord.objects.all()
    serializer_class = serializers.GoogleCloudRecordSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GoogleCloudRecordFilter
