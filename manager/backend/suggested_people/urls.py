from rest_framework import routers

from .api import SuggestedPeopleViewSet

router = routers.DefaultRouter()
# legacy
# router.register("api/suggested_people", SuggestedPeopleViewSet, "suggested_people")
urlpatterns = router.urls
