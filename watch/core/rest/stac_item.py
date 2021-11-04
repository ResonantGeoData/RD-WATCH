from rgd.rest.base import ModelViewSet

from ..models import STACItem
from ..serializers import STACItemSerializer


class STACItemViewSet(ModelViewSet):
    serializer_class = STACItemSerializer
    queryset = STACItem.objects.all()
