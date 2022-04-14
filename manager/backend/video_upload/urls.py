from rest_framework import routers

from .api import PresignedURLViewset

router = routers.DefaultRouter()
router.register("api/presigned-url", PresignedURLViewset, "presigned-url")
urlpatterns = router.urls
