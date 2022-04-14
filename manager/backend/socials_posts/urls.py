from rest_framework import routers

from .api import FBPostsViewSet, IGPostsViewSet, TwitterPostsViewSet

router = routers.DefaultRouter()
router.register("api/posts-ig", IGPostsViewSet, "posts-ig")
router.register("api/posts-fb", FBPostsViewSet, "posts-fb")
router.register("api/posts-twitter", TwitterPostsViewSet, "posts-twitter")
urlpatterns = router.urls
