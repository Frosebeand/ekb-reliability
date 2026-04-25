from __future__ import annotations

import random

import pandas as pd

from ekb_reliability.reliability.engine import ReliabilityEngine


FAMILIES = [
    ("resistor", "fixed_resistor"),
    ("resistor", "thermistor"),
    ("capacitor", "ceramic_capacitor"),
    ("capacitor", "electrolytic_capacitor"),
    ("inductor", "fixed_inductor"),
    ("diode", "signal_or_rectifier_diode"),
    ("diode", "zener_diode"),
    ("transistor", "bjt"),
    ("transistor", "mosfet"),
    ("integrated_circuit", "op_amp"),
    ("integrated_circuit", "microcontroller"),
    ("connector", "board_connector"),
    ("crystal", "quartz_crystal"),
]
QUALITIES = ["commercial", "industrial", "military"]
ENVIRONMENTS = ["ground_benign", "ground_fixed", "ground_mobile", "naval_sheltered", "airborne_inhabited_cargo"]


def _sample_features(family: str, subfamily: str) -> dict:
    if family == "resistor":
        feat = {
            "resistance_ohm": 10 ** random.uniform(0, 6),
            "power_ratio": random.uniform(0.1, 1.1),
        }
        if subfamily == "thermistor":
            feat["is_thermistor"] = True
        return feat
    if family == "capacitor":
        return {
            "capacitance_f": 10 ** random.uniform(-11, -3),
            "voltage_ratio": random.uniform(0.1, 1.1),
        }
    if family == "inductor":
        return {
            "inductance_h": 10 ** random.uniform(-9, -1),
            "current_ratio": random.uniform(0.1, 1.0),
        }
    if family == "diode":
        return {"voltage_ratio": random.uniform(0.1, 1.0), "is_zener": subfamily == "zener_diode"}
    if family == "transistor":
        return {"power_ratio": random.uniform(0.1, 1.0), "is_mosfet": subfamily == "mosfet", "is_bjt": subfamily == "bjt"}
    if family == "integrated_circuit":
        return {"pin_count": random.randint(8, 256)}
    if family == "connector":
        return {"contact_count": random.randint(2, 128)}
    if family == "crystal":
        return {"frequency_hz": random.choice([8e6, 12e6, 16e6, 25e6, 50e6])}
    return {}


def build_reference_regression_dataset(n_samples: int = 5000) -> pd.DataFrame:
    rows = []

    for _ in range(n_samples):
        family, subfamily = random.choice(FAMILIES)
        qty = random.randint(1, 40)
        features = _sample_features(family, subfamily)
        temp_c = random.choice([25, 40, 55, 70, 85, 105])
        quality = random.choice(QUALITIES)
        environment = random.choice(ENVIRONMENTS)
        engine = ReliabilityEngine(quality=quality, environment=environment)
        result = engine.evaluate(
            family=family,
            subfamily=subfamily,
            features=features,
            qty=qty,
            identification_confidence=0.99,
            operating_temp_c=temp_c,
        )
        rows.append(
            {
                "family": family,
                "subfamily": subfamily,
                "qty": qty,
                "temperature_c": temp_c,
                "quality": quality,
                "environment": environment,
                "resistance_ohm": features.get("resistance_ohm", 0.0),
                "capacitance_f": features.get("capacitance_f", 0.0),
                "inductance_h": features.get("inductance_h", 0.0),
                "voltage_ratio": features.get("voltage_ratio", 0.0),
                "power_ratio": features.get("power_ratio", 0.0),
                "current_ratio": features.get("current_ratio", 0.0),
                "pin_count": features.get("pin_count", 0),
                "contact_count": features.get("contact_count", 0),
                "frequency_hz": features.get("frequency_hz", 0.0),
                "target_lambda": result.lambda_value,
                "target_mtbf_hours": float(result.mtbf or 0.0),
            }
        )
    return pd.DataFrame(rows)
