from rest_framework import serializers

from rdwatch.models import lookups
from rdwatch.serializers.generics import TimeRangeSerializer
from rdwatch.serializers.performer import PerformerSerializer
from rdwatch.serializers.region import RegionSerializer


class HyperParametersWriteSerializer(serializers.Serializer):
    performer = serializers.CharField()
    title = serializers.CharField(max_length=1000)
    parameters = serializers.JSONField(default=dict)
    expiration_time = serializers.IntegerField(
        min_value=0, max_value=24 * 365, required=False
    )

    def validate_performer(self, value: str) -> lookups.Performer:
        try:
            return lookups.Performer.objects.get(slug=value.upper())
        except lookups.Performer.DoesNotExist:
            raise serializers.ValidationError(f"Invalid performer '{value}'")


class HyperParametersDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    region = RegionSerializer(allow_null=True)
    performer = PerformerSerializer()
    parameters = serializers.JSONField()
    numsites = serializers.IntegerField()
    score = serializers.FloatField(allow_null=True)
    timestamp = serializers.IntegerField(allow_null=True)
    timerange = TimeRangeSerializer(allow_null=True)
    bbox = serializers.JSONField(allow_null=True)


class HyperParametersListSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    previous = serializers.CharField()
    next = serializers.CharField()
    timerange = TimeRangeSerializer()
    bbox = serializers.JSONField(allow_null=True)
    results = HyperParametersDetailSerializer(many=True)
