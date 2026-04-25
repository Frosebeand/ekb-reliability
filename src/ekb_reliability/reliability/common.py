from __future__ import annotations

from ekb_reliability.reliability.constants import ENVIRONMENT_MULTIPLIER, QUALITY_MULTIPLIER
from ekb_reliability.utils import one_over


def fit_to_lambda(fit: float) -> float:
    return fit / 1e9


def lambda_to_fit(lmbd: float) -> float:
    return lmbd * 1e9


def with_common_multipliers(base_fit: float, quality: str, environment: str) -> float:
    q = QUALITY_MULTIPLIER.get(quality, QUALITY_MULTIPLIER["commercial"])
    e = ENVIRONMENT_MULTIPLIER.get(environment, ENVIRONMENT_MULTIPLIER["ground_fixed"])
    return base_fit * q * e


def result_from_fit(unit_fit: float, qty: int):
    unit_lambda = fit_to_lambda(unit_fit)
    line_lambda = unit_lambda * qty
    return {
        "unit_lambda_value": unit_lambda,
        "lambda_value": line_lambda,
        "fit": lambda_to_fit(line_lambda),
        "mtbf": one_over(line_lambda),
    }
