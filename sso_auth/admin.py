from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import MacFastUser


@admin.register(MacFastUser)
class MacFastUserAdmin(BaseUserAdmin):
    """
    Registers the custom MacFastUser model with the admin site
    """

    search_fields = ("username", "email")
