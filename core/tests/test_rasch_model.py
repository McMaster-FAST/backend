from decimal import Decimal
import time
from unittest.mock import patch

import pytest

from analytics.models import QuestionAttempt
from analytics.models import UserTopicAbilityScore
from core.cat_methods.rasch_model import RaschModel
from core.models import Question
from core.models import TestingParameters
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser


def _create_attempts(
    user: MacFastUser,
    question: Question,
    count: int,
    correct: bool,
) -> None:
    """Helper to create QuestionAttempt records directly in the DB."""
    for _ in range(count):
        QuestionAttempt.objects.create(
            user=user,
            question=question,
            answered_correctly=correct,
            skipped=False,
            updated_ability_score=0,
            time_spent=1.0,
        )
        time.sleep(0.002)


@pytest.mark.django_db
class TestRaschModelWarmupPhase:
    """Tests that compute_ability uses max_apost during warmup."""

    def test_uses_max_apost_when_below_warmup_length(
        self,
        user: MacFastUser,
        question: Question,
        subtopic: UnitSubtopic,
        testing_parameters: TestingParameters,
    ) -> None:
        """When the number of non-skipped responses is less than warmpup_length,
        max_apost should be called."""
        # Create fewer attempts than warmpup_length (default 3)
        _create_attempts(user, question, count=1, correct=True)

        with patch('core.cat_methods.rasch_model.max_apost', wraps=None) as mock_map:
            mock_map.return_value = (0.5, 5.0)
            RaschModel.compute_ability(user, subtopic)
            mock_map.assert_called_once()

    def test_uses_mle_when_at_or_above_warmup_length(
        self,
        user: MacFastUser,
        question: Question,
        subtopic: UnitSubtopic,
        testing_parameters: TestingParameters,
    ) -> None:
        """When the number of non-skipped responses reaches warmpup_length,
        mle should be called."""
        _create_attempts(user, question, count=3, correct=True)

        with patch('core.cat_methods.rasch_model.mle', wraps=None) as mock_mle:
            mock_mle.return_value = (0.8, 2.0)
            RaschModel.compute_ability(user, subtopic)
            mock_mle.assert_called_once()


@pytest.mark.django_db
class TestRaschModelSkippedExclusion:
    """Tests that skipped attempts are excluded from ability computation."""

    def test_skipped_attempts_are_not_counted(
        self,
        user: MacFastUser,
        question: Question,
        subtopic: UnitSubtopic,
        testing_parameters: TestingParameters,
    ) -> None:
        """Skipped attempts (skipped=True) should not be included in the
        responses passed to the estimation function."""
        # Create 1 non-skipped attempt and 5 skipped attempts
        _create_attempts(user, question, count=1, correct=True)
        for _ in range(5):
            QuestionAttempt.objects.create(
                user=user,
                question=question,
                answered_correctly=False,
                skipped=True,
                updated_ability_score=0,
                time_spent=0.0,
            )
            time.sleep(0.002)

        # With only 1 non-skipped attempt (< warmpup_length=3), max_apost
        # should be called, not mle
        with patch('core.cat_methods.rasch_model.max_apost', wraps=None) as mock_map:
            mock_map.return_value = (0.3, 8.0)
            RaschModel.compute_ability(user, subtopic)
            mock_map.assert_called_once()
            # Verify only 1 response was passed (the non-skipped one)
            responses_arg = mock_map.call_args[0][0]
            assert len(responses_arg) == 1


@pytest.mark.django_db
class TestRaschModelUsesStoredScoreAndVariance:
    """Tests that compute_ability reads previous score and variance."""

    def test_previous_score_and_variance_are_passed_to_map(
        self,
        user: MacFastUser,
        question: Question,
        subtopic: UnitSubtopic,
        testing_parameters: TestingParameters,
    ) -> None:
        """The stored score and variance in UserTopicAbilityScore should be
        used as inputs to max_apost."""
        # Set a specific score and variance
        ability, _ = UserTopicAbilityScore.objects.get_or_create(
            user=user, unit_sub_topic=subtopic
        )
        ability.score = Decimal('1.5000')
        ability.variance = Decimal('4.0000')
        ability.save()

        _create_attempts(user, question, count=1, correct=True)

        with patch('core.cat_methods.rasch_model.max_apost', wraps=None) as mock_map:
            mock_map.return_value = (1.6, 3.5)
            RaschModel.compute_ability(user, subtopic)

            # Verify prev_ability_score and prev_variance args
            call_args = mock_map.call_args[0]
            prev_ability_score = call_args[1]
            prev_variance = call_args[2]
            assert prev_ability_score == pytest.approx(1.5, abs=1e-3)
            assert prev_variance == pytest.approx(4.0, abs=1e-3)
