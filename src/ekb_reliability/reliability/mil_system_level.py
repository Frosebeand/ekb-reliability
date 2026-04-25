from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

from ekb_reliability.reliability.mil_parts_count_reference import ENV_ALIAS_TO_CODE
from ekb_reliability.reliability.mil_system_level_reference import MIL_BOARD_CIRCUIT_ROWS, MIL_SINGLE_CONNECTION_ROWS

SMT_HINTS = {
    "0402", "0603", "0805", "1206", "1210", "0201", "2512",
    "SMD", "SMT", "QFN", "DFN", "TQFP", "QFP", "LQFP", "SOIC", "SSOP", "TSSOP", "MSOP", "BGA", "LGA", "SON", "SOT", "SOD",
}
PTH_HINTS = {
    "DIP", "PDIP", "TO-220", "TO220", "TO-92", "TO92", "AXIAL", "RADIAL", "TH", "THROUGH-HOLE", "THROUGH HOLE",
}


def _env_code(environment: str) -> str:
    return ENV_ALIAS_TO_CODE.get(environment, ENV_ALIAS_TO_CODE["ground_fixed"])


def _text_for_row(row: pd.Series) -> str:
    package = ""
    feats = row.get("extracted_features")
    if isinstance(feats, dict):
        package = str(feats.get("package") or "")
    parts = [
        str(row.get("raw_description") or ""),
        str(row.get("normalized_description") or ""),
        package,
    ]
    return " ".join(parts).upper()


def infer_board_technology(df: pd.DataFrame) -> str | None:
    scores: Counter[str] = Counter()
    for _, row in df.iterrows():
        text = _text_for_row(row)
        if any(h in text for h in SMT_HINTS):
            scores["surface_mount"] += 1
        if any(h in text for h in PTH_HINTS):
            scores["plated_through_hole"] += 1
    if not scores:
        return None
    if scores["surface_mount"] == scores["plated_through_hole"]:
        return None
    return scores.most_common(1)[0][0]


def estimate_board_circuit_reference(df: pd.DataFrame, environment: str) -> dict[str, Any]:
    if df.empty:
        return {
            "included_in_total": False,
            "total_lambda_g_failures_per_1e6_hours": 0.0,
            "board_rows": [],
            "note": "No rows available.",
        }

    env_code = _env_code(environment)
    board_rows: list[dict[str, Any]] = []
    total_lambda_g = 0.0

    grouped = df.groupby(df["source_sheet"].fillna("<csv>"), dropna=False)
    for sheet_name, group in grouped:
        tech = infer_board_technology(group)
        if tech is None:
            board_rows.append(
                {
                    "source_sheet": sheet_name,
                    "estimated_board_technology": None,
                    "mil_reference": None,
                    "lambda_g_failures_per_1e6_hours": None,
                    "included": False,
                    "reason": "Unable to infer board technology from package/text hints.",
                }
            )
            continue
        row = MIL_BOARD_CIRCUIT_ROWS[tech]
        lambda_g = float(row["lambda_g"][env_code])
        total_lambda_g += lambda_g
        board_rows.append(
            {
                "source_sheet": sheet_name,
                "estimated_board_technology": tech,
                "mil_reference": row["mil_ref"],
                "lambda_g_failures_per_1e6_hours": lambda_g,
                "included": True,
                "notes": row["notes"],
            }
        )

    return {
        "included_in_total": False,
        "environment_code": env_code,
        "total_lambda_g_failures_per_1e6_hours": round(total_lambda_g, 6),
        "board_rows": board_rows,
        "note": "MIL Section 16 board-circuit references are reported separately and are not yet merged into total system FIT in this project.",
    }


def calculate_single_connection_reference(connection_type: str, count: int, environment: str) -> dict[str, Any] | None:
    row = MIL_SINGLE_CONNECTION_ROWS.get(connection_type)
    if row is None:
        return None
    env_code = _env_code(environment)
    lambda_g = float(row["lambda_g"][env_code])
    total_lambda_g = lambda_g * int(count)
    return {
        "connection_type": connection_type,
        "count": int(count),
        "environment_code": env_code,
        "mil_reference": row["mil_ref"],
        "unit_lambda_g_failures_per_1e6_hours": lambda_g,
        "total_lambda_g_failures_per_1e6_hours": round(total_lambda_g, 6),
        "included_in_total": False,
        "note": "MIL Section 17 single-connection references require explicit connection counts and are not auto-estimated from BOM rows.",
    }
