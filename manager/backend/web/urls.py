from rest_framework import routers

from .api import WebViewSet

router = routers.DefaultRouter()
router.register("api/web", WebViewSet, "web")
urlpatterns = router.urls
