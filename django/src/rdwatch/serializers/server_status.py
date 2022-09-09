from rest_framework import serializers

from rdwatch.dataclasses import ServerStatus


class UptimeSerializer(serializers.Serializer):
    iso8601 = serializers.DurationField(source="*")
    days = serializers.IntegerField()
    seconds = serializers.IntegerField()
    useconds = serializers.IntegerField(source="microseconds")


class ServerStatusSerializer(serializers.Serializer):
    uptime = UptimeSerializer(required=True)
    hostname = serializers.CharField(required=True)
    ip = serializers.IPAddressField(required=True)

    def create(self, validated_data):
        instance = ServerStatus(
            uptime=validated_data["uptime"]["iso8601"],
            hostname=validated_data["hostname"],
            ip=validated_data["iso8601"],
        )
        # we'd save it here if this were a Django model
        # instance.save()
        return instance

    def update(self, instance, validated_data):
        instance.uptime = validated_data.get("uptime", instance.uptime)
        instance.hostname = validated_data.get("hostname", instance.hostname)
        instance.ip = validated_data.get("ip", instance.ip)
        # we'd save it here if this were a Django model
        # instance.save()
        return instance
