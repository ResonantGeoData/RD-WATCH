from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from rdwatch.models import Region
from rdwatch.serializers import RegionSerializer


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all().select_related('classification')
    serializer_class = RegionSerializer
    pagination_class = PageNumberPagination
    # Set the number of items per page to 1000
    pagination_class.page_size = 1000
