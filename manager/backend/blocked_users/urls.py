from rest_framework import routers

from .api import BlockUserViewSet

router = routers.DefaultRouter()
router.register("api/block", BlockUserViewSet, "block")
urlpatterns = router.urls
