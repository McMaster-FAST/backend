# MacFAST Django backend

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

The project uses a `.env` file for managing secrets and environment-specific settings, system environment variables will take precendence over .env variables.

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

<!-- 2.  **Load Initial Data (Optional):**

    If your database is empty, you can load initial fixtures (sample courses and questions):

    ```bash
    uv run python manage.py load_fixtures
    ```

    This command automatically checks if the database is empty and only loads fixtures if needed. -->

3.  **Run the Development Server:**
    ```bash
    uv run manage.py runserver
    ```
    The server will start on `http://localhost:8000/`.

## Loading Mock Data

**If you are doing development and need mock data to test with you can run**

    ```
    uv run manage.py loaddata mock/data.json
    ```

## Testing the API

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
