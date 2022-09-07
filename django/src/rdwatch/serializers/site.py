from rest_framework import serializers


class PerformerSerializer(serializers.Serializer):
    team_name = serializers.CharField(source="description")
    short_code = serializers.CharField(source="slug")


class SiteEvaluationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    performer = PerformerSerializer(source="configuration.performer")
    configuration = serializers.JSONField(source="configuration.parameters")
    site = serializers.CharField(source="site_id")
    timestamp = serializers.DateTimeField()
    score = serializers.FloatField()
    bbox = serializers.ListField(
        child=serializers.FloatField(),
        required=True,
        source="bbox.extent",
        min_length=4,
        max_length=4,
    )


class SiteObservationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    label = serializers.CharField()  # type: ignore
    score = serializers.FloatField()
    timestamp = serializers.DateTimeField()
    constellation = serializers.CharField(source="constellation.slug")
    spectrum = serializers.CharField(source="spectrum.slug")
