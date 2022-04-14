"""manager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from .settings import ADMIN_ENABLED

schema_view = get_schema_view(
    openapi.Info(
        title="Tagg Backend",
        default_version="v1",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = []
if ADMIN_ENABLED:
    urlpatterns.append(path("admin/", admin.site.urls))

urlpatterns += [
    path("", include("backend.login.urls")),
    path("", include("backend.registration.urls")),
    path("", include("backend.phone_verification.urls")),
    path("", include("backend.social_linking.urls")),
    path("", include("backend.password_reset.urls")),
    path("", include("backend.friends.urls")),
    path("", include("backend.search.urls")),
    path("", include("backend.social_linking.urls")),
    path("", include("backend.socials_posts.urls")),
    path("", include("backend.get_profile_info.urls")),
    path("", include("backend.get_profile_pic.urls")),
    path("", include("backend.edit_profile.urls")),
    path("", include("backend.moments.urls")),
    path("", include("backend.moments.moment_category.urls")),
    path("", include("backend.moments.comments.urls")),
    path("", include("backend.moments.tags.urls")),
    path("", include("backend.report.urls")),
    path("", include("backend.blocked_users.urls")),
    path("", include("backend.notifications.urls")),
    path("", include("backend.discover.urls")),
    path("", include("backend.waitlist_user.urls")),
    path("", include("backend.info.urls")),
    path("", include("backend.suggested_people.urls")),
    path("", include("backend.profile.urls")),
    path("", include("backend.messaging.urls")),
    path("", include("backend.reactions.urls")),
    path("", include("backend.video_upload.urls")),
    path("", include("backend.widget.urls")),
    path("", include("backend.tagg_shop.urls")),
    path("", include("backend.user_interests.urls")),
    path("", include("backend.skins.urls")),
    path("", include("backend.web.urls")),
    path("", include("backend.login_count.urls")),
    path("", include("backend.has_rated.urls")),
    path("", include("backend.gamification.urls")),
    path("", include("backend.analytics.urls")),
    url(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    url(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]
