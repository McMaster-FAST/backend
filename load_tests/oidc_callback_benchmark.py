import urllib.parse
import random
from locust import HttpUser, task, between


class MozillaOIDCLester(HttpUser):
    wait_time = between(1, 2)

    @task
    def full_login_flow(self):
        # Initiate Login
        # allow_redirects=False prevents Locust from actually trying to visit the fake McMaster login screen
        response = self.client.get(
            "/oidc/authenticate/", allow_redirects=False, name="1. Init OIDC"
        )

        if response.status_code != 302:
            response.failure("Failed to initiate OIDC login")
            return

        # Extract the 'state' variable from the redirect URL
        redirect_url = response.headers.get("Location")
        parsed_url = urllib.parse.urlparse(redirect_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        state = query_params.get("state", [None])[0]

        if not state:
            response.failure("Could not extract state parameter")
            return

        # Simulate the Callback
        random_id = random.randint(1000, 9999)
        callback_url = f"/oidc/callback/?code=fake_code_{random_id}&state={state}"

        with self.client.get(
            callback_url, catch_response=True, name="2. OIDC Callback Processing"
        ) as callback_response:
            processing_time = callback_response.elapsed.total_seconds()

            if callback_response.status_code not in [200, 302]:
                callback_response.failure(
                    f"Server error! Status: {callback_response.status_code}"
                )
            elif processing_time > 2.0:
                callback_response.failure(
                    f"SLA Violation: Took {processing_time:.3f} seconds"
                )
            else:
                callback_response.success()
