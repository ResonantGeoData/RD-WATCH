from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rgd.rest.base import ModelViewSet, ReadOnlyModelViewSet

from watch.core import filters, models, serializers


class RegionViewSet(ModelViewSet):
    serializer_class = serializers.RegionSerializer
    queryset = models.Region.objects.all()
    filterset_class = filters.RegionFilter


class SiteViewSet(ModelViewSet):
    serializer_class = serializers.SiteSerializer
    queryset = models.Site.objects.all()
    filterset_class = filters.SiteFilter


class RegionViewSetBasic(ReadOnlyModelViewSet):
    serializer_class = serializers.RegionSerializerBasic
    queryset = models.Region.objects.all()
    filterset_class = filters.RegionFilter


class SiteViewSetBasic(ReadOnlyModelViewSet):
    serializer_class = serializers.SiteSerializerBasic
    queryset = models.Site.objects.all()
    filterset_class = filters.SiteFilter


class ObservationViewSetBasic(ReadOnlyModelViewSet):
    serializer_class = serializers.ObservationSerializerBasic
    queryset = models.Observation.objects.all()
    filterset_class = filters.ObservationFilter


class STACFileViewSet(ModelViewSet):
    serializer_class = serializers.STACFileSerializer
    queryset = models.STACFile.objects.all()
    filterset_class = filters.STACFileFilter

    @swagger_auto_schema(query_serialzer=serializers.StacFileGetSerializer())
    def list(self, request, *args, **kwargs):
        serializer = serializers.StacFileGetSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data.get('file', None)
        queryset = self.filter_queryset(self.get_queryset())

        # Filter if File ID passed
        if file:
            queryset = queryset.filter(file=file)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
