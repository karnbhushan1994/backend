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

from .models import HasRated
from .serializers import HasRatedSerializer


class HasRatedViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(HasRatedViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def retrieve(self, request, pk):
        try:
            if pk == None:
                raise ValidationError({"uid": "This field is required"})

            hasRatedObj = HasRated.objects.get(uid=pk)
            return Response(HasRatedSerializer(hasRatedObj).data)

        except HasRated.DoesNotExist:
            user = TaggUser.objects.get(id=pk)
            hasRatedObj = HasRated(uid=user, hasRated=False)
            hasRatedObj.save()
            return Response(HasRatedSerializer(hasRatedObj).data)
        except Exception as error:
            self.logger.exception(error)
            return Response("Something went wrong", 500)

    def update(self, request, pk):
        try:
            if pk == None:
                raise ValidationError({"uid": "This field is required"})

            hasRatedObj = HasRated.objects.get(uid=pk)
            hasRatedObj.hasRated = True
            hasRatedObj.save()
            return Response(HasRatedSerializer(hasRatedObj).data)

        except HasRated.DoesNotExist:
            self.logger.error("User does not exist")
            return Response("User does not exist", 400)
        except Exception as error:
            self.logger.exception(error)
            return Response("Something went wrong", 500)
