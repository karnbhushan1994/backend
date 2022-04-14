from rest_framework import routers

from .api import UserContactsViewSet

router = routers.DefaultRouter()
router.register("api/user_contacts", UserContactsViewSet, "user_contacts")
urlpatterns = router.urls
