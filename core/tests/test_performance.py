"""
Performance regression tests for user data compilation.

These tests run against in-memory SQLite (settings_test.py) and are intended
for regression detection only. Threshold violations indicate a potential
performance degradation, not a production-grade acceptance failure.

For production acceptance testing, use Locust against a Postgres environment.

Run these tests manually:
    pytest -m performance -v

Exclude from CI:
    pytest -m "not performance"
"""

import time
from decimal import Decimal

import pytest

from analytics.models import QuestionAttempt
from core.cat_methods.rasch_model import RaschModel
from core.models import Question
from core.models import QuestionOption
from core.models import TestingParameters
from core.queries.question_queries import add_response
from courses.models import Course
from courses.models import Unit
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser

# ---------------------------------------------------------------------------
# Fixtures (perf_ prefix to avoid collision with conftest.py)
# ---------------------------------------------------------------------------


@pytest.fixture
def perf_course(db: None) -> Course:
    return Course.objects.create(
        name='Perf Course',
        code='PERF101',
        year=2025,
        semester=Course.SemesterChoices.FALL,
    )


@pytest.fixture
def perf_testing_params(perf_course: Course) -> TestingParameters:
    return TestingParameters.objects.create(
        course=perf_course,
        warmpup_length=3,
        max_skips=3,
        skip_readmit_delay=5,
        max_question_repetitions=3,
    )


@pytest.fixture
def perf_unit(perf_course: Course) -> Unit:
    return Unit.objects.create(
        course=perf_course,
        name='Perf Unit',
        number=1,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_subtopic(unit: Unit, name: str) -> UnitSubtopic:
    return UnitSubtopic.objects.create(unit=unit, name=name)


def _create_question_with_options(
    subtopic: UnitSubtopic,
    serial: str,
    difficulty: float,
) -> tuple[Question, QuestionOption, QuestionOption]:
    question = Question.objects.create(
        subtopic=subtopic,
        serial_number=serial,
        content=f'Question {serial}',
        difficulty=Decimal(str(difficulty)),
    )
    correct = QuestionOption.objects.create(
        question=question,
        content='Correct',
        is_answer=True,
    )
    wrong = QuestionOption.objects.create(
        question=question,
        content='Wrong',
        is_answer=False,
    )
    return question, correct, wrong


# ---------------------------------------------------------------------------
# add_response() latency
# ---------------------------------------------------------------------------


@pytest.mark.performance
@pytest.mark.django_db
class TestAddResponseLatency:
    THRESHOLD_SECONDS = 2.0

    def test_single_attempt_within_threshold(
        self,
        perf_unit: Unit,
        perf_testing_params: TestingParameters,
    ) -> None:
        user = MacFastUser.objects.create_user(
            username='perf_user_single',
            password='testpass',
        )
        subtopic = _create_subtopic(perf_unit, 'Single Attempt Subtopic')
        question, correct, _ = _create_question_with_options(subtopic, 'PERF-S001', 0.0)

        start = time.perf_counter()
        add_response(user, question, correct)
        elapsed = time.perf_counter() - start

        print(f"\n  add_response() single attempt: {elapsed:.4f}s (threshold: {self.THRESHOLD_SECONDS}s)")
        assert elapsed < self.THRESHOLD_SECONDS, (
            f'add_response() took {elapsed:.3f}s, '
            f'exceeding {self.THRESHOLD_SECONDS}s threshold'
        )

    def test_attempt_with_prior_history_within_threshold(
        self,
        perf_unit: Unit,
        perf_testing_params: TestingParameters,
    ) -> None:
        user = MacFastUser.objects.create_user(
            username='perf_user_history',
            password='testpass',
        )
        subtopic = _create_subtopic(perf_unit, 'History Subtopic')

        # Build up 10 prior attempts so the user is past warmup
        for i in range(10):
            q, correct, wrong = _create_question_with_options(
                subtopic, f'PERF-H{i:03d}', round(-1.0 + i * 0.2, 1)
            )
            option = correct if i % 2 == 0 else wrong
            add_response(user, q, option)

        # Measure the 11th attempt
        target_q, target_correct, _ = _create_question_with_options(
            subtopic, 'PERF-H-TARGET', 0.5
        )

        start = time.perf_counter()
        add_response(user, target_q, target_correct)
        elapsed = time.perf_counter() - start

        print(f"\n  add_response() with 10 prior attempts: {elapsed:.4f}s (threshold: {self.THRESHOLD_SECONDS}s)")
        assert elapsed < self.THRESHOLD_SECONDS, (
            f'add_response() with history took {elapsed:.3f}s, '
            f'exceeding {self.THRESHOLD_SECONDS}s threshold'
        )


# ---------------------------------------------------------------------------
# RaschModel.compute_ability() latency
# ---------------------------------------------------------------------------


@pytest.mark.performance
@pytest.mark.django_db
class TestComputeAbilityLatency:
    THRESHOLD_SECONDS = 1.0
    NUM_ITERATIONS = 50

    def test_compute_ability_average_under_threshold(
        self,
        perf_unit: Unit,
        perf_testing_params: TestingParameters,
    ) -> None:
        elapsed_times: list[float] = []

        for i in range(self.NUM_ITERATIONS):
            user = MacFastUser.objects.create_user(
                username=f'perf_irt_user_{i}',
                password='testpass',
            )
            subtopic = _create_subtopic(perf_unit, f'IRT Subtopic {i}')

            # Vary the number of prior attempts (0 to 9) and difficulty spread
            num_prior = i % 10
            for j in range(num_prior):
                q, _, _ = _create_question_with_options(
                    subtopic,
                    f'PERF-IRT-{i}-{j}',
                    round(-2.0 + j * 0.5, 1),
                )
                answered_correctly = (i + j) % 3 != 0
                QuestionAttempt.objects.create(
                    question=q,
                    user=user,
                    answered_correctly=answered_correctly,
                    skipped=False,
                    updated_ability_score=Decimal('0.0'),
                    time_spent=1.0,
                )

            start = time.perf_counter()
            RaschModel.compute_ability(user, subtopic)
            elapsed = time.perf_counter() - start

            elapsed_times.append(elapsed)

        average_elapsed = sum(elapsed_times) / len(elapsed_times)
        max_elapsed = max(elapsed_times)

        print(
            f"\n  compute_ability() over {self.NUM_ITERATIONS} iterations: "
            f"avg={average_elapsed:.4f}s, max={max_elapsed:.4f}s "
            f"(threshold: avg < {self.THRESHOLD_SECONDS}s)"
        )
        assert average_elapsed < self.THRESHOLD_SECONDS, (
            f'compute_ability() average {average_elapsed:.4f}s '
            f'exceeds {self.THRESHOLD_SECONDS}s threshold '
            f'(max single run: {max_elapsed:.4f}s)'
        )
