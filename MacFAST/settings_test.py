import os

# Provide defaults for OIDC environment variables that are required by
# settings.py but not needed for unit tests.
os.environ.setdefault('ENTRA_TENANT_ID', 'test-tenant-id')
os.environ.setdefault('OIDC_RP_CLIENT_ID', 'test-client-id')
os.environ.setdefault('OIDC_RP_CLIENT_SECRET', 'test-client-secret')

from MacFAST.settings import *  # noqa: E402, F401, F403

# Use in-memory SQLite for fast test execution
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
