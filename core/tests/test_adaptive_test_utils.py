import pytest

from core.cat_methods.adaptive_test_utils import max_apost
from core.cat_methods.adaptive_test_utils import mle


class TestMLE:
    """Tests for the MLE (Maximum Likelihood Estimation) function."""

    def test_all_correct_answers_increase_ability(self) -> None:
        """When all answers are correct, the new ability should be higher
        than the previous ability."""
        # (difficulty, answered_correctly)
        responses = [
            (0.0, True),
            (0.0, True),
            (0.0, True),
        ]
        prev_ability = 0.0

        new_ability, variance = mle(responses, prev_ability)
        assert new_ability > prev_ability

    def test_all_wrong_answers_decrease_ability(self) -> None:
        """When all answers are wrong, the new ability should be lower
        than the previous ability."""
        responses = [
            (0.0, False),
            (0.0, False),
            (0.0, False),
        ]
        prev_ability = 0.0

        new_ability, variance = mle(responses, prev_ability)
        assert new_ability < prev_ability

    def test_empty_responses_raises_value_error(self) -> None:
        """MLE with empty responses should raise ValueError because
        the denominator is zero."""
        with pytest.raises(ValueError):
            mle([], 0.0)

    def test_returns_tuple_of_two_floats(self) -> None:
        """MLE should return (new_ability_score, variance)."""
        responses = [
            (0.5, True),
            (-0.5, False),
            (0.0, True),
        ]
        result = mle(responses, 0.0)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_higher_difficulty_correct_answers_give_larger_increase(self) -> None:
        """Answering harder questions correctly should increase ability more
        than answering easier questions correctly."""
        easy_responses = [
            (-1.0, True),
            (-1.0, True),
            (-1.0, True),
        ]
        hard_responses = [
            (1.0, True),
            (1.0, True),
            (1.0, True),
        ]
        prev_ability = 0.0

        easy_ability, _ = mle(easy_responses, prev_ability)
        hard_ability, _ = mle(hard_responses, prev_ability)
        assert hard_ability > easy_ability


class TestMaxApost:
    """Tests for the MAP (Maximum A Posteriori) function."""

    def test_all_correct_answers_increase_ability(self) -> None:
        """When all answers are correct, ability should increase."""
        responses = [
            (0.0, True),
            (0.0, True),
        ]
        prev_ability = 0.0
        prev_variance = 10.0

        new_ability, new_variance = max_apost(responses, prev_ability, prev_variance)
        assert new_ability > prev_ability

    def test_all_wrong_answers_decrease_ability(self) -> None:
        """When all answers are wrong, ability should decrease."""
        responses = [
            (0.0, False),
            (0.0, False),
        ]
        prev_ability = 0.0
        prev_variance = 10.0

        new_ability, new_variance = max_apost(responses, prev_ability, prev_variance)
        assert new_ability < prev_ability

    def test_variance_decreases_with_more_responses(self) -> None:
        """As more responses are added, the variance should decrease,
        reflecting increased certainty in the ability estimate."""
        prev_ability = 0.0
        prev_variance = 10.0

        responses_1 = [(0.0, True)]
        responses_3 = [(0.0, True), (0.0, False), (0.0, True)]
        responses_5 = [
            (0.0, True),
            (0.0, False),
            (0.0, True),
            (0.0, True),
            (0.0, False),
        ]

        _, variance_1 = max_apost(responses_1, prev_ability, prev_variance)
        _, variance_3 = max_apost(responses_3, prev_ability, prev_variance)
        _, variance_5 = max_apost(responses_5, prev_ability, prev_variance)

        assert variance_1 > variance_3 > variance_5

    def test_returns_tuple_of_two_floats(self) -> None:
        """max_apost should return (new_ability_score, new_variance)."""
        responses = [(0.0, True)]
        result = max_apost(responses, 0.0, 10.0)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_high_initial_variance_allows_larger_update(self) -> None:
        """With high initial variance (high uncertainty), the ability update
        should be larger compared to low initial variance."""
        responses = [(0.0, True), (0.0, True)]
        prev_ability = 0.0

        ability_high_var, _ = max_apost(responses, prev_ability, 10.0)
        ability_low_var, _ = max_apost(responses, prev_ability, 0.5)

        # High variance means the prior has less influence, so the update
        # should be larger
        assert abs(ability_high_var - prev_ability) > abs(
            ability_low_var - prev_ability
        )
