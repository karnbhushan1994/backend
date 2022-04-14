from rest_framework import routers

from .api import FriendsViewSet

router = routers.DefaultRouter()
router.register("api/friends", FriendsViewSet, "friends")
urlpatterns = router.urls
