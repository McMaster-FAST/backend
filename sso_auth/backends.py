from mozilla_django_oidc.auth import OIDCAuthenticationBackend
import json
import traceback

ROLES_CLAIM_URL = "https://chemfast.ca/roles"


class MyOIDCBackend(OIDCAuthenticationBackend):

    def verify_claims(self, claims):
        """
        Verify that we have at least a Subject ID.
        We do NOT call super() here because super() fails if email is missing.
        """
        print("\n" + "=" * 30)
        print("--- DEBUG: verify_claims ---")
        print(json.dumps(claims, indent=2))
        print("=" * 30 + "\n")

        # If 'sub' (Subject ID) is present, the token is valid enough for us.
        # We skip the email check.
        return "sub" in claims

    def filter_users_by_claims(self, claims):
        """
        Attempt to find an existing user.
        Standard logic tries email. We will try nickname (username) as a fallback.
        """
        email = claims.get("email")
        username = claims.get("nickname") or claims.get("preferred_username")

        # 1. Try finding by email (if we have one)
        if email:
            users = self.UserModel.objects.filter(email__iexact=email)
            if users.exists():
                print(f"--- DEBUG: Found user by email: {email} ---")
                return users

        # 2. Try finding by username (if email search failed or no email)
        if username:
            users = self.UserModel.objects.filter(username__iexact=username)
            if users.exists():
                print(f"--- DEBUG: Found user by username: {username} ---")
                return users

        return self.UserModel.objects.none()

    def create_user(self, claims):
        print("--- DEBUG: create_user (NEW USER) ---")

        email = claims.get("email")
        # Get username from nickname (GitHub) or preferred_username
        username = claims.get("nickname") or claims.get("preferred_username")

        # FALLBACK 1: If no username, use part of the email
        if not username and email:
            username = email.split("@")[0]

        # FALLBACK 2: If no email (GitHub Private Mode), generate a dummy one
        if not email:
            # We create a fake email using the username to satisfy Django requirements
            print("--- WARNING: No email in claims. Generating placeholder. ---")
            email = f"{username}@no-email.chemfast.ca"

        # Create the user
        user = self.UserModel.objects.create_user(username=username, email=email)

        self._set_user_flags(user, claims)
        return user

    def update_user(self, user, claims):
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
