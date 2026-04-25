from __future__ import annotations

from ekb_reliability.reliability.common import result_from_fit, with_common_multipliers
from ekb_reliability.reliability.constants import (
    BASE_PART_COUNT_FIT,
    DIELECTRIC_MULT,
    DIODE_SUBFAMILY_MULT,
    IC_SUBFAMILY_MULT,
    TRANSISTOR_SUBFAMILY_MULT,
)
from ekb_reliability.schemas import ReliabilityResult


def _temperature_multiplier(temp_c: float | None) -> float:
    if temp_c is None:
        return 1.0
    if temp_c <= 40:
        return 1.0
    if temp_c <= 70:
        return 1.2
    if temp_c <= 100:
        return 1.5
    return 2.0


def _stress_ratio_multiplier(value: float | None, low=0.5, high=0.8):
    if value is None:
        return 1.0
    if value <= low:
        return 0.9
    if value <= high:
        return 1.0
    if value <= 1.0:
        return 1.3
    return 1.8


def calculate_part_stress(
    family: str,
    subfamily: str,
    features: dict,
    qty: int,
    quality: str,
    environment: str,
    operating_temp_c: float | None = None,
):
    base = BASE_PART_COUNT_FIT.get(family, BASE_PART_COUNT_FIT["other"])
    temp_mult = _temperature_multiplier(operating_temp_c)
    extra = 1.0
    assumptions = {
        "quality": quality,
        "environment": environment,
        "operating_temp_c": operating_temp_c,
    }

    if family == "resistor":
        power_ratio = features.get("power_ratio")
        res_val = features.get("resistance_ohm")
        extra *= _stress_ratio_multiplier(power_ratio, 0.4, 0.7)
        if res_val is not None and res_val < 10:
            extra *= 1.15
        assumptions.update({"power_ratio": power_ratio})
    elif family == "capacitor":
        voltage_ratio = features.get("voltage_ratio")
        extra *= DIELECTRIC_MULT.get(subfamily, 1.1)
        extra *= _stress_ratio_multiplier(voltage_ratio, 0.5, 0.8)
        assumptions.update({"voltage_ratio": voltage_ratio})
    elif family in {"inductor", "ferrite"}:
        current_ratio = features.get("current_ratio")
        extra *= _stress_ratio_multiplier(current_ratio, 0.5, 0.8)
        assumptions.update({"current_ratio": current_ratio})
    elif family == "diode":
        extra *= DIODE_SUBFAMILY_MULT.get(subfamily, 1.0)
        extra *= _stress_ratio_multiplier(features.get("voltage_ratio"), 0.5, 0.8)
    elif family == "transistor":
        extra *= TRANSISTOR_SUBFAMILY_MULT.get(subfamily, 1.0)
        extra *= _stress_ratio_multiplier(features.get("power_ratio"), 0.4, 0.7)
    elif family == "integrated_circuit":
        extra *= IC_SUBFAMILY_MULT.get(subfamily, 1.0)
        pin_count = features.get("pin_count")
        if pin_count:
            extra *= 1.0 + min(pin_count, 256) / 512.0
        assumptions.update({"pin_count": pin_count})
    elif family == "connector":
        contact_count = features.get("contact_count", 2)
        extra *= 1.0 + min(contact_count, 128) / 128.0
        assumptions.update({"contact_count": contact_count})
    elif family == "crystal":
        freq = features.get("frequency_hz")
        if freq and freq > 25e6:
            extra *= 1.2
    else:
        return None

    effective_fit = with_common_multipliers(base * temp_mult * extra, quality, environment)
    values = result_from_fit(effective_fit, qty)
    return ReliabilityResult(
        selected_method="part_stress",
        status="calculated",
        assumptions={"base_fit_per_part": base, "temp_mult": temp_mult, "extra_mult": extra, **assumptions},
        comment="simplified part stress method",
        **values,
    )
