from rest_framework.generics import CreateAPIView

from .. import models, serializers


class CreateRegion(CreateAPIView):
    queryset = models.Region.objects.all()
    serializer_class = serializers.RegionSerializer
