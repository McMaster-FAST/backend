import uuid
from django.http import JsonResponse


def mock_token_endpoint(request):
    # Returns a fake access token instantly
    return JsonResponse(
        {
            "access_token": "mock_access_token_12345",
            "token_type": "Bearer",
            "expires_in": 3600,
            "id_token": "mock_id_token",
        }
    )


def mock_userinfo_endpoint(request):
    # Returns fake McMaster student claims.
    # The random UUID ensures Locust creates a new user in your DB for every concurrent request.
    return JsonResponse(
        {
            "sub": f"mock_sub_{uuid.uuid4().hex[:8]}",
            "email": f"student_{uuid.uuid4().hex[:8]}@mcmaster.ca",
            "given_name": "Test",
            "family_name": "Student",
        }
    )
