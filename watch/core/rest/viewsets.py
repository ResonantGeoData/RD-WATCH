from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rgd.rest.base import ModelViewSet

from watch.core.models import STACFile
from watch.core.serializers.stacfile import StacFileGetSerializer, STACFileSerializer


class STACFileViewSet(ModelViewSet):
    serializer_class = STACFileSerializer
    queryset = STACFile.objects.all()

    @swagger_auto_schema(query_serialzer=StacFileGetSerializer())
    def list(self, request, *args, **kwargs):
        serializer = StacFileGetSerializer(data=request.query_params)
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
