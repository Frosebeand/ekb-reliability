from __future__ import annotations

import re

from ekb_reliability.utils import compact_spaces

REPLACEMENTS = {
    "µf": "uf",
    "μf": "uf",
    "μh": "uh",
    "µh": "uh",
    "ω": "ohm",
    "±": "+/-",
    "в±": "+/-",
    "volt ": "v ",
}

MANUFACTURER_ALIASES = {
    "ti": "Texas Instruments",
    "texas instruments incorporated": "Texas Instruments",
    "nxp semiconductors": "NXP",
    "stmicroelectronics": "STMicroelectronics",
    "on semiconductor": "onsemi",
}


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    out = text.strip().lower()
    for src, dst in REPLACEMENTS.items():
        out = out.replace(src, dst)
    out = re.sub(r"[^\w\s\.\-\+/%]", " ", out)
    out = compact_spaces(out)
    return out


def normalize_mpn(mpn: str | None) -> str | None:
    if not mpn:
        return None
    cleaned = re.sub(r"\s+", "", mpn.strip().upper())
    return cleaned or None


def normalize_manufacturer(name: str | None) -> str | None:
    if not name:
        return None
    key = compact_spaces(name.strip().lower())
    return MANUFACTURER_ALIASES.get(key, compact_spaces(name.strip()))


def normalize_bom_row(row):
    row.normalized_description = normalize_text(row.raw_description)
    row.manufacturer = normalize_manufacturer(row.manufacturer)
    row.mpn = normalize_mpn(row.mpn)
    return row
