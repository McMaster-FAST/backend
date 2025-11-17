# In sso_auth/backends.py

from mozilla_django_oidc.auth import OIDCAuthenticationBackend
import json
import traceback  # We'll use this to see the full error

# This URL MUST EXACTLY MATCH the 'namespace' you defined in your Auth0 Action.
ROLES_CLAIM_URL = "https://chemfast.ca/roles"


class MyOIDCBackend(OIDCAuthenticationBackend):

    def verify_claims(self, claims):
        """
        This is the method that is failing. We are overriding it
        to print the claims data *before* it fails.
        """

        # --- START NUCLEAR DEBUG ---
        print("\n" + "=" * 30)
        print("--- DEBUG: verify_claims (THIS IS THE SPOT!) ---")
        print("Claims received from token. We will compare this to settings.py:")
        print(json.dumps(claims, indent=2))
        print("=" * 30 + "\n")
        # --- END NUCLEAR DEBUG ---

        try:
            # Run the original verification from the library
            return super().verify_claims(claims)
        except Exception as e:
            # --- START NUCLEAR DEBUG ---
            print("\n" + "!" * 30)
            print(f"--- VERIFICATION FAILED! Error: {e}")
            print("Traceback:")
            traceback.print_exc()
            print("!" * 30 + "\n")
            # --- END NUCLEAR DEBUG ---
            raise  # Re-raise the exception so the login fails as normal

    # --- The functions below are NOT being reached yet, ---
    # --- but we leave them here for when verify_claims works. ---

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

    def create_user(self, claims):
        print("--- DEBUG: create_user (NEW USER) ---")
        user = super().create_user(claims)
        self._set_user_flags(user, claims)
        return user

    def update_user(self, user, claims):
        print("--- DEBUG: update_user (EXISTING USER) ---")
        user = super().update_user(user, claims)
        self._set_user_flags(user, claims)
        return user
