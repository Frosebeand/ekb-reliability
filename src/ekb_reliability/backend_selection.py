from __future__ import annotations

from collections import Counter
from typing import Any

from ekb_reliability.schemas import ReliabilityResult

# Empirical post-calibration against the current reference contour.
# This is intentionally limited to the major part-stress families and is used
# only when the user explicitly requests the surrogate backend.
SURROGATE_FAMILY_CALIBRATION = {
    "capacitor": 0.80,
    "connector": 0.63,
    "crystal": 0.51,
    "diode": 0.60,
    "inductor": 0.43,
    "integrated_circuit": 1.20,
    "resistor": 0.60,
    "transistor": 0.55,
}

SURROGATE_ALLOWED_FAMILIES = frozenset(SURROGATE_FAMILY_CALIBRATION)
SURROGATE_REFERENCE_RATIO_MIN = 0.70
SURROGATE_REFERENCE_RATIO_MAX = 1.30


class BackendDecision(dict):
    """Lightweight typed dict wrapper for backend selection."""


def calibrate_surrogate_prediction(family: str, surrogate_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if surrogate_payload is None:
        return None
    factor = float(SURROGATE_FAMILY_CALIBRATION.get(family, 1.0))
    calibrated = dict(surrogate_payload)
    calibrated["calibration_factor"] = factor
    calibrated["lambda_value_raw"] = float(surrogate_payload["lambda_value"])
    calibrated["fit_raw"] = float(surrogate_payload["fit"])
    calibrated["mtbf_raw"] = float(surrogate_payload["mtbf"])
    calibrated["lambda_value"] = float(surrogate_payload["lambda_value"]) * factor
    calibrated["fit"] = float(surrogate_payload["fit"]) * factor
    mtbf_cal = calibrated["mtbf_raw"] / factor if factor > 0 else calibrated["mtbf_raw"]
    calibrated["mtbf"] = float(mtbf_cal)
    return calibrated


def choose_backend(
    *,
    requested_backend: str,
    family: str,
    identification_status: str,
    reference_result: ReliabilityResult,
    surrogate_payload: dict[str, Any] | None,
) -> BackendDecision:
    calibrated = calibrate_surrogate_prediction(family, surrogate_payload)

    decision = BackendDecision(
        chosen_backend="reference",
        decision_reason="reference_requested" if requested_backend != "surrogate" else "surrogate_unavailable",
        surrogate_accepted=False,
        calibrated_surrogate=calibrated,
    )
    if requested_backend != "surrogate":
        return decision
    if calibrated is None:
        return decision
    if family not in SURROGATE_ALLOWED_FAMILIES:
        decision["decision_reason"] = "surrogate_family_not_calibrated"
        return decision
    if reference_result.selected_method != "part_stress":
        decision["decision_reason"] = "surrogate_disabled_for_parts_count"
        return decision
    if reference_result.status != "calculated":
        decision["decision_reason"] = f"surrogate_blocked_reference_status_{reference_result.status}"
        return decision
    if identification_status != "calculated":
        decision["decision_reason"] = f"surrogate_blocked_identification_status_{identification_status}"
        return decision
    ref_fit = float(reference_result.fit or 0.0)
    if ref_fit <= 0:
        decision["decision_reason"] = "surrogate_zero_reference_fit"
        return decision
    ratio = float(calibrated["fit"]) / ref_fit
    decision["reference_ratio_after_calibration"] = ratio
    if ratio < SURROGATE_REFERENCE_RATIO_MIN or ratio > SURROGATE_REFERENCE_RATIO_MAX:
        decision["decision_reason"] = "surrogate_guardrail_reference_mismatch"
        return decision
    decision["chosen_backend"] = "surrogate"
    decision["decision_reason"] = "surrogate_guarded_accept"
    decision["surrogate_accepted"] = True
    return decision


def summarize_backend_decisions(df) -> dict[str, Any]:
    if df is None or getattr(df, "empty", True):
        return {
            "requested_backend": None,
            "surrogate_rows_available": 0,
            "surrogate_rows_accepted": 0,
            "surrogate_rows_rejected": 0,
            "decision_reason_counts": {},
        }
    requested_backend = None
    if "model_backend_requested" in df.columns and not df["model_backend_requested"].empty:
        requested_backend = str(df["model_backend_requested"].iloc[0])
    has_sur = df["surrogate_fit"].notna() if "surrogate_fit" in df.columns else df.index.to_series().astype(bool) * False
    accepted = df["surrogate_accepted"] if "surrogate_accepted" in df.columns else has_sur * False
    reasons = Counter(df.get("backend_decision_reason", []).tolist()) if "backend_decision_reason" in df.columns else Counter()
    return {
        "requested_backend": requested_backend,
        "surrogate_rows_available": int(has_sur.sum()),
        "surrogate_rows_accepted": int(accepted.sum()),
        "surrogate_rows_rejected": int((has_sur & ~accepted).sum()),
        "decision_reason_counts": dict(reasons),
        "calibration_families": sorted(SURROGATE_ALLOWED_FAMILIES),
        "reference_ratio_guardrails": {
            "min": SURROGATE_REFERENCE_RATIO_MIN,
            "max": SURROGATE_REFERENCE_RATIO_MAX,
        },
    }
