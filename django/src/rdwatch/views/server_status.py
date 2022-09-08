import datetime
import socket

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView

from rdwatch.dataclasses import ServerStatus
from rdwatch.serializers import ServerStatusSerializer

SERVER_INSTANCE_EPOCH = datetime.datetime.now()


class ServerStatusSchema(AutoSchema):
    def get_operation_id(self, *args):
        return "getStatus"

    def get_serializer(self, *args):
        return ServerStatusSerializer()


class RetrieveServerStatus(APIView):

    permission_classes = [permissions.AllowAny]
    schema = ServerStatusSchema()
    action = "retrieve"

    def get(self, request):
        uptime = datetime.datetime.now() - SERVER_INSTANCE_EPOCH
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        server_status = ServerStatus(uptime, hostname, ip)
        serializer = ServerStatusSerializer(server_status)
        return Response(serializer.data)
