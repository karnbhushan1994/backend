from rest_framework import routers

from .api import DiscoverViewSet

router = routers.DefaultRouter()
router.register("api/discover", DiscoverViewSet, "discover")
urlpatterns = router.urls
