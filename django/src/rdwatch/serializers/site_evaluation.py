import iso3166

from rest_framework import serializers

from rdwatch.serializers import BoundingBoxSerializer, TimeRangeSerializer


class PerformerSerializer(serializers.Serializer):
    team_name = serializers.CharField()
    short_code = serializers.CharField()


class SiteStringSerializer(serializers.BaseSerializer):
    def to_representation(self, value):
        country_numeric = str(value['region']['country']).zfill(3)
        country_code = iso3166.countries_by_numeric[country_numeric].alpha2
        region_class = value['region']['classification']
        region_number = (
            'xxx'
            if value['region']['number'] is None
            else str(value['region']['number']).zfill(3)
        )
        site_number = str(value['number']).zfill(3)
        return f'{country_code}_{region_class}{region_number}_{site_number}'


class SiteEvaluationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    site = SiteStringSerializer()
    configuration = serializers.JSONField()
    performer = PerformerSerializer()
    score = serializers.FloatField()
    timestamp = serializers.IntegerField()
    timerange = TimeRangeSerializer()
    bbox = BoundingBoxSerializer()


class SiteEvaluationListSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    timerange = TimeRangeSerializer()
    bbox = BoundingBoxSerializer()
    performers = serializers.ListField()
    results = SiteEvaluationSerializer(many=True)
    next = serializers.CharField()
    previous = serializers.CharField()
