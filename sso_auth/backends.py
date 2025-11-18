from mozilla_django_oidc.auth import OIDCAuthenticationBackend
import json
import traceback

ROLES_CLAIM_URL = "https://chemfast.ca/roles"


class MyOIDCBackend(OIDCAuthenticationBackend):

    def verify_claims(self, claims):
        # ... Your existing debug logic ...
        print("\n" + "=" * 30)
        print("--- DEBUG: verify_claims ---")
        print(json.dumps(claims, indent=2))
        print("=" * 30 + "\n")

        return super().verify_claims(claims)

    def create_user(self, claims):
        """
        Create the user using the username from claims (nickname)
        instead of the default hash/email logic.
        """
        print("--- DEBUG: create_user (NEW USER) ---")

        # 1. Get the email
        email = claims.get("email")

        # 2. Get the username.
        # Auth0/GitHub usually puts the username in 'nickname'.
        # Standard OIDC uses 'preferred_username'. We try both.
        username = claims.get("nickname") or claims.get("preferred_username")

        # Fallback: If no username exists, split the email
        if not username:
            username = email.split("@")[0]

        # 3. Create the user instance directly using your Custom User Model
        # Note: We use self.UserModel to ensure we use MacFastUser
        user = self.UserModel.objects.create_user(username=username, email=email)

        # 4. Set permissions
        self._set_user_flags(user, claims)

        return user

    def update_user(self, user, claims):
        print("--- DEBUG: update_user (EXISTING USER) ---")

        # Set permissions on every login to keep them synced
        self._set_user_flags(user, claims)

        return user

    def _set_user_flags(self, user, claims):
        roles = claims.get(ROLES_CLAIM_URL, [])

        # Reset flags first
        user.is_staff = False
        user.is_superuser = False

        if "admin" in roles:
            user.is_staff = True
            user.is_superuser = True
        elif "staff" in roles:
            user.is_staff = True

        user.save()
