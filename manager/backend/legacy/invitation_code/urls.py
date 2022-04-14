from rest_framework import routers

from .api import CreateInvitationCode, InvitationCodeViewSet, VerifyInvitationCode

router = routers.DefaultRouter()
router.register("api/create-code", CreateInvitationCode, "create-code")
router.register("api/verify-code", VerifyInvitationCode, "verify-code")
router.register("api/invite", InvitationCodeViewSet, "invite")
urlpatterns = router.urls
