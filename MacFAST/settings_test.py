import os

# Provide defaults for OIDC environment variables that are required by
# settings.py but not needed for unit tests.
os.environ.setdefault('ENTRA_TENANT_ID', 'test-tenant-id')
os.environ.setdefault('OIDC_RP_CLIENT_ID', 'test-client-id')
os.environ.setdefault('OIDC_RP_CLIENT_SECRET', 'test-client-secret')

import MacFAST.settings as _base_settings  # noqa: E402

for _name in dir(_base_settings):
    if _name.isupper():
        globals()[_name] = getattr(_base_settings, _name)

# Use in-memory SQLite for fast test execution
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Keep test uploads out of the repo `media/` folder.
# This path gets cleaned up by a pytest session fixture.
BASE_DIR = _base_settings.BASE_DIR
MEDIA_ROOT = BASE_DIR / ".test_media"
