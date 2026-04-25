from __future__ import annotations

import pandas as pd

from ekb_reliability.reliability.mil_system_level import (
    calculate_single_connection_reference,
    estimate_board_circuit_reference,
    infer_board_technology,
)


def _df(rows):
    return pd.DataFrame(rows)


def test_infer_board_technology_surface_mount():
    df = _df([
        {"raw_description": "10k resistor 0603 1%", "normalized_description": "10k resistor 0603 1%", "extracted_features": {"package": "0603"}},
        {"raw_description": "MCU 48-QFN", "normalized_description": "MCU 48-QFN", "extracted_features": {"package": "QFN"}},
    ])
    assert infer_board_technology(df) == "surface_mount"


def test_infer_board_technology_through_hole():
    df = _df([
        {"raw_description": "header 2.54mm through-hole", "normalized_description": "header 2.54mm through-hole", "extracted_features": {"package": "TH"}},
        {"raw_description": "transistor TO-92", "normalized_description": "transistor TO-92", "extracted_features": {"package": "TO-92"}},
    ])
    assert infer_board_technology(df) == "plated_through_hole"


def test_estimate_board_circuit_reference_per_sheet():
    df = _df([
        {"source_sheet": "Board_A", "raw_description": "10k resistor 0603 1%", "normalized_description": "10k resistor 0603 1%", "extracted_features": {"package": "0603"}},
        {"source_sheet": "Board_B", "raw_description": "header through-hole 2x5", "normalized_description": "header through-hole 2x5", "extracted_features": {"package": "TH"}},
    ])
    ref = estimate_board_circuit_reference(df, environment="ground_fixed")
    assert ref["included_in_total"] is False
    assert len(ref["board_rows"]) == 2
    rows = {r["source_sheet"]: r for r in ref["board_rows"]}
    assert rows["Board_A"]["estimated_board_technology"] == "surface_mount"
    assert rows["Board_B"]["estimated_board_technology"] == "plated_through_hole"
    assert abs(ref["total_lambda_g_failures_per_1e6_hours"] - (0.37 + 0.045)) < 1e-9


def test_calculate_single_connection_reference_manual():
    result = calculate_single_connection_reference("reflow_solder", count=10, environment="ground_fixed")
    assert result is not None
    assert result["count"] == 10
    assert result["environment_code"] == "GF"
    assert abs(result["unit_lambda_g_failures_per_1e6_hours"] - 0.00024) < 1e-12
    assert abs(result["total_lambda_g_failures_per_1e6_hours"] - 0.0024) < 1e-12
