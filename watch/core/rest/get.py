from rest_framework.generics import RetrieveAPIView

from .. import models, serializers


class GetRegion(RetrieveAPIView):
    serializer_class = serializers.RegionSerializer
    lookup_field = 'pk'
    queryset = models.Region.objects.all()
