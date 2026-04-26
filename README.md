# MacFAST Django backend

REST API for the MacFAST project built with the Django REST framework, deployed on the university's network at https://macfast.ca.

## Getting Started

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/McMaster-FAST/backend.git
    cd backend
    ```

2.  **Create and Activate Virtual Environment:**
    Using `uv`:

    ```bash
    uv venv
    source .venv/bin/activate
    ```

    (Or with standard `venv`: `python -m venv .venv` and `source .venv/bin/activate`)

3.  **Install Dependencies:**
    ```bash
    uv sync
    ```

## Configuration

The project uses a `.env` file for managing secrets and environment-specific settings. System environment variables take precedence over values loaded from `.env`.
The project uses a `.env` file for managing secrets and environment-specific settings. System environment variables take precedence over values loaded from `.env`.

1.  **Create your Environment File:**
    Copy the sample file to create your local environment file. This `.env` file is in `.gitignore` and should never be committed to source control.

    ```bash
    cp sample.env .env
    ```

2.  **Edit your `.env` File:**
    Open the `.env` file in your editor and fill in the required values. The comments in `sample.env` will guide you.

## Running the Server

1.  **Apply Database Migrations:**

    ```bash
    uv run manage.py migrate
    ```

2.  **Run the Development Server:**
    ```bash
    uv run manage.py runserver
    ```
    The server will start on `http://localhost:8000/`.

### Migration History Repair (one-off)

If you hit an error like:
`InconsistentMigrationHistory: analytics.0007 ... applied before analytics.0006 ...`,
run:

```bash
uv run manage.py repair_analytics_migration_history
uv run manage.py migrate
```

To preview without changing anything:

```bash
uv run manage.py repair_analytics_migration_history --dry-run
```

## Loading Mock Data

**If you are doing development and need mock data to test with you can run**

To load mock data only if the database is empty:

```
uv run manage.py load_fixtures
```

or to load all mock data unconditionally:

```
uv run manage.py loaddata mock/data.json
```

To unload mock data:

```
uv run manage.py unload_fixtures
```

## Health Check

You can test that the server is running correctly by hitting the API's health check "ping" endpoint.

**Endpoint:** `GET /api/core/ping/`

**Example using a Browser:**
With the server running, visit the following URL in your browser:
[http://localhost:8000/api/core/ping/](http://localhost:8000/api/core/ping/)

**Expected Response**

```
{
  "message": "pong"
}
```

## Running Tests

### Unit Tests

You can run the unit tests for the project by running the following command:

```
uv run pytest
```

### Load Testing

Use a separate Postgres database for load testing instead of the Django test DB.

1. Change the DATABASE_URL to use the loadtest DB:

```bash
source .env
export DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/mc-fast-load-test
```

2. Create the loadtest DB in the running Postgres Docker container (run once per machine):

```bash
docker compose exec db psql -U "${POSTGRES_USER}" -d postgres -c 'DROP DATABASE IF EXISTS "mc-fast-load-test";'
docker compose exec db psql -U "${POSTGRES_USER}" -d postgres -c 'CREATE DATABASE "mc-fast-load-test";'
```

3. Apply migrations to the loadtest DB:

```bash
uv run manage.py migrate
```

4. Restart the Django server with the new DATABASE_URL in a new terminal (if running):

```bash
source .env
export DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/mc-fast-load-test
uv run manage.py runserver
```

5. Create session pool for Locust:

```
uv run manage.py create_loadtest_sessions
```

6. Run Locust:

```
uv run locust -f load_tests/submit_answer_locustfile.py --host=http://localhost:8000
```