from __future__ import annotations

from pathlib import Path

from ekb_reliability.pipeline import ReliabilityPipeline


def test_surrogate_guardrail_summary_present():
    pipe = ReliabilityPipeline(persistence_enabled=False)
    result = pipe.process_file(Path("data/sample_bom.csv"), persist_db=False, reliability_backend="surrogate")
    summary = result.summary["backend_selection_summary"]
    assert summary["requested_backend"] == "surrogate"
    assert "surrogate_rows_available" in summary
    assert "surrogate_rows_accepted" in summary
    assert "decision_reason_counts" in summary


def test_surrogate_only_accepted_for_part_stress_rows():
    pipe = ReliabilityPipeline(persistence_enabled=False)
    result = pipe.process_file(Path("data/sample_bom.csv"), persist_db=False, reliability_backend="surrogate")
    df = result.line_results
    accepted = df[df["surrogate_accepted"]]
    if not accepted.empty:
        assert (accepted["selected_method"] == "part_stress").all()
        assert (accepted["model_backend"] == "surrogate").all()
    rejected = df[~df["surrogate_accepted"]]
    if not rejected.empty:
        assert (rejected["model_backend"] == "reference").all()
        assert rejected["backend_decision_reason"].notna().all()
