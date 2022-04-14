from rest_framework import routers

from .api import MomentsCategoryViewSet

router = routers.DefaultRouter()

router.register("api/moment-category", MomentsCategoryViewSet, "moment-category")
urlpatterns = router.urls
