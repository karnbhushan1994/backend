from django.shortcuts import render
from rest_framework import routers

from .api import LoginCountViewSet

# GET/PUT - http://localhost:8000/api/login_count/5d0b67be-30f9-4342-b12a-40e5b1553fd1/

router = routers.DefaultRouter()
router.register("api/login_count", LoginCountViewSet, "login_count")

urlpatterns = router.urls
