from rest_framework import routers

from .api import SendOtpViewSet, VerifyOtpViewSet, PhoneViewSet

router = routers.DefaultRouter()
router.register("api/send-otp", SendOtpViewSet, "send-otp")
router.register("api/verify-otp", VerifyOtpViewSet, "verify-otp")
router.register("api/phone", PhoneViewSet, "phone")
urlpatterns = router.urls
