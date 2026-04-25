import os

# Set required environment variables before importing main settings
os.environ.setdefault('ENTRA_TENANT_ID', 'test-tenant-id')
os.environ.setdefault('OIDC_RP_CLIENT_ID', 'test-client-id')
os.environ.setdefault('OIDC_RP_CLIENT_SECRET', 'test-client-secret')
# Use SQLite for tests so Docker PostgreSQL is not required
os.environ['DATABASE_URL'] = 'sqlite:///test_db.sqlite3'

from MacFAST.settings import *  # noqa: E402, F401, F403
