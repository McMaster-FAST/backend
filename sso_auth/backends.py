import uuid
import jwt
from jwt import PyJWKClient
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.conf import settings

jwks_client = PyJWKClient(
    getattr(settings, "OIDC_OP_JWKS_ENDPOINT", ""),
    cache_jwk_set=True,
    lifespan=600,
    cache_keys=True,
    max_cached_keys=16,
)


class MyOIDCBackend(OIDCAuthenticationBackend):
    def get_token(self, payload):
        if settings.OIDC_USE_MOCK:
            return {
                "access_token": "mock_access_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "id_token": "mock_id_token",
            }
        return super().get_token(payload)

    def verify_token(self, token, **kwargs):
        if settings.OIDC_USE_MOCK:
            # In load-testing/mock mode, skip signature validation and return
            # minimal claims expected by downstream auth logic.
            return {
                "sub": "mock_sub",
                "email": "student_mock@mcmaster.ca",
                "preferred_username": "student_mock",
            }
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
        if settings.OIDC_USE_MOCK:
            uid = uuid.uuid4().hex[:8]
            return {
                "sub": f"mock_sub_{uid}",
                "email": f"student_{uid}@mcmaster.ca",
                "given_name": "Test",
                "family_name": "Student",
            }
        if payload is None:
            payload = self.verify_token(access_token)
        return payload or {}

    def verify_claims(self, claims):
        if not claims:
            return False
        has_identity = "sub" in claims or "oid" in claims
        has_contact = claims.get("email") or claims.get("preferred_username")
        return has_identity and bool(has_contact)

    def filter_users_by_claims(self, claims):
        email = claims.get("email")
        username = (
            claims.get("name")
            or claims.get("preferred_username")
            or claims.get("nickname")
        )

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
        username = claims.get("name") or claims.get("preferred_username")

        if not username and email:
            username = email.split("@")[0]

        if not email:
            username_clean = username.replace(" ", "_") if username else "user"
            email = f"{username_clean}@mcmaster.ca"

        user = self.UserModel.objects.create_user(username=username, email=email)
        self._set_user_flags(user, claims)
        return user

    def update_user(self, user, claims):
        name = claims.get("name")
        if name and user.username != name:
            user.username = name
            user.save()
        self._set_user_flags(user, claims)
        return user

    def _set_user_flags(self, user, claims):
        if settings.DEBUG:
            print(f"debug print - giving all perms to {user.email}")

        user.is_staff = True
        user.is_superuser = True
        user.save()
