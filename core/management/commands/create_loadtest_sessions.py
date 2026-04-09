"""
Management command to create a session pool for Locust load testing.

Creates 100 test users, each with their own question data and a valid
Django session. Outputs session_pool.json for Locust to consume.

Usage:
    python manage.py create_loadtest_sessions
    python manage.py create_loadtest_sessions --users 50 --output /tmp/pool.json
"""

import json
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from django.core.management.base import BaseCommand
from django.core.management.base import CommandParser
from django.middleware.csrf import get_token
from django.test import RequestFactory

from core.models import Question
from core.models import QuestionOption
from core.models import TestingParameters
from courses.models import Course
from courses.models import Unit
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser

DEFAULT_OUTPUT_PATH = Path(settings.BASE_DIR) / 'loadtests' / 'session_pool.json'
DEFAULT_NUM_USERS = 100


class Command(BaseCommand):
    help = 'Create test users and session pool for Locust load testing'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--users',
            type=int,
            default=DEFAULT_NUM_USERS,
            help=f'Number of test users to create (default: {DEFAULT_NUM_USERS})',
        )
        parser.add_argument(
            '--output',
            type=str,
            default=str(DEFAULT_OUTPUT_PATH),
            help=f'Output path for session_pool.json (default: {DEFAULT_OUTPUT_PATH})',
        )

    def handle(self, *args: object, **options: object) -> None:
        num_users: int = options['users']
        output_path = Path(options['output'])

        self.stdout.write(f'Creating {num_users} load test users...')

        # Create shared course infrastructure
        course = self._get_or_create_course()
        self._get_or_create_testing_params(course)
        unit = self._get_or_create_unit(course)

        session_pool: list[dict[str, str]] = []
        request_factory = RequestFactory()

        for i in range(num_users):
            username = f'loadtest_user_{i}'

            # Create user
            user = self._get_or_create_user(username)

            # Create a unique subtopic and question for this user
            subtopic = UnitSubtopic.objects.get_or_create(
                unit=unit,
                name=f'Loadtest Subtopic {i}',
            )[0]

            question, option = self._get_or_create_question(subtopic, i)

            # Create Django session for this user
            session = SessionStore()
            session['_auth_user_id'] = str(user.pk)
            session['_auth_user_backend'] = settings.AUTHENTICATION_BACKENDS[0]
            session['_auth_user_hash'] = user.get_session_auth_hash()
            session.create()

            # Generate CSRF token
            request = request_factory.get('/')
            request.META['CSRF_COOKIE_USED'] = True
            csrf_token = get_token(request)

            session_pool.append(
                {
                    'session_key': session.session_key,
                    'csrf_token': csrf_token,
                    'question_id': str(question.public_id),
                    'selected_option_id': str(option.public_id),
                    'username': username,
                }
            )

            if (i + 1) % 25 == 0:
                self.stdout.write(f'  Created {i + 1}/{num_users} users...')

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(session_pool, f, indent=2)

        self.stdout.write(
            self.style.SUCCESS(
                f'Session pool with {num_users} users written to {output_path}'
            )
        )

    def _get_or_create_course(self) -> Course:
        course, _ = Course.objects.get_or_create(
            code='LOADTEST101',
            defaults={
                'name': 'Load Test Course',
                'year': 2025,
                'semester': Course.SemesterChoices.FALL,
            },
        )
        return course

    def _get_or_create_testing_params(self, course: Course) -> TestingParameters:
        params, _ = TestingParameters.objects.get_or_create(
            course=course,
            defaults={
                'warmpup_length': 3,
                'max_skips': 3,
                'skip_readmit_delay': 5,
                'max_question_repetitions': 3,
            },
        )
        return params

    def _get_or_create_unit(self, course: Course) -> Unit:
        unit, _ = Unit.objects.get_or_create(
            course=course,
            number=1,
            defaults={'name': 'Load Test Unit'},
        )
        return unit

    def _get_or_create_user(self, username: str) -> MacFastUser:
        user, created = MacFastUser.objects.get_or_create(
            username=username,
            defaults={'password': 'loadtest_not_for_production'},
        )
        if created:
            user.set_password('loadtest_not_for_production')
            user.save()
        return user

    def _get_or_create_question(
        self, subtopic: UnitSubtopic, index: int
    ) -> tuple[Question, QuestionOption]:
        serial = f'LOADTEST-Q{index:04d}'
        question, _ = Question.objects.get_or_create(
            serial_number=serial,
            defaults={
                'subtopic': subtopic,
                'content': f'Load test question {index}',
                'difficulty': Decimal(str(round(-1.0 + (index % 20) * 0.1, 1))),
            },
        )
        option, _ = QuestionOption.objects.get_or_create(
            question=question,
            is_answer=True,
            defaults={'content': 'Correct answer'},
        )
        return question, option
