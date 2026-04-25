from __future__ import annotations

import math
import re
from typing import Iterable

import numpy as np


def safe_float(value, default=None):
    try:
        if value is None:
            return default
        if isinstance(value, str):
            value = value.strip().replace(",", ".")
        return float(value)
    except Exception:
        return default


def is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def compact_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def merge_dicts(*items: dict) -> dict:
    out = {}
    for item in items:
        out.update({k: v for k, v in item.items() if v is not None})
    return out


def one_over(value: float | None) -> float | None:
    if value is None or value <= 0:
        return None
    return 1.0 / value
