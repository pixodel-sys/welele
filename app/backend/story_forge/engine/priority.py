"""
Welele Story Forge™ — Dependency Priority Calculation
Deterministic scoring formula: Impact + Urgency + Risk + Leverage - Cost
"""

from typing import Tuple, Optional
from ..models import PriorityComponents, PriorityWeights


def calculate_priority_score(
    components: PriorityComponents,
    weights: Optional[PriorityWeights] = None
) -> Tuple[float, str]:
    """
    Calculates weighted priority score and produces transparent rationale.
    Score formula: (w_i * Impact) + (w_u * Urgency) + (w_r * Risk) + (w_l * Leverage) - (w_c * Cost)
    """
    if weights is None:
        weights = PriorityWeights()

    weighted_impact = weights.weight_impact * components.impact
    weighted_urgency = weights.weight_urgency * components.urgency
    weighted_risk = weights.weight_risk * components.risk
    weighted_leverage = weights.weight_leverage * components.leverage
    weighted_cost = weights.weight_cost * components.cost

    raw_score = weighted_impact + weighted_urgency + weighted_risk + weighted_leverage - weighted_cost
    score = round(max(0.0, raw_score), 2)

    rationale = (
        f"Score {score:.2f} derived from: "
        f"Impact={components.impact}(x{weights.weight_impact:.1f}) + "
        f"Urgency={components.urgency}(x{weights.weight_urgency:.1f}) + "
        f"Risk={components.risk}(x{weights.weight_risk:.1f}) + "
        f"Leverage={components.leverage}(x{weights.weight_leverage:.1f}) - "
        f"Cost={components.cost}(x{weights.weight_cost:.1f})"
    )

    return score, rationale
