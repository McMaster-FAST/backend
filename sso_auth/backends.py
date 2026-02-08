from mozilla_django_oidc.auth import OIDCAuthenticationBackend
import json
import hashlib
from django.conf import settings
from django.core.cache import cache

ROLES_CLAIM_URL = "https://chemfast.ca/roles"


class MyOIDCBackend(OIDCAuthenticationBackend):

    def get_userinfo(self, access_token, id_token, payload):
        """
        TODO
        Convert to local validation with caching when switching over to Microsoft Entra
        """

        """
        Override get_userinfo to cache the response from Auth0.
        This prevents hitting the 429 Rate Limit when the frontend
        fires multiple API requests at once.
        """
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        cache_key = f"oidc_userinfo_{token_hash}"

        user_info = cache.get(cache_key)

        if user_info:
            print("found userinfo in cache")
            return user_info

        try:
            user_info = super().get_userinfo(access_token, id_token, payload)
        except Exception as e:
            raise e

        cache.set(cache_key, user_info, timeout=600)

        return user_info

    def verify_claims(self, claims):
        if settings.DEBUG:
            print("verify_claims")
            print(json.dumps(claims, indent=2))
        return "sub" in claims

    def filter_users_by_claims(self, claims):
        email = claims.get("email")
        username = claims.get("nickname") or claims.get("preferred_username")

        if email:
            users = self.UserModel.objects.filter(email__iexact=email)
            if users.exists():
                print(f"--- DEBUG: Found user by email: {email} ---")
                return users

        if username:
            users = self.UserModel.objects.filter(username__iexact=username)
            if users.exists():
                print(f"--- DEBUG: Found user by username: {username} ---")
                return users

        return self.UserModel.objects.none()

    def create_user(self, claims):
        if settings.DEBUG:
            print("--- DEBUG: create_user (NEW USER) ---")

        email = claims.get("email")
        username = claims.get("nickname") or claims.get("preferred_username")

        if not username and email:
            username = email.split("@")[0]

        if not email:
            print("--- WARNING: No email in claims. Generating placeholder. ---")
            email = f"{username}@no-email.chemfast.ca"

        user = self.UserModel.objects.create_user(username=username, email=email)
        self._set_user_flags(user, claims)
        return user

    def update_user(self, user, claims):
        if settings.DEBUG:
            print("--- DEBUG: update_user (EXISTING USER) ---")
        self._set_user_flags(user, claims)
        return user

    def _set_user_flags(self, user, claims):
        roles = claims.get(ROLES_CLAIM_URL, [])
        user.is_staff = False
        user.is_superuser = False
        if "admin" in roles:
            user.is_staff = True
            user.is_superuser = True
        elif "staff" in roles:
            user.is_staff = True
        user.save()
