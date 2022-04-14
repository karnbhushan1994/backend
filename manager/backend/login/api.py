import json
import logging

from django.contrib.auth import authenticate, login
from drf_yasg import openapi
from drf_yasg.openapi import TYPE_STRING, TYPE_OBJECT, TYPE_BOOLEAN
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..serializers import TaggUserSerializer


class LoginViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    serializer_class = TaggUserSerializer

    def __init__(self, *args, **kwargs):
        super(LoginViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=TYPE_OBJECT,
            required=["username", "password"],
            properties={
                "username": openapi.Schema(type=TYPE_STRING),
                "password": openapi.Schema(type=TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Response(
                "",
                openapi.Schema(
                    type=TYPE_OBJECT,
                    properties={
                        "status": openapi.Schema(type=TYPE_STRING),
                        "UserID": openapi.Schema(type=TYPE_STRING),
                        "isOnboarded": openapi.Schema(type=TYPE_BOOLEAN),
                        "university": openapi.Schema(type=TYPE_STRING),
                    },
                ),
            ),
            401: "Invalid credentials",
        },
    )
    def create(self, request):
        try:
            body = json.loads(request.body)

            if "username" not in body:
                return Response(
                    "Username not found in body.", status=status.HTTP_400_BAD_REQUEST
                )
            username = body["username"]
            if "password" not in body:
                return Response(
                    "Password not found in body.", status=status.HTTP_400_BAD_REQUEST
                )
            password = body["password"]

            user = authenticate(username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    # Redirect to home page
                    token, _ = Token.objects.get_or_create(user=user)

                    response = {
                        "status": "Success: User logged in",
                        "UserID": user.id,
                        "token": token.key,
                        "isOnboarded": user.taggusermeta.is_onboarded,
                        "university": user.university,
                    }
                    return Response(response, status=200)
            else:
                return Response("Error: Invalid credentials", status=401)
        except UnicodeDecodeError as err:
            self.logger.exception("Expected JSON data in request body.")
            return Response("Expected JSON data in request body.", status=400)
        except json.decoder.JSONDecodeError:
            self.logger.exception("Expected JSON-formatted data.")
            return Response("Expected JSON-formatted data.", status=400)
        except Exception as err:
            self.logger.exception("Internal server error")
            return Response("Internal server error", status=500)
