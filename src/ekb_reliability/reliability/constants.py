from __future__ import annotations

# All base rates below are expressed in FIT per part for MVP.
# They are intentionally externalized and easily replaceable with validated tables.
BASE_PART_COUNT_FIT = {
    "resistor": 2.0,
    "capacitor": 3.0,
    "inductor": 4.0,
    "ferrite": 2.5,
    "diode": 4.5,
    "transistor": 6.0,
    "integrated_circuit": 18.0,
    "connector": 12.0,
    "relay": 28.0,
    "fuse": 5.0,
    "crystal": 8.0,
    "sensor_module": 20.0,
    "other": 10.0,
    "unknown": 0.0,
}

QUALITY_MULTIPLIER = {
    "military": 0.8,
    "industrial": 1.0,
    "commercial": 1.2,
    "unknown": 1.2,
}

ENVIRONMENT_MULTIPLIER = {
    "ground_benign": 1.0,
    "ground_fixed": 1.2,
    "ground_mobile": 1.6,
    "naval_sheltered": 1.8,
    "naval_unsheltered": 2.1,
    "airborne_inhabited_cargo": 2.6,
    "airborne_uninhabited_fighter": 3.2,
    "space": 1.5,
}

# family-specific modifiers for simplified part stress
DIELECTRIC_MULT = {
    "ceramic_capacitor": 1.0,
    "electrolytic_capacitor": 1.8,
    "film_or_mica_capacitor": 0.9,
    "generic_capacitor": 1.2,
}

TRANSISTOR_SUBFAMILY_MULT = {
    "mosfet": 1.1,
    "bjt": 1.0,
    "generic_transistor": 1.2,
}

DIODE_SUBFAMILY_MULT = {
    "signal_or_rectifier_diode": 1.0,
    "zener_diode": 1.2,
    "tvs_diode": 1.4,
}

IC_SUBFAMILY_MULT = {
    "op_amp": 0.8,
    "memory_ic": 1.1,
    "microcontroller": 1.0,
    "display_module": 1.2,
    "analog_ic": 0.9,
    "generic_ic": 1.0,
}
