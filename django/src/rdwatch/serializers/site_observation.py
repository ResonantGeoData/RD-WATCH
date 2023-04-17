from django.core.files.storage import default_storage
from rest_framework import serializers

from rdwatch.models import SiteObservation
from rdwatch.serializers import BoundingBoxSerializer, TimeRangeSerializer


class SiteObservationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    label = serializers.CharField()  # type: ignore
    score = serializers.FloatField()
    constellation = serializers.CharField()
    spectrum = serializers.CharField()
    timerange = TimeRangeSerializer()
    bbox = BoundingBoxSerializer()
    video = serializers.SerializerMethodField()

    class Meta:
        model = SiteObservation
        fields = ['video']

    def get_video(self, obj):
        video = obj.get('video', None)
        if video:
            return default_storage.url(video)
        return None


class SiteObservationListSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    timerange = TimeRangeSerializer()
    bbox = BoundingBoxSerializer()
    results = SiteObservationSerializer(many=True)
