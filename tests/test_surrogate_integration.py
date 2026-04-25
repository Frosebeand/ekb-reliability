from __future__ import annotations

from pathlib import Path

from ekb_reliability.pipeline import ReliabilityPipeline


def test_surrogate_backend_columns_present():
    pipe = ReliabilityPipeline(persistence_enabled=False)
    result = pipe.process_file(Path("data/sample_bom.csv"), persist_db=False, reliability_backend="surrogate")
    df = result.line_results
    assert "model_backend" in df.columns
    assert "reference_mtbf" in df.columns
    assert "surrogate_mtbf" in df.columns
    assert result.summary["pipeline_options"]["reliability_backend"] == "surrogate"
