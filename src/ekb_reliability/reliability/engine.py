from __future__ import annotations

from ekb_reliability.config import DEFAULT_ENVIRONMENT, DEFAULT_QUALITY
from ekb_reliability.reliability.part_stress import calculate_part_stress
from ekb_reliability.reliability.parts_count import calculate_parts_count
from ekb_reliability.schemas import ReliabilityResult

SUPPORTED_STRESS_FAMILIES = {
    "resistor",
    "capacitor",
    "inductor",
    "ferrite",
    "diode",
    "transistor",
    "integrated_circuit",
    "connector",
    "crystal",
}


class ReliabilityEngine:
    def __init__(self, quality: str = DEFAULT_QUALITY, environment: str = DEFAULT_ENVIRONMENT):
        self.quality = quality
        self.environment = environment

    def select_method(self, family: str, features: dict) -> str:
        if family not in SUPPORTED_STRESS_FAMILIES:
            return "parts_count"
        if family == "resistor" and features.get("resistance_ohm") is not None:
            return "part_stress"
        if family == "capacitor" and features.get("capacitance_f") is not None:
            return "part_stress"
        if family in {"inductor", "ferrite"} and features.get("inductance_h") is not None:
            return "part_stress"
        if family == "diode" and any(features.get(k) is not None or features.get(k) for k in ["voltage_ratio", "rated_voltage_v", "is_schottky", "is_zener", "is_tvs"]):
            return "part_stress"
        if family == "transistor" and any(features.get(k) is not None or features.get(k) for k in ["power_ratio", "rated_voltage_v", "is_mosfet", "is_bjt"]):
            return "part_stress"
        if family == "integrated_circuit" and (features.get("pin_count") is not None or any(features.get(k) for k in ["is_microcontroller", "is_memory", "is_op_amp", "is_logic_ic", "is_power_ic"])):
            return "part_stress"
        if family == "connector":
            source_text = str(features.get("source_text") or "")
            if any(token in source_text for token in ["test point", "test pin", "battery holder"]):
                return "parts_count"
            if features.get("contact_count") is not None or any(token in source_text for token in ["usb", "header", "socket", "receptacle", "plug", "jack", "connector"]):
                return "part_stress"
        if family == "crystal" and features.get("frequency_hz") is not None:
            return "part_stress"
        return "parts_count"

    def evaluate(self, family: str, subfamily: str, features: dict, qty: int, identification_confidence: float, operating_temp_c: float | None = None) -> ReliabilityResult:
        if family == "unknown":
            return ReliabilityResult(
                selected_method="none",
                status="manual_review_required",
                lambda_value=0.0,
                fit=0.0,
                mtbf=None,
                comment="unknown family",
            )

        method = self.select_method(family, features)

        if method == "part_stress":
            result = calculate_part_stress(
                family=family,
                subfamily=subfamily,
                features=features,
                qty=qty,
                quality=self.quality,
                environment=self.environment,
                operating_temp_c=operating_temp_c,
            )
            if result is not None:
                if identification_confidence < 0.70:
                    result.status = "partial_match"
                    result.comment = (result.comment or "") + "; low identification confidence"
                return result

        result = calculate_parts_count(
            family=family,
            subfamily=subfamily,
            features=features,
            qty=qty,
            quality=self.quality,
            environment=self.environment,
            comment="fallback parts count" if method != "parts_count" else "parts count method",
        )
        result.status = "fallback_parts_count" if method != "parts_count" else ("partial_match" if identification_confidence < 0.70 else "calculated")
        return result
