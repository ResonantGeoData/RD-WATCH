import datetime
import socket
from dataclasses import dataclass

from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView

SERVER_INSTANCE_EPOCH = datetime.datetime.now()


@dataclass
class ServerStatus:
    uptime: datetime.timedelta
    hostname: str
    ip: str


class UptimeSerializer(serializers.Serializer):
    iso8601 = serializers.DurationField(source='*')
    days = serializers.IntegerField()
    seconds = serializers.IntegerField()
    useconds = serializers.IntegerField(source='microseconds')


class ServerStatusSerializer(serializers.Serializer):
    uptime = UptimeSerializer(required=True)
    hostname = serializers.CharField(required=True)
    ip = serializers.IPAddressField(required=True)

    def create(self, validated_data):
        instance = ServerStatus(
            uptime=validated_data['uptime']['iso8601'],
            hostname=validated_data['hostname'],
            ip=validated_data['iso8601'],
        )
        # we'd save it here if this were a Django model
        # instance.save()
        return instance

    def update(self, instance, validated_data):
        instance.uptime = validated_data.get('uptime', instance.uptime)
        instance.hostname = validated_data.get('hostname', instance.hostname)
        instance.ip = validated_data.get('ip', instance.ip)
        # we'd save it here if this were a Django model
        # instance.save()
        return instance


class ServerStatusSchema(AutoSchema):
    def get_operation_id(self, *args):
        return 'getStatus'

    def get_serializer(self, *args):
        return ServerStatusSerializer()


class RetrieveServerStatus(APIView):
    permission_classes = [permissions.AllowAny]
    schema = ServerStatusSchema()
    action = 'retrieve'

    def get(self, request):
        uptime = datetime.datetime.now() - SERVER_INSTANCE_EPOCH
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        server_status = ServerStatus(uptime, hostname, ip)
        serializer = ServerStatusSerializer(server_status)
        return Response(serializer.data)
