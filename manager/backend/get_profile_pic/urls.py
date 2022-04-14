from rest_framework import routers

from .api import HeaderPicViewSet, ProfilePicViewSet

router = routers.DefaultRouter()
router.register("api/profile-pic", ProfilePicViewSet, "profile-pic")
router.register("api/header-pic", HeaderPicViewSet, "header-pic")
urlpatterns = router.urls
