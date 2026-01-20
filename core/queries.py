from .views.adaptive_test.submit_test_answer import item_information
from .models import Question, QuestionOption, TestSession
from courses.models import UnitSubtopic
from analytics.models import UserTopicAbilityScore

import numpy as np

# A place for functions that fetch objects from the database


class QuestionBundle:
    def __init__(self, question, options):
        self.question = question
        self.options = options


def get_next_question_bundle(
    course_code, unit_name, subtopic_name, user, difficulty_range
):
    subtopic = UnitSubtopic.objects.get(
        unit__course__code=course_code,
        unit__name=unit_name,
        name=subtopic_name,
    )

    user_score, _ = UserTopicAbilityScore.objects.get_or_create(
        user=user, unit_sub_topic=subtopic
    )
    theta = user_score.score

    test_session = TestSession.objects.filter(
        user=user, course=subtopic.unit.course
    ).first()
    if not test_session:
        test_session = TestSession.objects.create(
            user=user,
            course=subtopic.unit.course,
            subtopic=subtopic,
            current_question=None,
        )
        test_session.excluded_questions.set([])
    excluded_questions = test_session.excluded_questions.values_list(
        "id", flat=True
    )

    possible_questions = Question.objects.filter(
        subtopic=subtopic,
        difficulty__gte=theta - difficulty_range,
        difficulty__lte=theta + difficulty_range,
    ).exclude(id__in=excluded_questions)

    if not possible_questions.exists():
        return None

    next_question = max(
        possible_questions,
        key=lambda q: item_information(
            q.discrimination, q.difficulty, q.guessing, theta
        ),
    )
    test_session.current_question = next_question
    test_session.save()

    options = QuestionOption.objects.filter(question=next_question)
    return QuestionBundle(next_question, options)


def item_information(a, b, c, theta):
    p = c + (1 - c) / (1 + np.exp(-a * (theta - b)))
    q = 1 - p
    return (a**2) * ((q / (p * (1 - c))) * ((p - c) ** 2))
