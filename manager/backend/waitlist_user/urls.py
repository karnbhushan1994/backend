from rest_framework import routers

from .api import WaitlistUserViewSet

router = routers.DefaultRouter()
router.register("api/waitlist-user", WaitlistUserViewSet, "waitlist-user")
urlpatterns = router.urls
