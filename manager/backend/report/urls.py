from rest_framework import routers

from .api import ReportViewSet

router = routers.DefaultRouter()
router.register("api/report", ReportViewSet, "report")
urlpatterns = router.urls
