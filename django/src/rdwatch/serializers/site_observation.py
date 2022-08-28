from rdwatch.models import SiteObservation
from rest_framework import serializers


class SiteObservationSerializer(serializers.ModelSerializer):
    bounds = serializers.ListField(
        child=serializers.FloatField(
            read_only=True,
        ),
        read_only=True,
        source="boundingbox.extent",
        min_length=4,
        max_length=4,
        help_text=(
            "The maximum extent of available map tiles represented in WGS 84 "
            "latitude and longitude values, in the order left, bottom, right "
            "top."
        ),
    )

    class Meta:
        model = SiteObservation
        fields = ["id", "configuration", "label", "score", "bounds"]
