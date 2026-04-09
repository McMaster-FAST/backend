from django.urls import path
from django.conf import settings
from .views import login_failed, logout_success

urlpatterns = [
    path("login-failed/", login_failed, name="login_failed"),
    path("logged-out/", logout_success, name="logout_success"),
]

if settings.DEBUG:
    from .views import mock_token_endpoint, mock_userinfo_endpoint

    urlpatterns += [
        path("mock-oidc/token/", mock_token_endpoint, name="mock_token"),
        path("mock-oidc/userinfo/", mock_userinfo_endpoint, name="mock_userinfo"),
    ]
