from rest_framework import routers

from .api import SkinViewSet


router = routers.DefaultRouter()
router.register("api/skin", SkinViewSet, "skin")

urlpatterns = router.urls
