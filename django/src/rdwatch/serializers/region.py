import iso3166

from rest_framework import serializers

from rdwatch.models import Region


class RegionStringSerializer(serializers.BaseSerializer):
    def to_representation(self, value):
        if isinstance(value, Region):
            country = value.country
            classification = value.classification.slug
            number = value.number
        else:
            country = value["country"]
            classification = value["classification"]["slug"]
            number = value["number"]
        country_numeric = str(country).zfill(3)
        country_code = iso3166.countries_by_numeric[country_numeric].alpha2
        region_number = "xxx" if number is None else str(number).zfill(3)
        return f"{country_code}_{classification}{region_number}"


class RegionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = RegionStringSerializer(source="*")
