from rest_framework import serializers

from rdwatch.serializers import BoundingBoxSerializer, TimeRangeSerializer


class SiteObservationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    label = serializers.CharField()  # type: ignore
    score = serializers.FloatField()
    constellation = serializers.CharField()
    spectrum = serializers.CharField()
    timerange = TimeRangeSerializer()
    timestamp = serializers.IntegerField()  # type: ignore
    bbox = BoundingBoxSerializer()
    area = serializers.FloatField()


class SiteObservationListSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    timerange = TimeRangeSerializer()
    bbox = BoundingBoxSerializer()
    results = SiteObservationSerializer(many=True)

class SiteObservationGeomSerializer(serializers.Serializer):
    timestamp = serializers.IntegerField()
    geoJSON = serializers.JSONField(default=dict)
    label = serializers.CharField()

class SiteObservationGeomListSerializer(serializers.Serializer):
    results = SiteObservationGeomSerializer(many=True)
