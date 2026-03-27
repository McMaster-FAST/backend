from math import exp, sqrt

from core.models import Question

# TODO: document this
def probability_of_success(ability_score: float, difficulty: float) -> float:
    return exp(ability_score - difficulty) / (1 + exp(ability_score - difficulty))


def mle(
    responses: list[tuple[Question, bool]],
    prev_abiltiy_score: float,
) -> tuple[float, float]:
    successes = sum(1 for _, response in responses if response)
    numerator = successes - sum(
        probability_of_success(prev_abiltiy_score, float(difficulty)) for difficulty, _ in responses
    )

    denominator = sum(
        (
            probability_of_success(prev_abiltiy_score, float(difficulty))
            * (1 - probability_of_success(prev_abiltiy_score, float(difficulty)))
        )
        for difficulty, _ in responses
    )

    if denominator == 0:
        raise ValueError(
            "Denominator for ability update is zero, cannot update ability score."
        )

    new_ability_score = prev_abiltiy_score + numerator / denominator
    variance = sqrt(1 / denominator)
    return new_ability_score, variance


def max_apost(
    responses: list[tuple[Question, bool]],
    prev_abiltiy_score: float,
    prev_variance: float,
) -> tuple[float, float]:
    successes = sum(1 for _, response in responses if response)

    precision = 1 / prev_variance
    score = (
        successes
        - sum(probability_of_success(prev_abiltiy_score, float(difficulty)) for difficulty, _ in responses)
    )

    fischer_information = sum(
        (
            probability_of_success(prev_abiltiy_score, float(difficulty))
            * (1 - probability_of_success(prev_abiltiy_score, float(difficulty)))
        )
        for difficulty, _ in responses
    )

    new_ability_score = prev_abiltiy_score + (
        score - precision * prev_abiltiy_score
    ) / (fischer_information + precision)

    new_variance = 1 / (fischer_information + precision)

    return new_ability_score, new_variance
