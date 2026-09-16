"""
Story Forge Unit Tests: Dependency Priority Calculation
Formula: (w_i * Impact) + (w_u * Urgency) + (w_r * Risk) + (w_l * Leverage) - (w_c * Cost)
"""

import pytest
from story_forge.models import PriorityComponents, PriorityWeights
from story_forge.engine.priority import calculate_priority_score


def test_priority_score_standard_weights():
    comps = PriorityComponents(impact=8, urgency=7, risk=6, leverage=9, cost=2)
    score, rationale = calculate_priority_score(comps)
    # Expected: 8 + 7 + 6 + 9 - 2 = 28.00
    assert score == 28.00
    assert "derived from" in rationale
    assert "Impact=8" in rationale


def test_priority_score_custom_weights():
    comps = PriorityComponents(impact=10, urgency=10, risk=10, leverage=10, cost=5)
    weights = PriorityWeights(
        weight_impact=2.0,
        weight_urgency=1.5,
        weight_risk=1.0,
        weight_leverage=1.0,
        weight_cost=0.5
    )
    score, rationale = calculate_priority_score(comps, weights)
    # Expected: 20 + 15 + 10 + 10 - 2.5 = 52.5
    assert score == 52.50
    assert "x2.0" in rationale


def test_priority_score_non_negative_clamp():
    comps = PriorityComponents(impact=1, urgency=1, risk=1, leverage=1, cost=10)
    weights = PriorityWeights(
        weight_impact=0.1,
        weight_urgency=0.1,
        weight_risk=0.1,
        weight_leverage=0.1,
        weight_cost=5.0
    )
    score, rationale = calculate_priority_score(comps, weights)
    assert score == 0.0
