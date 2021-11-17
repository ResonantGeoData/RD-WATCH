from rgd.rest.base import ModelViewSet

from ..models import STACFile
from ..serializers import STACFileSerializer


class STACFileViewSet(ModelViewSet):
    serializer_class = STACFileSerializer
    queryset = STACFile.objects.all()
