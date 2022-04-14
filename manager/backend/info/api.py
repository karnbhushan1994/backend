from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class VersionViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        """
        version ^1.24
        Returns the current live verion and environment.
        """
        return Response(
            {
                "live_versions": settings.LIVE_VERSION.split(","),
                "env": settings.ENV,
            }
        )

    @action(detail=False, methods=["get"])
    def v2(self, request):
        """
        version ^1.12

        Returns a list of allowed live versions.
        """
        return Response(settings.LIVE_VERSION.split(","))
