from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from analytics.models import CourseXP
from analytics.models import QuestionAttempt
from analytics.models import UserTopicAbilityScore
from core.models import AdaptiveTestQuestionMetric
from core.models import Question
from core.models import QuestionOption
from core.models import TestingParameters
from core.queries.question_queries import TooManySkipsException
from core.queries.question_queries import add_response
from courses.models import Course
from courses.models import Unit
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser


@pytest.mark.django_db
class TestAddResponseCreatesQuestionAttempt:
    """Tests for QuestionAttempt creation via add_response()."""

    def test_correct_answer_creates_attempt_with_expected_fields(
        self,
        user: MacFastUser,
        question: Question,
        correct_option: QuestionOption,
        testing_parameters: TestingParameters,
    ) -> None:
        """When a correct answer is submitted, QuestionAttempt should record
        the correct user, question, answered_correctly=True, skipped=False,
        and time_spent."""
        add_response(user, question, correct_option, time_spent=5.0)

        attempt = QuestionAttempt.objects.get(user=user, question=question)
        assert attempt.answered_correctly is True
        assert attempt.skipped is False
        assert attempt.time_spent == 5.0
        assert attempt.timestamp is not None
        assert attempt.updated_ability_score is not None

    def test_wrong_answer_creates_attempt_with_incorrect_flag(
        self,
        user: MacFastUser,
        question: Question,
        wrong_option: QuestionOption,
        testing_parameters: TestingParameters,
    ) -> None:
        """When a wrong answer is submitted, answered_correctly should be False."""
        add_response(user, question, wrong_option, time_spent=3.0)

        attempt = QuestionAttempt.objects.get(user=user, question=question)
        assert attempt.answered_correctly is False
        assert attempt.skipped is False

    def test_skip_creates_attempt_with_skipped_flag(
        self,
        user: MacFastUser,
        question: Question,
        testing_parameters: TestingParameters,
    ) -> None:
        """When selected_option is None, the attempt should be marked as skipped."""
        add_response(user, question, None, time_spent=0.0)

        attempt = QuestionAttempt.objects.get(user=user, question=question)
        assert attempt.skipped is True
        assert attempt.answered_correctly is False


@pytest.mark.django_db
class TestAddResponseMultipleAttempts:
    """Tests for recording multiple attempts."""

    def test_multiple_attempts_are_recorded(
        self,
        user: MacFastUser,
        question: Question,
        correct_option: QuestionOption,
        wrong_option: QuestionOption,
        testing_parameters: TestingParameters,
    ) -> None:
        """Two calls to add_response should create two QuestionAttempt records."""
        add_response(user, question, correct_option)
        add_response(user, question, wrong_option)

        count = QuestionAttempt.objects.filter(user=user, question=question).count()
        assert count == 2


@pytest.mark.django_db
class TestAddResponseXP:
    """Tests for XP awarding via add_response()."""

    def test_correct_answer_awards_xp_within_clamp_range(
        self,
        user: MacFastUser,
        question: Question,
        correct_option: QuestionOption,
        testing_parameters: TestingParameters,
    ) -> None:
        """A correct answer should award XP clamped to [5, 15]."""
        add_response(user, question, correct_option)

        xp_record = CourseXP.objects.get(
            user=user, course=question.subtopic.unit.course
        )
        assert 5 <= xp_record.total_xp <= 15

    def test_wrong_answer_does_not_award_xp(
        self,
        user: MacFastUser,
        question: Question,
        wrong_option: QuestionOption,
        testing_parameters: TestingParameters,
    ) -> None:
        """An incorrect answer should not change total_xp."""
        add_response(user, question, wrong_option)

        xp_exists = CourseXP.objects.filter(
            user=user, course=question.subtopic.unit.course
        ).exists()
        if xp_exists:
            xp_record = CourseXP.objects.get(
                user=user, course=question.subtopic.unit.course
            )
            assert xp_record.total_xp == 0
        # If no CourseXP record exists, that also means no XP was awarded.


@pytest.mark.django_db
class TestAddResponseAbilityClamp:
    """Tests for ability score clamping in add_response()."""

    def test_ability_score_clamped_to_upper_bound(
        self,
        user: MacFastUser,
        question: Question,
        correct_option: QuestionOption,
        testing_parameters: TestingParameters,
    ) -> None:
        """When compute_ability returns a value > 3, updated_ability_score
        should be clamped to 3."""
        mock_model = MagicMock()
        mock_model.compute_ability.return_value = (5.0, 1.0)

        add_response(user, question, correct_option, model=mock_model)

        attempt = QuestionAttempt.objects.get(user=user, question=question)
        assert float(attempt.updated_ability_score) == 3.0

    def test_ability_score_clamped_to_lower_bound(
        self,
        user: MacFastUser,
        question: Question,
        correct_option: QuestionOption,
        testing_parameters: TestingParameters,
    ) -> None:
        """When compute_ability returns a value < -3, updated_ability_score
        should be clamped to -3."""
        mock_model = MagicMock()
        mock_model.compute_ability.return_value = (-5.0, 1.0)

        add_response(user, question, correct_option, model=mock_model)

        attempt = QuestionAttempt.objects.get(user=user, question=question)
        assert float(attempt.updated_ability_score) == -3.0


@pytest.mark.django_db
class TestAddResponseTooManySkips:
    """Tests for TooManySkipsException and rollback."""

    def test_too_many_skips_raises_exception(
        self,
        user: MacFastUser,
        question: Question,
        testing_parameters: TestingParameters,
    ) -> None:
        """When a question has been skipped max_skips times, the next skip
        should raise TooManySkipsException."""
        # Build up skips to reach the limit
        metric, _ = AdaptiveTestQuestionMetric.objects.get_or_create(
            user=user, question=question
        )
        metric.skips_since_last_answer = testing_parameters.max_skips
        metric.save()

        with pytest.raises(TooManySkipsException):
            add_response(user, question, None)

    def test_too_many_skips_does_not_create_attempt(
        self,
        user: MacFastUser,
        question: Question,
        testing_parameters: TestingParameters,
    ) -> None:
        """When TooManySkipsException is raised, no new QuestionAttempt
        should be created due to @transaction.atomic rollback."""
        metric, _ = AdaptiveTestQuestionMetric.objects.get_or_create(
            user=user, question=question
        )
        metric.skips_since_last_answer = testing_parameters.max_skips
        metric.save()

        initial_count = QuestionAttempt.objects.filter(
            user=user, question=question
        ).count()

        with pytest.raises(TooManySkipsException):
            add_response(user, question, None)

        final_count = QuestionAttempt.objects.filter(
            user=user, question=question
        ).count()
        assert final_count == initial_count


def _create_question_for_subtopic(
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


@pytest.mark.django_db
class TestAddResponseCumulativeAbilityScore:
    @pytest.fixture
    def cumulative_setup(self, db: None) -> dict:
        course = Course.objects.create(
            name='Cumulative Course',
            code='CUM101',
            year=2025,
            semester=Course.SemesterChoices.FALL,
        )
        TestingParameters.objects.create(
            course=course,
            warmpup_length=3,
            max_skips=3,
            skip_readmit_delay=5,
            max_question_repetitions=3,
        )
        unit = Unit.objects.create(course=course, name='Cumulative Unit', number=1)
        subtopic = UnitSubtopic.objects.create(unit=unit, name='Cumulative Subtopic')
        user = MacFastUser.objects.create_user(
            username='cumulative_user',
            password='testpass',
        )
        return {
            'user': user,
            'subtopic': subtopic,
        }

    def test_consecutive_correct_answers_increase_score(
        self,
        cumulative_setup: dict,
    ) -> None:
        user = cumulative_setup['user']
        subtopic = cumulative_setup['subtopic']

        for i in range(5):
            q, correct, _ = _create_question_for_subtopic(
                subtopic, f'CUM-CORRECT-{i}', 0.0
            )
            add_response(user, q, correct)

        ability = UserTopicAbilityScore.objects.get(user=user, unit_sub_topic=subtopic)
        assert float(ability.score) > 0.0

    def test_consecutive_wrong_answers_decrease_score(
        self,
        cumulative_setup: dict,
    ) -> None:
        user = cumulative_setup['user']
        subtopic = cumulative_setup['subtopic']

        for i in range(5):
            q, _, wrong = _create_question_for_subtopic(subtopic, f'CUM-WRONG-{i}', 0.0)
            add_response(user, q, wrong)

        ability = UserTopicAbilityScore.objects.get(user=user, unit_sub_topic=subtopic)
        assert float(ability.score) < 0.0

    def test_score_updates_with_each_attempt(
        self,
        cumulative_setup: dict,
    ) -> None:
        user = cumulative_setup['user']
        subtopic = cumulative_setup['subtopic']

        scores: list[float] = []
        for i in range(4):
            q, correct, _ = _create_question_for_subtopic(
                subtopic, f'CUM-TRACK-{i}', 0.0
            )
            add_response(user, q, correct)
            ability = UserTopicAbilityScore.objects.get(
                user=user, unit_sub_topic=subtopic
            )
            scores.append(float(ability.score))

        # Score should be updated after each attempt (not stuck at initial value)
        unique_scores = set(scores)
        assert len(unique_scores) > 1

        # After all correct answers, the final score should be positive
        assert scores[-1] > 0.0

    def test_attempt_records_reflect_cumulative_score(
        self,
        cumulative_setup: dict,
    ) -> None:
        user = cumulative_setup['user']
        subtopic = cumulative_setup['subtopic']

        for i in range(4):
            q, correct, _ = _create_question_for_subtopic(
                subtopic, f'CUM-RECORD-{i}', 0.0
            )
            add_response(user, q, correct)

        attempts = QuestionAttempt.objects.filter(
            user=user,
            question__subtopic=subtopic,
        ).order_by('timestamp')

        ability_scores = [float(a.updated_ability_score) for a in attempts]

        # The stored ability scores should reflect the running total
        final_ability = UserTopicAbilityScore.objects.get(
            user=user, unit_sub_topic=subtopic
        )
        assert ability_scores[-1] == float(final_ability.score)


@pytest.mark.django_db
class TestAddResponseAbilityComputationOrder:
    """Regression tests for the ordering of QuestionAttempt persistence
    relative to compute_ability(). Without this ordering the ability
    estimate lags one response behind."""

    def test_compute_ability_sees_current_attempt(
        self,
        user: MacFastUser,
        question: Question,
        correct_option: QuestionOption,
        testing_parameters: TestingParameters,
    ) -> None:
        observed: dict = {'attempt_visible': None}

        def capture_attempt_state(
            user_arg: MacFastUser,
            subtopic_arg: UnitSubtopic,
        ) -> tuple[float, float]:
            observed['attempt_visible'] = QuestionAttempt.objects.filter(
                user=user_arg,
                question=question,
            ).exists()
            return (0.5, 1.0)

        mock_model = MagicMock()
        mock_model.compute_ability.side_effect = capture_attempt_state

        add_response(user, question, correct_option, model=mock_model)

        mock_model.compute_ability.assert_called_once()
        assert observed['attempt_visible'] is True

    def test_skipped_attempt_is_persisted_before_compute_ability(
        self,
        user: MacFastUser,
        question: Question,
        testing_parameters: TestingParameters,
    ) -> None:
        observed: dict = {'attempt_visible': None}

        def capture_attempt_state(
            user_arg: MacFastUser,
            subtopic_arg: UnitSubtopic,
        ) -> tuple[float, float]:
            observed['attempt_visible'] = QuestionAttempt.objects.filter(
                user=user_arg,
                question=question,
                skipped=True,
            ).exists()
            return (0.0, 10.0)

        mock_model = MagicMock()
        mock_model.compute_ability.side_effect = capture_attempt_state

        add_response(user, question, None, model=mock_model)

        assert observed['attempt_visible'] is True


@pytest.mark.django_db
class TestAddResponseXPUsesPreAnswerAbility:
    """XP must be computed against the pre-answer ability so a correct
    answer's ability bump does not shrink its own reward."""

    def test_xp_uses_pre_answer_ability_not_post_answer(
        self,
        user: MacFastUser,
        subtopic: UnitSubtopic,
        testing_parameters: TestingParameters,
    ) -> None:
        hard_question = Question.objects.create(
            subtopic=subtopic,
            serial_number='XP-HARD-1',
            content='Hard question',
            difficulty=Decimal('2.0'),
        )
        correct = QuestionOption.objects.create(
            question=hard_question,
            content='Correct',
            is_answer=True,
        )

        mock_model = MagicMock()
        mock_model.compute_ability.return_value = (1.5, 1.0)

        add_response(user, hard_question, correct, model=mock_model)

        # pre-answer ability 0.0, difficulty 2.0, delta 2.0 → 14.
        # post-answer (1.5) would give delta 0.5 → 11.
        xp_record = CourseXP.objects.get(
            user=user, course=hard_question.subtopic.unit.course
        )
        assert xp_record.total_xp == 14

    def test_xp_uses_pre_answer_ability_for_easy_question(
        self,
        user: MacFastUser,
        subtopic: UnitSubtopic,
        testing_parameters: TestingParameters,
    ) -> None:
        UserTopicAbilityScore.objects.update_or_create(
            user=user,
            unit_sub_topic=subtopic,
            defaults={'score': Decimal('1.0'), 'variance': Decimal('1.0')},
        )
        easy_question = Question.objects.create(
            subtopic=subtopic,
            serial_number='XP-EASY-1',
            content='Easy question',
            difficulty=Decimal('-2.0'),
        )
        correct = QuestionOption.objects.create(
            question=easy_question,
            content='Correct',
            is_answer=True,
        )

        mock_model = MagicMock()
        mock_model.compute_ability.return_value = (0.5, 1.0)

        add_response(user, easy_question, correct, model=mock_model)

        # delta -3.0 → raw_xp 4, clamped to min_xp 5.
        xp_record = CourseXP.objects.get(
            user=user, course=easy_question.subtopic.unit.course
        )
        assert xp_record.total_xp == 5
