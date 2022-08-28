from django.contrib.gis.db.models.functions import AsGeoJSON, Envelope, Transform
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rdwatch.models import SiteCharacterization
from rdwatch.serializers import SiteCharacterizationSerializer
from rest_framework import permissions, viewsets
from rest_framework.decorators import action


class SiteCharacterizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        SiteCharacterization.objects.annotate(
            boundingbox=Transform(Envelope("geometry"), 4326)
        )
        .defer("geometry")
        .all()
    )
    serializer_class = SiteCharacterizationSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True)
    def geojson(self, *args, pk=None, **kwargs):
        """
        Retrieve the GeoJSON.
        """
        obj = get_object_or_404(
            SiteCharacterization.objects.values(
                geojson=AsGeoJSON(Transform("geometry", 4326))
            ),
            pk=pk,
        )
        return HttpResponse(
            obj["geojson"],
            content_type="application/vnd.geo+json",
        )
