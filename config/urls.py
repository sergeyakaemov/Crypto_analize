"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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

from django.conf import settings
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

api_v1_patterns: list[URLPattern | URLResolver] = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("schema/", SpectacularAPIView.as_view(throttle_classes=[]), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="schema", throttle_classes=[]),
        name="swagger-ui",
    ),
    path("", include("crypto.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(r"^api/(?P<version>v1)/", include(api_v1_patterns)),
]

if settings.DEBUG:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
