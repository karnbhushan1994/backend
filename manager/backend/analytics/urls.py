from rest_framework import routers

from .widgets.api import WidgetViewsViewSet
from .profile.api import ProfileViewsViewSet
from .moments.api import MomentInsightsViewSet

router = routers.DefaultRouter()
router.register("api/insights/taggs", WidgetViewsViewSet, "insights_taggs")
router.register("api/insights/profile", ProfileViewsViewSet, "insights_profile")
router.register("api/insights/moments", MomentInsightsViewSet, "insights_moments")

urlpatterns = router.urls
