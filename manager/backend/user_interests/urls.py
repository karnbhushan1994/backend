from rest_framework import routers

from .api import UserInterestsViewSet

router = routers.DefaultRouter()
router.register("api/user_interests", UserInterestsViewSet, "user_interests")
urlpatterns = router.urls
