from django.urls import path
from .views import login_failed, logout_success

urlpatterns = [
    path("login-failed/", login_failed, name="login_failed"),
    path("logged-out/", logout_success, name="logout_success"),
]
