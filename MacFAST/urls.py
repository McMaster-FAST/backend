"""
URL configuration for MacFAST project.
"""

from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path(
        "admin/login/",
        RedirectView.as_view(
            url=reverse_lazy("oidc_authentication_init"), permanent=False
        ),
    ),
    path("admin/", admin.site.urls),
    path("oidc/", include("mozilla_django_oidc.urls")),
    path("auth/", include("sso_auth.urls")),
    path("api/core/", include("core.urls")),
    path("api/", include("courses.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
