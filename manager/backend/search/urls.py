from rest_framework import routers

from .api import SearchViewSet
from .api import AllUsersViewSet

router = routers.DefaultRouter()
router.register("api/search", SearchViewSet, "search")
router.register("api/users", AllUsersViewSet, "users")
urlpatterns = router.urls
