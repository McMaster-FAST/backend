from decimal import Decimal
from unittest.mock import MagicMock

from django.test import TestCase

from analytics.models import QuestionAttempt
from analytics.models import UserTopicAbilityScore
from core.models import Question
from core.models import QuestionOption
from core.models import TestSession
from core.models import TestingParameters
from core.queries.question_queries import ContinueActions
from core.queries.question_queries import add_response
from core.queries.question_queries import get_next_question_bundle
from courses.models import Course
from courses.models import Unit
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser


class AdaptiveQuestionFlowTests(TestCase):
    def setUp(self) -> None:
        self.user = MacFastUser.objects.create_user(
            username='testuser',
            password='testpass123',
        )
        self.course = Course.objects.create(
            name='Test Course',
            code='TEST101',
            year=2025,
            semester=Course.SemesterChoices.FALL,
        )
        self.unit = Unit.objects.create(
            course=self.course,
            name='Test Unit',
            number=1,
        )
        self.subtopic = UnitSubtopic.objects.create(
            unit=self.unit,
            name='Test Subtopic',
        )
        TestingParameters.objects.create(
            course=self.course,
            warmpup_length=3,
            max_skips=3,
            skip_readmit_delay=5,
            max_question_repetitions=3,
        )

    def _create_question_with_options(
        self,
        serial: str,
        difficulty: float,
        discrimination: float = 1.0,
    ) -> tuple[Question, QuestionOption, QuestionOption]:
        question = Question.objects.create(
            subtopic=self.subtopic,
            serial_number=serial,
            content=f'Question {serial}',
            difficulty=Decimal(str(difficulty)),
            discrimination=Decimal(str(discrimination)),
        )
        correct_option = QuestionOption.objects.create(
            question=question,
            content='Correct',
            is_answer=True,
        )
        wrong_option = QuestionOption.objects.create(
            question=question,
            content='Wrong',
            is_answer=False,
        )
        return question, correct_option, wrong_option

    def test_submit_correct_answer_marks_correct_and_updates_ability(self) -> None:
        question, correct_option, _ = self._create_question_with_options(
            'ANSWER-CORRECT-001',
            difficulty=0.0,
        )
        mock_model = MagicMock()
        mock_model.compute_ability.return_value = (1.25, 2.5)

        add_response(self.user, question, correct_option, model=mock_model)

        attempt = QuestionAttempt.objects.get(user=self.user, question=question)
        ability = UserTopicAbilityScore.objects.get(
            user=self.user,
            unit_sub_topic=self.subtopic,
        )
        self.assertTrue(attempt.answered_correctly)
        self.assertEqual(float(ability.score), 1.25)

    def test_submit_wrong_answer_marks_incorrect_and_updates_ability(self) -> None:
        question, _, wrong_option = self._create_question_with_options(
            'ANSWER-WRONG-001',
            difficulty=0.0,
        )
        mock_model = MagicMock()
        mock_model.compute_ability.return_value = (-1.25, 2.5)

        add_response(self.user, question, wrong_option, model=mock_model)

        attempt = QuestionAttempt.objects.get(user=self.user, question=question)
        ability = UserTopicAbilityScore.objects.get(
            user=self.user,
            unit_sub_topic=self.subtopic,
        )
        self.assertFalse(attempt.answered_correctly)
        self.assertEqual(float(ability.score), -1.25)

    def test_requesting_next_question_uses_ability_difficulty_range(self) -> None:
        UserTopicAbilityScore.objects.update_or_create(
            user=self.user,
            unit_sub_topic=self.subtopic,
            defaults={'score': Decimal('1.0000'), 'variance': Decimal('10.0000')},
        )
        TestSession.objects.update_or_create(
            user=self.user,
            subtopic=self.subtopic,
            defaults={'selection_lower_bound': -0.25, 'selection_upper_bound': 0.25},
        )

        in_range_question, _, _ = self._create_question_with_options(
            'RANGE-IN-001',
            difficulty=1.1,
        )
        self._create_question_with_options('RANGE-LOW-001', difficulty=0.2)
        self._create_question_with_options('RANGE-HIGH-001', difficulty=1.9)

        question_bundle, _, _ = get_next_question_bundle(self.user, self.subtopic)

        self.assertIsNotNone(question_bundle)
        selected_question = question_bundle.question
        self.assertEqual(selected_question, in_range_question)
        self.assertGreaterEqual(float(selected_question.difficulty), 0.75)
        self.assertLessEqual(float(selected_question.difficulty), 1.25)

    def test_starting_new_subtopic_creates_user_ability_score(self) -> None:
        self.assertFalse(
            UserTopicAbilityScore.objects.filter(
                user=self.user,
                unit_sub_topic=self.subtopic,
            ).exists()
        )

        get_next_question_bundle(self.user, self.subtopic)

        self.assertTrue(
            UserTopicAbilityScore.objects.filter(
                user=self.user,
                unit_sub_topic=self.subtopic,
            ).exists()
        )

    def test_no_questions_available_returns_continue_actions(self) -> None:
        question_bundle, continue_actions, suggested_actions = get_next_question_bundle(
            self.user,
            self.subtopic,
        )

        self.assertIsNone(question_bundle)
        self.assertIn(ContinueActions.INCREMENT_WINDOW_UPPERBOUND, continue_actions)
        self.assertIn(ContinueActions.DECREMENT_WINDOW_LOWERBOUND, continue_actions)
        self.assertEqual(suggested_actions, [])

    def test_higher_item_information_question_is_prioritized(self) -> None:
        UserTopicAbilityScore.objects.update_or_create(
            user=self.user,
            unit_sub_topic=self.subtopic,
            defaults={'score': Decimal('0.0000'), 'variance': Decimal('10.0000')},
        )
        TestSession.objects.update_or_create(
            user=self.user,
            subtopic=self.subtopic,
            defaults={'selection_lower_bound': -1.0, 'selection_upper_bound': 1.0},
        )

        high_info_question, _, _ = self._create_question_with_options(
            'INFO-HIGH-001',
            difficulty=0.0,
            discrimination=2.0,
        )
        self._create_question_with_options(
            'INFO-LOW-001',
            difficulty=0.8,
            discrimination=0.5,
        )

        question_bundle, _, _ = get_next_question_bundle(self.user, self.subtopic)

        self.assertIsNotNone(question_bundle)
        self.assertEqual(question_bundle.question, high_info_question)
