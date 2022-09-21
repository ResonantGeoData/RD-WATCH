from rest_framework import serializers


class TimeRangeSerializer(serializers.Serializer):
    min = serializers.IntegerField()
    max = serializers.IntegerField()


class BoundingBoxSerializer(serializers.Serializer):
    xmin = serializers.FloatField()
    xmax = serializers.FloatField()
    ymin = serializers.FloatField()
    ymax = serializers.FloatField()
