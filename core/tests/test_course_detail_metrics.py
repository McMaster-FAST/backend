import pytest
from rest_framework import status
from rest_framework.test import APIClient

from analytics.models import QuestionAttempt
from core.models import Question
from courses.models import Course
from courses.models import Unit
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser

pytestmark = pytest.mark.django_db


def _create_attempt(
    user: MacFastUser,
    question: Question,
    *,
    answered_correctly: bool,
    skipped: bool = False,
) -> QuestionAttempt:
    return QuestionAttempt.objects.create(
        user=user,
        question=question,
        answered_correctly=answered_correctly,
        skipped=skipped,
        updated_ability_score=0,
        time_spent=1.0,
    )


def test_course_detail_includes_unit_progress(
    api_client: APIClient,
    user: MacFastUser,
    course: Course,
    unit: Unit,
    subtopic: UnitSubtopic,
    question: Question,
) -> None:
    user.is_staff = True
    user.save(update_fields=['is_staff'])

    second_question = Question.objects.create(
        subtopic=subtopic,
        serial_number='Q002',
        content='What is 3 + 3?',
    )
    inactive_question = Question.objects.create(
        subtopic=subtopic,
        serial_number='Q003',
        content='Inactive question',
        is_active=False,
    )
    other_unit = Unit.objects.create(course=course, name='Other Unit', number=2)
    other_subtopic = UnitSubtopic.objects.create(unit=other_unit, name='Other Subtopic')
    other_unit_question = Question.objects.create(
        subtopic=other_subtopic,
        serial_number='Q004',
        content='Other unit question',
    )

    _create_attempt(user, question, answered_correctly=True)
    _create_attempt(user, question, answered_correctly=True)
    _create_attempt(user, second_question, answered_correctly=False)
    _create_attempt(user, second_question, answered_correctly=True, skipped=True)
    _create_attempt(user, inactive_question, answered_correctly=True)
    _create_attempt(user, other_unit_question, answered_correctly=True)

    response = api_client.get(f'/api/courses/{course.code}/')

    assert response.status_code == status.HTTP_200_OK

    unit_data = response.data['units'][0]
    assert unit_data['public_id'] == str(unit.public_id)
    assert unit_data['correct_questions'] == 1
    assert unit_data['total_questions'] == 2
    assert unit_data['completion_percentage'] == 50.0


def test_course_list_includes_course_progress(
    api_client: APIClient,
    user: MacFastUser,
    course: Course,
    unit: Unit,
    subtopic: UnitSubtopic,
    question: Question,
) -> None:
    user.is_staff = True
    user.save(update_fields=['is_staff'])

    second_question = Question.objects.create(
        subtopic=subtopic,
        serial_number='Q100',
        content='Another active question',
    )
    Question.objects.create(
        subtopic=subtopic,
        serial_number='Q101',
        content='Inactive question',
        is_active=False,
    )

    _create_attempt(user, question, answered_correctly=True)
    _create_attempt(user, second_question, answered_correctly=False)
    _create_attempt(user, second_question, answered_correctly=True, skipped=True)

    response = api_client.get('/api/courses/')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1

    course_data = response.data[0]
    assert course_data['public_id'] == str(course.public_id)
    assert course_data['correct_questions'] == 1
    assert course_data['total_questions'] == 2
