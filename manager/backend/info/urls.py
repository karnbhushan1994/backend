from inspect import getlineno
from rest_framework import routers

from .api import VersionViewSet

router = routers.DefaultRouter()
router.register("api/version", VersionViewSet, "version")
urlpatterns = router.urls
