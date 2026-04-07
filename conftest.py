import pytest
from rest_framework.test import APIClient

from core.models import Question
from core.models import QuestionOption
from courses.models import Course
from courses.models import Unit
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser


@pytest.fixture
def user(db: None) -> MacFastUser:
    return MacFastUser.objects.create_user(
        username='testuser',
        password='testpassword123',
    )


@pytest.fixture
def api_client(user: MacFastUser) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def unauthenticated_client() -> APIClient:
    return APIClient()


@pytest.fixture
def course(db: None) -> Course:
    return Course.objects.create(
        name='Test Course',
        code='TEST101',
        year=2026,
        semester='FALL',
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
        content='What is 2 + 2?',
    )


@pytest.fixture
def question_option(question: Question) -> QuestionOption:
    return QuestionOption.objects.create(
        question=question,
        content='4',
        is_answer=True,
    )
