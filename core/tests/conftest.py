import pytest

from core.models import Question
from core.models import QuestionOption
from core.models import TestingParameters
from courses.models import Course
from courses.models import Unit
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser


@pytest.fixture
def user(db: None) -> MacFastUser:
    return MacFastUser.objects.create_user(
        username='testuser',
        password='testpass123',
    )


@pytest.fixture
def course(db: None) -> Course:
    return Course.objects.create(
        name='Test Course',
        code='TEST101',
        year=2025,
        semester=Course.SemesterChoices.FALL,
    )


@pytest.fixture
def unit(course: Course) -> Unit:
    return Unit.objects.create(
        course=course,
        name='Test Unit',
        number=1,
    )


@pytest.fixture
def subtopic(unit: Unit) -> UnitSubtopic:
    return UnitSubtopic.objects.create(
        unit=unit,
        name='Test Subtopic',
    )


@pytest.fixture
def question(subtopic: UnitSubtopic) -> Question:
    return Question.objects.create(
        subtopic=subtopic,
        serial_number='Q001',
        content='What is 1+1?',
        difficulty=0.0,
    )


@pytest.fixture
def correct_option(question: Question) -> QuestionOption:
    return QuestionOption.objects.create(
        question=question,
        content='2',
        is_answer=True,
    )


@pytest.fixture
def wrong_option(question: Question) -> QuestionOption:
    return QuestionOption.objects.create(
        question=question,
        content='3',
        is_answer=False,
    )


@pytest.fixture
def testing_parameters(course: Course) -> TestingParameters:
    return TestingParameters.objects.create(
        course=course,
        warmpup_length=3,
        max_skips=3,
        skip_readmit_delay=5,
        max_question_repetitions=3,
    )
