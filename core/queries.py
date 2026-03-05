from sso_auth.models import MacFastUser
from .models import Question, QuestionOption, TestSession, SavedForLater
from courses.models import UnitSubtopic
from analytics.models import UserTopicAbilityScore

import numpy as np

# A place for functions that fetch objects from the database


class QuestionBundle:
    def __init__(self, question, options, saved_for_later):
        self.question = question
        self.options = options
        self.saved_for_later = saved_for_later


def get_testsession_and_set_active(
    user: MacFastUser, subtopic: UnitSubtopic
) -> TestSession:
    test_session, _ = TestSession.objects.get_or_create(
        user=user,
        subtopic=subtopic,
    )
    set_user_active_subtopic(user, test_session.subtopic)
    return test_session


def set_user_active_subtopic(user: MacFastUser, subtopic: UnitSubtopic) -> None:
    # Premature/ unnecessary optimization?
    if user.active_subtopic != subtopic:
        user.active_subtopic = subtopic
        user.save()


def get_next_question_bundle(subtopic, user, test_session) -> QuestionBundle | None:
    user_score, _ = UserTopicAbilityScore.objects.get_or_create(
        user=user, unit_sub_topic=subtopic
    )

    skipped_questions = test_session.skipped_questions.values_list("id", flat=True)

    possible_questions = Question.objects.filter(
        subtopic=subtopic,
    ).exclude(id__in=skipped_questions)

    theta = float(user_score.score)

    # NOTE: If the load from searching all questions becomes too much we can set a range
    # to search first, and if no questions are found keep increasing it? Would that actually
    # make this more efficient?

    if not possible_questions.exists():
        return None

    # TODO: Choose questions randomly from the difficulty range stored in the test session
    next_question = max(
        possible_questions,
        key=lambda q: item_information(
            q.discrimination, q.difficulty, q.guessing, theta
        ),
    )
    test_session.current_question = next_question
    test_session.save()

    options = QuestionOption.objects.filter(question=next_question)
    saved_for_later = SavedForLater.objects.filter(user=user, question=next_question).exists()
    return QuestionBundle(next_question, options, saved_for_later)


def item_information(a, b, c, theta) -> float:
    # Avoid unsupported operation errors between different number types
    a, b, c, theta = map(float, (a, b, c, theta))

    p = c + (1 - c) / (1 + np.exp(-a * (theta - b)))
    q = 1 - p
    return (a**2) * ((q / (p * (1 - c))) * ((p - c) ** 2))
