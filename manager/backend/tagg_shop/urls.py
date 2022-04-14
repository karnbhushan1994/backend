from rest_framework import routers

from .api import TaggShopViewSet

router = routers.DefaultRouter()
router.register("api/tagg_shop", TaggShopViewSet, "tagg_shop")
urlpatterns = router.urls







