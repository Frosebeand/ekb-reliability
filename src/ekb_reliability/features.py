from __future__ import annotations

import re
from typing import Any

from ekb_reliability.utils import safe_float

CAP_MULT = {"pf": 1e-12, "nf": 1e-9, "uf": 1e-6, "mf": 1e-3, "f": 1.0}
IND_MULT = {"nh": 1e-9, "uh": 1e-6, "mh": 1e-3, "h": 1.0}
RES_MULT = {"mohm": 1e6, "kohm": 1e3, "ohm": 1.0}

PACKAGE_PAT = re.compile(r"\b(0201|0402|0603|0805|1206|1210|2512|sot-23|sot23|sot563|sod-123|qfn|tqfn|qfp|tqfp|bga|lga|soic|ssop|msop|sop|dip|smd|sc70|sc-70|sot-363)\b", re.I)
VOLT_PAT = re.compile(r"(\d+(?:\.\d+)?)\s*v\b", re.I)
POWER_PAT = re.compile(r"(\d+(?:\.\d+)?)\s*w\b", re.I)
TOL_PAT = re.compile(r"(\+/-\s*\d+(?:\.\d+)?)\s*%", re.I)
FREQ_PAT = re.compile(r"(\d+(?:\.\d+)?)\s*(hz|khz|mhz|ghz)\b", re.I)
BIT_WIDTH_PAT = re.compile(r"\b(8|16|32)\s*[- ]?bit\b", re.I)
MEMORY_SIZE_PAT = re.compile(r"\b(16|64|256)\s*k(?:bit|b)?\b|\b1\s*m(?:bit|b)?\b", re.I)
PIN_COUNT_PAT = re.compile(r"\b(\d{1,3})\s*[- ]?(?:qfn|tqfn|qfp|tqfp|soic|ssop|msop|sop|dip|bga|lga|pqfn|dfn)\b", re.I)
PORT_COUNT_PAT = re.compile(r"\b(\d+)\s*[- ]?port\b", re.I)
SATA_PIN_PAT = re.compile(r"\b(\d+)p\b", re.I)
CONTACT_PIN_PAT = re.compile(r"\b(\d{1,3})\s*(?:pin|pins|pos|position)\b", re.I)

CAP_PAT = re.compile(r"(\d+(?:\.\d+)?)\s*(pf|nf|uf|mf|f)\b", re.I)
IND_PAT = re.compile(r"(\d+(?:\.\d+)?)\s*(nh|uh|mh|h)\b", re.I)
RES_PAT = re.compile(r"(\d+(?:\.\d+)?)\s*(mohm|kohm|ohm)\b", re.I)


def _extract_scaled(text: str, pattern, mapping):
    m = pattern.search(text)
    if not m:
        return None
    value = safe_float(m.group(1))
    unit = m.group(2).lower()
    if value is None:
        return None
    return value * mapping[unit]


def extract_features(text: str) -> dict[str, Any]:
    text = text.lower()
    features: dict[str, Any] = {"source_text": text}

    features["capacitance_f"] = _extract_scaled(text, CAP_PAT, CAP_MULT)
    features["inductance_h"] = _extract_scaled(text, IND_PAT, IND_MULT)
    features["resistance_ohm"] = _extract_scaled(text, RES_PAT, RES_MULT)

    if m := VOLT_PAT.search(text):
        features["rated_voltage_v"] = safe_float(m.group(1))
    if m := POWER_PAT.search(text):
        features["power_w"] = safe_float(m.group(1))
    if m := TOL_PAT.search(text):
        tol = m.group(1).replace("+/-", "").strip()
        features["tolerance_pct"] = safe_float(tol)
    if m := FREQ_PAT.search(text):
        val = safe_float(m.group(1))
        unit = m.group(2).lower()
        mult = {"hz": 1.0, "khz": 1e3, "mhz": 1e6, "ghz": 1e9}[unit]
        features["frequency_hz"] = val * mult if val is not None else None
    if m := BIT_WIDTH_PAT.search(text):
        features["bit_width"] = int(m.group(1))
    if "flash" in text or "dram" in text or "sram" in text or "memory" in text or "eeprom" in text or "e2prom" in text or "eprom" in text or "rom" in text:
        if m := MEMORY_SIZE_PAT.search(text):
            token = m.group(0).lower().replace(" ", "")
            if token.startswith("1m"):
                features["memory_size_bits"] = 1_000_000
            else:
                import re as _re
                n = int(_re.match(r"(16|64|256)", token).group(1))
                features["memory_size_bits"] = n * 1000
    if m := PACKAGE_PAT.search(text):
        features["package"] = m.group(1).upper().replace("SOT23", "SOT-23").replace("SC70", "SC-70")
    if m := PIN_COUNT_PAT.search(text):
        features["pin_count"] = int(m.group(1))
    if m := PORT_COUNT_PAT.search(text):
        features["contact_count"] = int(m.group(1))
    elif m := CONTACT_PIN_PAT.search(text):
        features["contact_count"] = int(m.group(1))
    elif m := SATA_PIN_PAT.search(text):
        features["contact_count"] = int(m.group(1))

    features["is_ceramic"] = "cer" in text or "ceramic" in text
    features["is_electrolytic"] = "electrolytic" in text or "aluminum" in text
    features["is_ferrite"] = "ferrite" in text or "bead" in text
    features["is_mica"] = " mica" in f" {text}" or "ptfe" in text
    features["is_schottky"] = "schottky" in text
    features["is_mosfet"] = "mosfet" in text or "f e t" in text or "fet" in text
    features["is_bjt"] = "bjt" in text or "transistor" in text or "trans prebias" in text
    features["is_zener"] = "zener" in text
    features["is_tvs"] = "tvs" in text or "transorb" in text
    features["is_op_amp"] = "op amp" in text or "opamp" in text or "buffer amp" in text
    features["is_microcontroller"] = "microcontroller" in text or "mcu" in text or "controller" in text
    features["is_memory"] = "flash" in text or "dram" in text or "sram" in text or "memory" in text or "eeprom" in text or "e2prom" in text
    features["is_connector"] = any(token in text for token in [
        "connector", "socket", "header", "usb connector", "micro-usb", "usb-c", "rj45", "battery holder", "sata", "receptacle", "plug", "jack", "test point", "test pin"
    ])
    features["is_crystal"] = "crystal" in text or "oscillator" in text or "osci" in text or "xtal osc" in text or text.startswith("osc ")
    features["is_relay"] = "relay" in text or "optomos" in text
    features["is_fuse"] = "fuse" in text or "ptc resettable" in text
    features["is_diode"] = "diode" in text or "rectifier" in text or text.startswith("led") or " led " in f" {text} "
    features["is_transceiver"] = "transceiver" in text
    features["is_sensor"] = "sensor" in text
    features["is_transformer"] = "transformer" in text
    features["is_thermistor"] = "thermistor" in text or "ntc" in text or "ptc" in text
    features["is_logic_ic"] = any(keyword in text for keyword in ["buffer", "driver", "translator", "decoder", "demultiplexer", "mux", "switch", "hub", "fanout", "clock generator", "clock buffer", "clock"])
    features["is_power_ic"] = any(keyword in text for keyword in ["buck converter", "step-down", "dc-dc", "ldo", "regulator", "power mux", "converter"])

    return {k: v for k, v in features.items() if v is not None}
