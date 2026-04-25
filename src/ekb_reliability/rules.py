from __future__ import annotations

from ekb_reliability.features import extract_features
from ekb_reliability.taxonomy import default_subfamily
from ekb_reliability.schemas import IdentificationResult


def classify_by_rules(description: str) -> IdentificationResult:
    text = description.lower()
    feat = extract_features(text)

    def make(family: str, subfamily: str | None = None, conf: float = 0.9, status: str = "calculated", comment: str | None = None):
        return IdentificationResult(
            family=family,
            subfamily=subfamily or default_subfamily(family),
            confidence=conf,
            identification_status=status,
            extracted_features=feat,
            comment=comment,
        )

    if feat.get("is_connector") or text.startswith("conn ") or " wafer " in f" {text} ":
        status = "partial_match" if "test point" in text or "test pin" in text or "battery holder" in text else "calculated"
        subfamily = "socket" if "socket" in text else "board_connector"
        return make("connector", subfamily, 0.90 if status == "partial_match" else 0.96, status)
    if feat.get("is_crystal"):
        return make("crystal", "quartz_crystal", 0.92 if text.startswith("osc ") or "xtal osc" in text else 0.96)
    if feat.get("is_sensor"):
        return make("sensor_module", "sensor_module", 0.90)
    if feat.get("is_relay"):
        return make("relay", "electromechanical_relay", 0.95)
    if feat.get("is_fuse"):
        return make("fuse", "fuse", 0.93 if "ptc" in text else 0.95, "partial_match" if "ptc" in text else "calculated")
    if "common mode choke" in text or "choke coil" in text:
        return make("inductor", "common_mode_choke", 0.90)
    if feat.get("is_transformer"):
        return make("inductor", "transformer", 0.88, "partial_match")
    if feat.get("is_ferrite"):
        return make("ferrite", "ferrite_bead", 0.94)
    if "inductor" in text or feat.get("inductance_h") is not None:
        return make("inductor", "fixed_inductor", 0.92)
    if text.startswith("led") or " led " in f" {text} ":
        return make("diode", "led_diode", 0.86, "partial_match")
    if feat.get("is_thermistor"):
        return make("resistor", "thermistor", 0.95)
    if "resistor" in text or text.startswith("res ") or " res " in f" {text} " or feat.get("resistance_ohm") is not None:
        return make("resistor", "fixed_resistor", 0.93)
    if "cap" in text or "capacitor" in text or feat.get("capacitance_f") is not None:
        if feat.get("is_electrolytic"):
            return make("capacitor", "electrolytic_capacitor", 0.94)
        if feat.get("is_ceramic"):
            return make("capacitor", "ceramic_capacitor", 0.95)
        if feat.get("is_mica"):
            return make("capacitor", "film_or_mica_capacitor", 0.92)
        return make("capacitor", "generic_capacitor", 0.88, "partial_match")
    if feat.get("is_zener"):
        return make("diode", "zener_diode", 0.93)
    if feat.get("is_tvs"):
        return make("diode", "tvs_diode", 0.93)
    if feat.get("is_diode"):
        return make("diode", "signal_or_rectifier_diode", 0.90)
    if feat.get("is_mosfet"):
        return make("transistor", "mosfet", 0.92)
    if feat.get("is_bjt"):
        return make("transistor", "bjt", 0.84, "partial_match")
    if feat.get("is_op_amp"):
        return make("integrated_circuit", "op_amp", 0.93)
    if feat.get("is_microcontroller"):
        return make("integrated_circuit", "microcontroller", 0.95)
    if feat.get("is_memory"):
        return make("integrated_circuit", "memory_ic", 0.92)
    if "transmitter/receiver" in text or "transceiver" in text:
        return make("integrated_circuit", "transceiver_ic", 0.90)
    if feat.get("is_logic_ic") or feat.get("is_power_ic"):
        return make("integrated_circuit", "generic_ic", 0.84, "partial_match")
    if "ic" in text or "qfn" in text or "tqfp" in text or "bga" in text or "sop" in text:
        return make("integrated_circuit", "generic_ic", 0.78, "partial_match")
    return IdentificationResult(
        family="unknown",
        subfamily="unknown",
        confidence=0.15,
        identification_status="manual_review_required",
        extracted_features=feat,
        comment="rule-based classifier found no strong pattern",
    )
