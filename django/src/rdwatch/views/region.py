from rest_framework import viewsets

from rdwatch.models import Region
from rdwatch.serializers import RegionSerializer


class RegionViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Region.objects.all().select_related("classification")
    serializer_class = RegionSerializer
