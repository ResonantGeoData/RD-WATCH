from rest_framework import mixins, permissions, viewsets

from rdwatch.models import HyperParameters
from rdwatch.serializers import HyperParametersSerializer


class ModelRunViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):

    permission_classes = [permissions.AllowAny]
    queryset = HyperParameters.objects.select_related("performer").all()
    serializer_class = HyperParametersSerializer
