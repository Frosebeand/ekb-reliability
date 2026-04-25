from __future__ import annotations

from ekb_reliability.reliability.common import result_from_fit, with_common_multipliers
from ekb_reliability.reliability.constants import BASE_PART_COUNT_FIT
from ekb_reliability.reliability.mil_parts_count import calculate_mil_parts_count
from ekb_reliability.schemas import ReliabilityResult


def calculate_parts_count(
    family: str,
    qty: int,
    quality: str,
    environment: str,
    comment: str | None = None,
    subfamily: str | None = None,
    features: dict | None = None,
) -> ReliabilityResult:
    # First try the validated MIL Appendix A subset.
    mil_result = calculate_mil_parts_count(
        family=family,
        subfamily=subfamily or "unknown",
        features=features or {},
        qty=qty,
        quality=quality,
        environment=environment,
    )
    if mil_result is not None:
        return mil_result

    # Legacy fallback for families not yet validated against MIL tables.
    base_fit = BASE_PART_COUNT_FIT.get(family, BASE_PART_COUNT_FIT["other"])
    effective_fit = with_common_multipliers(base_fit, quality, environment)
    values = result_from_fit(effective_fit, qty)
    return ReliabilityResult(
        selected_method="parts_count",
        status="calculated",
        assumptions={
            "reference_method": "legacy_mvp_parts_count",
            "base_fit_per_part": base_fit,
            "quality": quality,
            "environment": environment,
        },
        comment=comment or "legacy parts count fallback",
        **values,
    )
