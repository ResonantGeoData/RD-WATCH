from django.contrib.gis.db.models.functions import AsGeoJSON, Envelope, Transform
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rdwatch.models import SiteObservation
from rdwatch.serializers import SiteObservationSerializer
from rest_framework import permissions, viewsets
from rest_framework.decorators import action


class SiteObservationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        SiteObservation.objects.annotate(
            boundingbox=Transform(Envelope("geometry"), 4326)
        )
        .defer("geometry")
        .all()
    )
    serializer_class = SiteObservationSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True)
    def geojson(self, *args, pk=None, **kwargs):
        """
        Retrieve the GeoJSON.
        """
        obj = get_object_or_404(
            SiteObservation.objects.values(
                geojson=AsGeoJSON(Transform("geometry", 4326))
            ),
            pk=pk,
        )
        return HttpResponse(
            obj["geojson"],
            content_type="application/vnd.geo+json",
        )
