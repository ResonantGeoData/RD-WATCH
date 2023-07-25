from rest_framework import serializers

from rdwatch.serializers import BoundingBoxSerializer, TimeRangeSerializer


class SiteObservationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    label = serializers.CharField()  # type: ignore
    score = serializers.FloatField()
    constellation = serializers.CharField()
    spectrum = serializers.CharField()
    timerange = TimeRangeSerializer(required=False, allow_null=True)
    timestamp = serializers.IntegerField(required=False, allow_null=True)  # type: ignore
    bbox = BoundingBoxSerializer()
    area = serializers.FloatField()


class SiteObservationListSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    timerange = TimeRangeSerializer()
    bbox = BoundingBoxSerializer()
    results = SiteObservationSerializer(many=True)
