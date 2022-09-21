from rest_framework import serializers

from rdwatch.serializers import BoundingBoxSerializer, TimeRangeSerializer


class SiteObservationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    label = serializers.CharField()  # type: ignore
    score = serializers.FloatField()
    constellation = serializers.CharField()
    spectrum = serializers.CharField()
    timerange = TimeRangeSerializer()
    bbox = BoundingBoxSerializer()


class SiteObservationListSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    timerange = TimeRangeSerializer()
    bbox = BoundingBoxSerializer()
    results = SiteObservationSerializer(many=True)
