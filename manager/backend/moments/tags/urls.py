from rest_framework import routers

from .api import MomentTagViewSet

router = routers.DefaultRouter()
router.register("api/moment-tag", MomentTagViewSet, "moment-tag")
urlpatterns = router.urls
