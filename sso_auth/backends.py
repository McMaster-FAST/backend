import json
import jwt
from jwt import PyJWKClient
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.conf import settings

# Init PyJWKClient globally so it stays alive and caches the keys.
jwks_client = PyJWKClient(
    getattr(settings, "OIDC_OP_JWKS_ENDPOINT", ""),
    cache_jwk_set=True,
    lifespan=600,
    cache_keys=True,
    max_cached_keys=16,
)


class MyOIDCBackend(OIDCAuthenticationBackend):

    def verify_token(self, token, **kwargs):
        """
        Handles fetching the public key and validating the RSA256 signature locally.
        """
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.OIDC_RP_CLIENT_ID,
                issuer=getattr(settings, "OIDC_OP_ISSUER", None),
                options={
                    "verify_issuer": bool(getattr(settings, "OIDC_OP_ISSUER", False))
                },
            )

            nonce = kwargs.get("nonce")
            if nonce and payload.get("nonce") != nonce:
                return None

            return payload
        except jwt.PyJWTError as e:
            if settings.DEBUG:
                print(f"Token validation failed: {e}")
            return None

    def get_userinfo(self, access_token, id_token, payload):
        """Using locally verified payload directly."""
        return payload

    def verify_claims(self, claims):
        # Entra uses "sub" or "oid" (Object ID) to identify users.
        return "sub" in claims or "oid" in claims

    def filter_users_by_claims(self, claims):
        email = claims.get("email")
        username = claims.get("preferred_username") or claims.get("nickname")

        if email:
            users = self.UserModel.objects.filter(email__iexact=email)
            if users.exists():
                return users

        if username:
            users = self.UserModel.objects.filter(username__iexact=username)
            if users.exists():
                return users

        return self.UserModel.objects.none()

    def create_user(self, claims):
        email = claims.get("email")
        username = claims.get("preferred_username") or claims.get("name")

        if not username and email:
            username = email.split("@")[0]

        if not email:
            # Fallback for McMaster students if email claim is missing
            username_clean = username.replace(" ", "_") if username else "user"
            email = f"{username_clean}@mcmaster.ca"

        user = self.UserModel.objects.create_user(username=username, email=email)
        self._set_user_flags(user, claims)
        return user

    def update_user(self, user, claims):
        self._set_user_flags(user, claims)
        return user

    def _set_user_flags(self, user, claims):
        """
        TEMPORARY: Granting everyone who logs in via Entra
        full admin access for development/testing.
        """
        if settings.DEBUG:
            print(f"--- DEBUG: Granting Superuser access to {user.email} ---")

        user.is_staff = True
        user.is_superuser = True
        user.save()
