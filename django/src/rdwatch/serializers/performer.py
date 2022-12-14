from rest_framework import serializers


class PerformerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    team_name = serializers.CharField()
    short_code = serializers.CharField()
