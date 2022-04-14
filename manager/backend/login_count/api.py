import logging
from rest_framework import viewsets

from django.db.models.signals import pre_save
from django.dispatch.dispatcher import receiver
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from ..models import TaggUser

from .models import LoginCount
from .serializers import LoginCountSerializer

from datetime import datetime

class LoginCountViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(LoginCountViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def retrieve(self, request, pk):
        try:
            if pk == None:
                raise ValidationError({"uid": "This field is required"})

            loginCount = LoginCount.objects.get(uid=pk)
            return Response(LoginCountSerializer(loginCount).data)

        except LoginCount.DoesNotExist:
            user = TaggUser.objects.get(id=pk)
            countObj = LoginCount(uid=user, count=0)
            countObj.save()
            return Response(LoginCountSerializer(countObj).data)
        except Exception as error:
            self.logger.exception(error)
            return Response("Something went wrong", 500)

    def update(self, request, pk):
        try:
            if pk == None:
                raise ValidationError({"uid": "This field is required"})

            loginCount = LoginCount.objects.get(uid=pk)
            if str(loginCount.last_login) == str(datetime.now().date()):
                loginCount.count += 1
                loginCount.save()
            else:
                loginCount.last_login = datetime.now().date()
                loginCount.count = 1
                loginCount.save()
            return Response(LoginCountSerializer(loginCount).data)

        except LoginCount.DoesNotExist:
            user = TaggUser.objects.get(id=pk)
            loginCount = LoginCount(uid=user, count=1)
            loginCount.save()
            return Response(LoginCountSerializer(loginCount).data)
        except Exception as error:
            self.logger.exception(error)
            return Response("Something went wrong", 500)
