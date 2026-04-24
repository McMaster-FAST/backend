"""
Locust load test for the submit-answer endpoint.

Simulates 100 concurrent users submitting answers to verify that each
request completes within 2 seconds under peak load.

Prerequisites:
    1. Django server running against Postgres (recommended):
       python manage.py runserver

    2. Session pool generated:
       python manage.py create_loadtest_sessions

Usage:
    locust -f load_tests/submit_answer_locustfile.py --host=http://localhost:8000

    Then open http://localhost:8089 and configure:
    - Number of users: 100
    - Spawn rate: 10
    - Host: http://localhost:8000

Docker mode:
    1. Start services:
       docker compose up -d

    2. Run migrations (first time only):
       docker compose exec web uv run python manage.py migrate

    3. Generate session pool:
       docker compose exec web uv run python manage.py create_loadtest_sessions

    4. Run Locust from host:
       locust -f load_tests/submit_answer_locustfile.py --host=http://localhost:8000

Headless mode:
    locust -f load_tests/submit_answer_locustfile.py \
        --host=http://localhost:8000 \
        --users=100 \
        --spawn-rate=10 \
        --run-time=60s \
        --headless
"""

import json
import logging
import threading
from pathlib import Path

from locust import HttpUser
from locust import between
from locust import events
from locust import task

logger = logging.getLogger(__name__)

SESSION_POOL_PATH = Path(__file__).parent / 'session_pool.json'

_pool_lock = threading.Lock()
_session_pool: list[dict[str, str]] = []


@events.init.add_listener
def on_locust_init(environment: object, **kwargs: object) -> None:
    global _session_pool

    if not SESSION_POOL_PATH.exists():
        raise FileNotFoundError(
            f'Session pool not found at {SESSION_POOL_PATH}. '
            f"Run 'python manage.py create_loadtest_sessions' first."
        )

    with open(SESSION_POOL_PATH) as f:
        _session_pool = json.load(f)

    logger.info('Loaded %d sessions from %s', len(_session_pool), SESSION_POOL_PATH)


def _acquire_session() -> dict[str, str] | None:
    with _pool_lock:
        if _session_pool:
            return _session_pool.pop()
    return None


class SubmitAnswerUser(HttpUser):
    wait_time = between(0.5, 1.5)

    def on_start(self) -> None:
        session_info = _acquire_session()
        if session_info is None:
            logger.warning(
                'Session pool exhausted. '
                'This virtual user has no session and will not send requests. '
                'Increase pool size with: python manage.py create_loadtest_sessions --users <N>'
            )
            self._has_session = False
            return

        self._has_session = True
        self._question_id: str = session_info['question_id']
        self._selected_option_id: str = session_info['selected_option_id']
        self._csrf_token: str = session_info['csrf_token']

        self.client.cookies.set('sessionid', session_info['session_key'])
        self.client.cookies.set('csrftoken', self._csrf_token)

    @task
    def submit_answer(self) -> None:
        if not self._has_session:
            return

        response = self.client.post(
            '/api/core/adaptive-test/submit-answer/',
            json={
                'question_id': self._question_id,
                'selected_option_id': self._selected_option_id,
            },
            headers={
                'X-CSRFToken': self._csrf_token,
                'Content-Type': 'application/json',
            },
        )

        if response.status_code != 200:
            logger.error(
                'submit-answer failed: status=%d body=%s',
                response.status_code,
                response.text[:200],
            )
