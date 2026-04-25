from __future__ import annotations

import io
import json

import pandas as pd

from ekb_reliability.schemas import PipelineResult


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
    return buffer.getvalue()


def pipeline_result_to_excel_bytes(result: PipelineResult) -> bytes:
    buffer = io.BytesIO()
    df = result.line_results.copy()
    summary_df = pd.DataFrame(
        [{"metric": k, "value": json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v} for k, v in result.summary.items() if k not in {"top_contributors", "diagnostic_rows"}]
    )
    diagnostics_df = df[df["status"].isin(["manual_review_required", "unsupported_component", "partial_match"])].copy()
    top_df = df.sort_values("fit", ascending=False).head(25).copy()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="LineResults")
        summary_df.to_excel(writer, index=False, sheet_name="Summary")
        diagnostics_df.to_excel(writer, index=False, sheet_name="Diagnostics")
        top_df.to_excel(writer, index=False, sheet_name="TopContributors")
    return buffer.getvalue()
