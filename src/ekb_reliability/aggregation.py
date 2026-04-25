from __future__ import annotations

import pandas as pd

from ekb_reliability.backend_selection import summarize_backend_decisions
from ekb_reliability.reliability.mil_system_level import estimate_board_circuit_reference


def _clean_records(df: pd.DataFrame, cols: list[str], sort_by: str | None = None, ascending: bool = False, limit: int | None = None) -> list[dict]:
    if df.empty:
        return []
    view = df[cols].copy()
    if sort_by:
        view = view.sort_values(sort_by, ascending=ascending)
    if limit is not None:
        view = view.head(limit)
    return view.to_dict(orient="records")


def build_summary(df: pd.DataFrame, *, environment: str, quality: str, operating_temp_c: float | None, selected_sheets: list[str] | None = None, reliability_backend: str = "reference") -> dict:
    total_lambda = float(df["lambda_value"].sum()) if not df.empty else 0.0
    total_fit = float(df["fit"].sum()) if not df.empty else 0.0
    system_mtbf = (1.0 / total_lambda) if total_lambda > 0 else None

    status_counts = df["status"].value_counts().to_dict() if not df.empty else {}
    family_fit = (
        df.groupby("family", dropna=False)["fit"].sum().sort_values(ascending=False).round(6).to_dict()
        if not df.empty else {}
    )
    family_qty = (
        df.groupby("family", dropna=False)["qty"].sum().sort_values(ascending=False).to_dict()
        if not df.empty else {}
    )
    selected_method_counts = df["selected_method"].value_counts().to_dict() if not df.empty else {}
    source_sheet_counts = (
        df["source_sheet"].fillna("<csv>").value_counts().to_dict()
        if not df.empty and "source_sheet" in df.columns else {}
    )

    diagnostics = df[df["status"].isin(["manual_review_required", "unsupported_component", "partial_match"])].copy() if not df.empty else pd.DataFrame()
    top_fit = df.sort_values("fit", ascending=False).head(15).copy() if not df.empty else pd.DataFrame()

    board_circuit_reference = estimate_board_circuit_reference(df, environment=environment)
    backend_summary = summarize_backend_decisions(df)

    return {
        "row_count": int(len(df)),
        "total_qty": int(df["qty"].sum()) if not df.empty else 0,
        "calculated_rows": int(df["status"].isin(["calculated", "fallback_parts_count", "partial_match"]).sum()) if not df.empty else 0,
        "manual_review_rows": int((df["status"] == "manual_review_required").sum()) if not df.empty else 0,
        "unsupported_rows": int((df["status"] == "unsupported_component").sum()) if not df.empty else 0,
        "partial_match_rows": int((df["status"] == "partial_match").sum()) if not df.empty else 0,
        "parts_count_rows": int((df["selected_method"] == "parts_count").sum()) if not df.empty else 0,
        "part_stress_rows": int((df["selected_method"] == "part_stress").sum()) if not df.empty else 0,
        "total_lambda": total_lambda,
        "total_fit": total_fit,
        "system_mtbf_hours": system_mtbf,
        "status_counts": status_counts,
        "selected_method_counts": selected_method_counts,
        "family_fit": family_fit,
        "family_qty": family_qty,
        "source_sheet_counts": source_sheet_counts,
        "pipeline_options": {
            "environment": environment,
            "quality": quality,
            "operating_temp_c": operating_temp_c,
            "selected_sheets": selected_sheets,
            "reliability_backend": reliability_backend,
        },
        "backend_selection_summary": backend_summary,
        "mil_board_circuit_reference": board_circuit_reference,
        "top_contributors": _clean_records(
            top_fit,
            ["raw_description", "family", "subfamily", "qty", "fit", "status", "source_sheet", "model_backend"],
            limit=15,
        ),
        "diagnostic_rows": _clean_records(
            diagnostics,
            [
                "raw_description",
                "family",
                "subfamily",
                "identification_confidence",
                "selected_method",
                "status",
                "comment",
                "source_sheet",
                "model_backend",
            ],
        ),
    }
