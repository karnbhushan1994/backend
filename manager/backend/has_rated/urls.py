from django.shortcuts import render
from rest_framework import routers

from .api import HasRatedViewSet

# GET/PUT - http://localhost:8000/api/has_rated/5d0b67be-30f9-4342-b12a-40e5b1553fd1/

router = routers.DefaultRouter()
router.register("api/has_rated", HasRatedViewSet, "has_rated")

urlpatterns = router.urls
