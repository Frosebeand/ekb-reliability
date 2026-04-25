from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

RAW_CATEGORY_TO_TAXONOMY = {
    "Capacitors_aluminum_electrolytic.csv": ("capacitor", "electrolytic_capacitor"),
    "mica_and_ptfe_capacitors.csv": ("capacitor", "film_or_mica_capacitor"),
    "fixed_inductors.csv": ("inductor", "fixed_inductor"),
    "fuses.csv": ("fuse", "fuse"),
    "automotive_relays.csv": ("relay", "electromechanical_relay"),
    "instrumentation__op_amps__buffer_amps.csv": ("integrated_circuit", "op_amp"),
    "analog_multipliers__dividers.csv": ("integrated_circuit", "analog_ic"),
    "single_bipolar_transistors.csv": ("transistor", "bjt"),
    "single_diodes.csv": ("diode", "signal_or_rectifier_diode"),
    "through_hole_resistors.csv": ("resistor", "fixed_resistor"),
    "isolation_transformers_and_autotransformers__step_up__step_down.csv": ("inductor", "transformer"),
    "led_character_and_numeric.csv": ("integrated_circuit", "display_module"),
    # intentionally not using clearly irrelevant/non-EKB files in baseline training set
}

SUPPORTED_FAMILIES = {
    "resistor",
    "capacitor",
    "inductor",
    "ferrite",
    "diode",
    "transistor",
    "integrated_circuit",
    "connector",
    "relay",
    "fuse",
    "crystal",
    "sensor_module",
    "other",
    "unknown",
}

DEFAULT_SUBFAMILY_BY_FAMILY = {
    "resistor": "fixed_resistor",
    "capacitor": "ceramic_capacitor",
    "inductor": "fixed_inductor",
    "ferrite": "ferrite_bead",
    "diode": "signal_or_rectifier_diode",
    "transistor": "bjt",
    "integrated_circuit": "generic_ic",
    "connector": "board_connector",
    "relay": "electromechanical_relay",
    "fuse": "fuse",
    "crystal": "quartz_crystal",
    "sensor_module": "sensor_module",
    "other": "other",
    "unknown": "unknown",
}

def normalize_family(value: str | None) -> str:
    if not value:
        return "unknown"
    value = value.strip().lower().replace(" ", "_")
    return value if value in SUPPORTED_FAMILIES else "unknown"

def default_subfamily(family: str) -> str:
    family = normalize_family(family)
    return DEFAULT_SUBFAMILY_BY_FAMILY.get(family, "unknown")
