from django.db.models import F
from rest_framework import viewsets

from rdwatch.models.lookups import Performer
from rdwatch.serializers import PerformerSerializer


class PerformerViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Performer.objects.defer("description", "slug").annotate(
        team_name=F("description"),
        short_code=F("slug"),
    )
    serializer_class = PerformerSerializer
