from rest_framework import routers
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from .api import NotificationListViewSet

router = routers.DefaultRouter()
router.register("api/notifications", NotificationListViewSet, "notifications")
router.register("api/fcm", FCMDeviceAuthorizedViewSet, "fcm")

urlpatterns = router.urls
