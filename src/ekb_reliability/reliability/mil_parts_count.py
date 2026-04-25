from __future__ import annotations

from typing import Any

from ekb_reliability.reliability.common import result_from_fit
from ekb_reliability.reliability.mil_parts_count_reference import (
    ENV_ALIAS_TO_CODE,
    GENERIC_QUALITY_ALIAS,
    MIL_PARTS_COUNT_ROWS,
    MIL_MICROCIRCUIT_ROWS,
    QUALITY_FACTORS,
    SEMICONDUCTOR_QUALITY_ALIAS,
)
from ekb_reliability.schemas import ReliabilityResult


def _env_code(environment: str) -> str:
    return ENV_ALIAS_TO_CODE.get(environment, ENV_ALIAS_TO_CODE["ground_fixed"])


def _generic_quality_key(quality: str) -> str:
    return GENERIC_QUALITY_ALIAS.get(quality, "lower")


def _semiconductor_quality_key(quality: str, features: dict[str, Any]) -> str:
    alias = SEMICONDUCTOR_QUALITY_ALIAS.get(quality, "plastic")
    if alias == "plastic" and not _looks_like_plastic_package(features):
        return "lower"
    return alias


def _microcircuit_quality_key(quality: str) -> str | None:
    # The validated microcircuit subset is only applied for explicitly MIL-like aliases.
    quality = (quality or "").strip().lower()
    if quality in {"military", "mil_spec"}:
        return "mil_spec"
    if quality in {"b1"}:
        return "b1"
    return None


def _microcircuit_learning_factor(years_in_production: float | None) -> float:
    if years_in_production is None or years_in_production >= 2.0:
        return 1.0
    import math
    return round(0.01 * math.exp(5.35 - 0.35 * years_in_production), 3)


def _pick_microcircuit_row(subfamily: str, features: dict[str, Any]) -> str | None:
    if subfamily == "microcontroller":
        bits = int(features.get("bit_width") or 32)
        if bits <= 8:
            return "microprocessor_mos_8bit"
        if bits <= 16:
            return "microprocessor_mos_16bit"
        return "microprocessor_mos_32bit"

    if subfamily == "memory_ic":
        mem_bits = int(features.get("memory_size_bits") or 16_000)
        text = str(features.get("source_text") or "").lower()
        if "eeprom" in text or "e2prom" in text or "eprom" in text or "uveprom" in text:
            return "memory_mos_eeprom_16k" if mem_bits <= 64_000 else "memory_mos_eeprom_256k"
        if "sram" in text:
            return "memory_cmos_sram_16k" if mem_bits <= 64_000 else "memory_cmos_sram_256k"
        return "memory_mos_rom_16k" if mem_bits <= 64_000 else "memory_mos_rom_256k"

    return None


def _looks_like_plastic_package(features: dict[str, Any]) -> bool:
    package = str(features.get("package") or "").upper()
    if not package:
        return False
    return any(token in package for token in ["SOT", "SOD", "SOIC", "SSOP", "TSSOP", "QFN", "TQFP", "DFN", "SC-70", "SC70", "SMD"])


def _pick_resistor_row(subfamily: str, features: dict[str, Any]) -> str:
    if subfamily == "thermistor":
        return "resistor_thermistor"
    package = str(features.get("package") or "").upper()
    if package or features.get("resistance_ohm") is not None:
        return "resistor_film_chip"
    return "resistor_film_general"


def _pick_capacitor_row(subfamily: str, features: dict[str, Any]) -> str:
    package = str(features.get("package") or "").upper()
    if subfamily == "film_or_mica_capacitor":
        text_mica = bool(features.get("is_mica"))
        return "capacitor_mica" if text_mica else "capacitor_film"
    if subfamily == "electrolytic_capacitor":
        text = str(features.get("source_text") or "").lower()
        if "tantalum" in text or package in {"1206", "1210", "0805", "0603", "0402", "0201", "SMD"}:
            return "capacitor_tantalum_chip"
        return "capacitor_aluminum_dry"
    if package in {"0201", "0402", "0603", "0805", "1206", "1210", "2512", "SMD"}:
        return "capacitor_ceramic_chip"
    return "capacitor_ceramic_general"


def _pick_diode_row(subfamily: str, features: dict[str, Any]) -> str:
    if subfamily == "tvs_diode":
        return "diode_tvs"
    if subfamily == "zener_diode":
        return "diode_zener"
    text = str(features.get("source_text") or "")
    if "schottky" in text:
        return "diode_schottky"
    return "diode_signal"


def _pick_transistor_row(subfamily: str, features: dict[str, Any]) -> str | None:
    if subfamily == "bjt":
        return "transistor_bjt_low_freq"
    return None


def _pick_inductor_row(subfamily: str, features: dict[str, Any]) -> str:
    if subfamily in {"transformer", "common_mode_choke"} or features.get("is_transformer"):
        return "inductor_transformer"
    return "inductor_fixed"


def _pick_connector_row(subfamily: str, features: dict[str, Any]) -> str:
    text = str(features.get("source_text") or "")
    if "coax" in text or "sma" in text or "u.fl" in text or "ufl" in text or "rf" in text:
        return "connector_rf_coaxial"
    if "socket" in text:
        return "connector_socket"
    return "connector_rectangular"


def select_mil_parts_count_row(family: str, subfamily: str, features: dict[str, Any]) -> str | None:
    if family == "resistor":
        return _pick_resistor_row(subfamily, features)
    if family == "capacitor":
        return _pick_capacitor_row(subfamily, features)
    if family == "diode":
        return _pick_diode_row(subfamily, features)
    if family == "transistor":
        return _pick_transistor_row(subfamily, features)
    if family in {"inductor", "ferrite"}:
        return _pick_inductor_row(subfamily, features)
    if family == "connector":
        return _pick_connector_row(subfamily, features)
    if family == "relay":
        return "relay_mechanical_general"
    if family == "crystal":
        return "quartz_crystal"
    if family == "fuse":
        return "fuse"
    if family == "integrated_circuit":
        return _pick_microcircuit_row(subfamily, features)
    return None


def calculate_mil_parts_count(family: str, subfamily: str, features: dict[str, Any], qty: int, quality: str, environment: str) -> ReliabilityResult | None:
    row_key = select_mil_parts_count_row(family, subfamily, features)
    if not row_key:
        return None

    row = MIL_PARTS_COUNT_ROWS.get(row_key) or MIL_MICROCIRCUIT_ROWS.get(row_key)
    if row is None:
        return None
    env_code = _env_code(environment)
    lambda_g = row["lambda_g"].get(env_code)
    if lambda_g is None:
        return None

    q_group = row["quality_group"]
    if q_group.startswith("semiconductor"):
        q_key = _semiconductor_quality_key(quality, features)
    elif q_group == "microcircuit":
        q_key = _microcircuit_quality_key(quality)
        if q_key is None:
            return None
    else:
        q_key = _generic_quality_key(quality)

    q_factor = QUALITY_FACTORS.get(q_group, {}).get(q_key, 1.0)
    pi_l = 1.0
    if q_group == "microcircuit":
        pi_l = _microcircuit_learning_factor(features.get("years_in_production"))
    unit_fit = float(lambda_g) * float(q_factor) * float(pi_l)
    values = result_from_fit(unit_fit, qty)
    assumptions = {
        "reference_method": "MIL-HDBK-217F Appendix A (validated subset)",
        "mil_row_key": row_key,
        "mil_reference": row["mil_ref"],
        "mil_environment_code": env_code,
        "lambda_g_failures_per_1e6_hours": lambda_g,
        "quality_group": q_group,
        "quality_key": q_key,
        "pi_q": q_factor,
        "pi_l": pi_l,
    }
    return ReliabilityResult(
        selected_method="parts_count",
        status="calculated",
        assumptions=assumptions,
        comment="MIL-HDBK-217F Appendix A parts count",
        **values,
    )
