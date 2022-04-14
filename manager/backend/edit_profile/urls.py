from rest_framework import routers

from .api import EditProfileViewSet

router = routers.DefaultRouter()
router.register("api/edit-profile", EditProfileViewSet, "edit-profile")
urlpatterns = router.urls
