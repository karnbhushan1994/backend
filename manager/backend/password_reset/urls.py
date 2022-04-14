from rest_framework import routers

from .api import PasswordResetViewset

router = routers.DefaultRouter()
router.register("api/password-reset", PasswordResetViewset, "password-reset")
urlpatterns = router.urls
