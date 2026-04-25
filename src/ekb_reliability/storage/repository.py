from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import desc, func, or_, select

from ekb_reliability.storage.models import LineResultRecord, ProcessingRun


def _sanitize_scalar(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, np.generic):
        value = value.item()

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    return value


def _sanitize_for_db(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sanitize_for_db(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_db(v) for v in value]
    if isinstance(value, tuple):
        return [_sanitize_for_db(v) for v in value]

    return _sanitize_scalar(value)


def _safe_str(value: Any, default: str | None = None) -> str | None:
    value = _sanitize_scalar(value)
    if value is None:
        return default
    return str(value)


def _safe_int(value: Any, default: int = 0) -> int:
    value = _sanitize_scalar(value)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    value = _sanitize_scalar(value)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class StorageRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save_pipeline_result(
        self,
        *,
        source_file: str,
        source_kind: str,
        result,
        pipeline_options: dict[str, Any],
    ) -> int:
        with self.session_factory() as session:
            run_data = _sanitize_for_db(
                {
                    "source_file": source_file,
                    "source_kind": source_kind,
                    "total_rows": _safe_int(result.summary.get("row_count", 0), 0),
                    "total_fit": _safe_float(result.summary.get("total_fit", 0.0), 0.0),
                    "total_lambda": _safe_float(result.summary.get("total_lambda", 0.0), 0.0),
                    "system_mtbf_hours": _safe_float(result.summary.get("system_mtbf_hours"), None),
                    "environment": _safe_str(pipeline_options.get("environment"), "unknown"),
                    "quality": _safe_str(pipeline_options.get("quality"), "unknown"),
                    "operating_temp_c": _safe_float(pipeline_options.get("operating_temp_c"), None),
                    "selected_sheets": _sanitize_for_db(pipeline_options.get("selected_sheets")),
                    "summary": _sanitize_for_db(result.summary),
                }
            )

            run = ProcessingRun(**run_data)
            session.add(run)
            session.flush()

            # КРИТИЧЕСКИЙ фикс:
            # сначала чистим весь DataFrame от NaN/NA/np.nan
            df = result.line_results.copy()
            df = df.astype(object).where(pd.notna(df), None)

            records: list[LineResultRecord] = []

            for row in df.to_dict(orient="records"):
                record_data = _sanitize_for_db(
                    {
                        "processing_run_id": run.id,
                        "source_file": _safe_str(row.get("source_file")),
                        "source_sheet": _safe_str(row.get("source_sheet")),
                        "row_index": _safe_int(row.get("row_index"), 0),
                        "raw_description": _safe_str(row.get("raw_description"), "") or "",
                        "normalized_description": _safe_str(row.get("normalized_description"), "") or "",
                        "manufacturer": _safe_str(row.get("manufacturer")),
                        "mpn": _safe_str(row.get("mpn")),
                        "qty": _safe_int(row.get("qty"), 1),
                        "ref_designator": _safe_str(row.get("ref_designator")),
                        "family": _safe_str(row.get("family"), "unknown") or "unknown",
                        "subfamily": _safe_str(row.get("subfamily"), "unknown") or "unknown",
                        "extracted_features": _sanitize_for_db(row.get("extracted_features") or {}),
                        "identification_confidence": _safe_float(
                            row.get("identification_confidence"), 0.0
                        ),
                        "identification_status": _safe_str(
                            row.get("identification_status"), "manual_review_required"
                        )
                        or "manual_review_required",
                        "matched_reference": _safe_str(row.get("matched_reference")),
                        "selected_method": _safe_str(row.get("selected_method"), "none") or "none",
                        "status": _safe_str(row.get("status"), "manual_review_required")
                        or "manual_review_required",
                        "lambda_value": _safe_float(row.get("lambda_value"), 0.0),
                        "unit_lambda_value": _safe_float(row.get("unit_lambda_value"), None),
                        "fit": _safe_float(row.get("fit"), 0.0),
                        "mtbf": _safe_float(row.get("mtbf"), None),
                        "assumptions": _sanitize_for_db(row.get("assumptions") or {}),
                        "comment": _safe_str(row.get("comment")),
                    }
                )

                records.append(LineResultRecord(**record_data))

            session.add_all(records)
            session.commit()
            return int(run.id)

    def list_recent_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.session_factory() as session:
            stmt = select(ProcessingRun).order_by(desc(ProcessingRun.created_at)).limit(limit)
            rows = session.execute(stmt).scalars().all()
            return [
                {
                    "id": r.id,
                    "created_at": r.created_at.isoformat(timespec="seconds"),
                    "source_file": r.source_file,
                    "source_kind": r.source_kind,
                    "total_rows": r.total_rows,
                    "total_fit": r.total_fit,
                    "total_lambda": r.total_lambda,
                    "system_mtbf_hours": r.system_mtbf_hours,
                    "environment": r.environment,
                    "quality": r.quality,
                }
                for r in rows
            ]

    def search_parts(self, query: str, limit: int = 25) -> list[dict[str, Any]]:
        q = (query or "").strip()
        if not q:
            return []

        q_like = f"%{q}%"

        with self.session_factory() as session:
            stmt = (
                select(LineResultRecord)
                .where(
                    or_(
                        func.upper(LineResultRecord.mpn) == q.upper(),
                        LineResultRecord.mpn.ilike(q_like),
                        LineResultRecord.raw_description.ilike(q_like),
                        LineResultRecord.normalized_description.ilike(q_like),
                    )
                )
                .order_by(desc(LineResultRecord.identification_confidence), desc(LineResultRecord.fit))
                .limit(limit)
            )
            rows = session.execute(stmt).scalars().all()

            seen = set()
            results = []

            for row in rows:
                key = (row.mpn or "", row.family, row.subfamily, row.raw_description)
                if key in seen:
                    continue
                seen.add(key)

                results.append(
                    {
                        "mpn": row.mpn,
                        "manufacturer": row.manufacturer,
                        "raw_description": row.raw_description,
                        "family": row.family,
                        "subfamily": row.subfamily,
                        "identification_confidence": row.identification_confidence,
                        "selected_method": row.selected_method,
                        "status": row.status,
                        "fit": row.fit,
                        "mtbf": row.mtbf,
                        "source_sheet": row.source_sheet,
                        "comment": row.comment,
                    }
                )

            return results

    def find_exact_mpn(self, mpn: str | None) -> dict[str, Any] | None:
        if not mpn:
            return None

        with self.session_factory() as session:
            stmt = (
                select(LineResultRecord)
                .where(func.upper(LineResultRecord.mpn) == mpn.upper())
                .order_by(desc(LineResultRecord.identification_confidence))
                .limit(1)
            )
            row = session.execute(stmt).scalar_one_or_none()

            if row is None:
                return None

            return {
                "mpn": row.mpn,
                "manufacturer": row.manufacturer,
                "family": row.family,
                "subfamily": row.subfamily,
                "source": "db_history",
            }