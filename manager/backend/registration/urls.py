from rest_framework import routers

from .api import RegisterViewSet

router = routers.DefaultRouter()
router.register("api/register", RegisterViewSet, "register")
urlpatterns = router.urls
