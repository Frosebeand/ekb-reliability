from pathlib import Path

import pandas as pd

from ekb_reliability.pipeline import ReliabilityPipeline


def test_pipeline_options_are_reflected_in_summary(tmp_path: Path):
    df = pd.DataFrame(
        [
            {"Description": "CAP CER 0603 16V 10uF X6S +/-20%", "Qty": 2},
            {"Description": "RES 10K OHM 1% 0603", "Qty": 4},
        ]
    )
    path = tmp_path / "bom.csv"
    df.to_csv(path, index=False)

    pipe = ReliabilityPipeline()
    result = pipe.process_file(path, quality="industrial", environment="ground_benign", operating_temp_c=55)

    assert result.summary["pipeline_options"]["quality"] == "industrial"
    assert result.summary["pipeline_options"]["environment"] == "ground_benign"
    assert result.summary["pipeline_options"]["operating_temp_c"] == 55
    assert "status_counts" in result.summary
    assert "family_fit" in result.summary


def test_pipeline_can_limit_excel_sheets(tmp_path: Path):
    path = tmp_path / "bom.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame([{"Description": "CAP CER 0603 1uF 16V", "Qty": 1}]).to_excel(writer, sheet_name="Main", index=False)
        pd.DataFrame([{"Description": "RES 1K OHM 1% 0603", "Qty": 1}]).to_excel(writer, sheet_name="Aux", index=False)

    pipe = ReliabilityPipeline()
    result = pipe.process_file(path, selected_sheets=["Main"])

    assert len(result.line_results) == 1
    assert result.line_results.iloc[0]["source_sheet"] == "Main"
