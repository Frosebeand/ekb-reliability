from __future__ import annotations

from pathlib import Path

import pandas as pd

from ekb_reliability.aggregation import build_summary
from ekb_reliability.backend_selection import choose_backend
from ekb_reliability.bom import inspect_bom_file, load_bom_file
from ekb_reliability.catalog import InMemoryCatalog
from ekb_reliability.classification import ComponentClassifier
from ekb_reliability.config import DEFAULT_ENVIRONMENT, DEFAULT_QUALITY, DEFAULT_RELIABILITY_BACKEND
from ekb_reliability.fusion import fuse_identification
from ekb_reliability.ml.surrogate import SurrogateRegressor
from ekb_reliability.normalization import normalize_bom_row
from ekb_reliability.reliability.engine import ReliabilityEngine
from ekb_reliability.schemas import PipelineOptions, PipelineResult
from ekb_reliability.search import evaluate_part_query


class ReliabilityPipeline:
    def __init__(self, *, quality: str = DEFAULT_QUALITY, environment: str = DEFAULT_ENVIRONMENT, persistence_enabled: bool = False):
        self.classifier = ComponentClassifier()
        self.surrogate = SurrogateRegressor()
        self.default_quality = quality
        self.default_environment = environment
        self.persistence_enabled = persistence_enabled
        self.repository = None
        if persistence_enabled:
            try:
                from ekb_reliability.storage.db import get_session_factory, init_db
                from ekb_reliability.storage.repository import StorageRepository

                init_db()
                self.repository = StorageRepository(get_session_factory())
            except Exception:
                self.repository = None
                self.persistence_enabled = False

    def inspect_file(self, path: str | Path) -> dict:
        return inspect_bom_file(path)

    def process_file(
        self,
        path: str | Path,
        *,
        quality: str | None = None,
        environment: str | None = None,
        operating_temp_c: float | None = None,
        selected_sheets: list[str] | None = None,
        persist_db: bool | None = None,
        reliability_backend: str = DEFAULT_RELIABILITY_BACKEND,
    ) -> PipelineResult:
        options = PipelineOptions(
            quality=quality or self.default_quality,
            environment=environment or self.default_environment,
            operating_temp_c=operating_temp_c,
            selected_sheets=selected_sheets,
            reliability_backend=reliability_backend,
        )
        engine = ReliabilityEngine(quality=options.quality, environment=options.environment)

        rows = load_bom_file(path, selected_sheets=options.selected_sheets)
        rows = [normalize_bom_row(r) for r in rows]
        catalog = InMemoryCatalog.from_rows(rows)

        prepared_rows = []
        for row in rows:
            ident = fuse_identification(row, self.classifier, catalog)
            rel_ref = engine.evaluate(
                family=ident.family,
                subfamily=ident.subfamily,
                features=ident.extracted_features,
                qty=row.qty,
                identification_confidence=ident.confidence,
                operating_temp_c=options.operating_temp_c,
            )
            prepared_rows.append({"row": row, "ident": ident, "rel_ref": rel_ref})

        surrogate_predictions: list[dict | None] = [None for _ in prepared_rows]
        if options.reliability_backend == "surrogate" and self.surrogate.is_available:
            requests = []
            request_indices = []
            for idx, item in enumerate(prepared_rows):
                ident = item["ident"]
                row = item["row"]
                if ident.family == "unknown":
                    continue
                requests.append(
                    {
                        "family": ident.family,
                        "subfamily": ident.subfamily,
                        "features": ident.extracted_features,
                        "qty": row.qty,
                        "operating_temp_c": options.operating_temp_c,
                        "quality": options.quality,
                        "environment": options.environment,
                    }
                )
                request_indices.append(idx)
            predictions = self.surrogate.predict_many(requests)
            for idx, payload in zip(request_indices, predictions):
                surrogate_predictions[idx] = payload

        line_results = []
        for idx, item in enumerate(prepared_rows):
            row = item["row"]
            ident = item["ident"]
            rel_ref = item["rel_ref"]
            rel_sur = surrogate_predictions[idx]

            backend_decision = choose_backend(
                requested_backend=options.reliability_backend,
                family=ident.family,
                identification_status=ident.identification_status,
                reference_result=rel_ref,
                surrogate_payload=rel_sur,
            )
            rel_sur_cal = backend_decision.get("calibrated_surrogate")
            chosen_backend = backend_decision["chosen_backend"]
            chosen_lambda = rel_sur_cal["lambda_value"] if chosen_backend == "surrogate" and rel_sur_cal else rel_ref.lambda_value
            chosen_fit = rel_sur_cal["fit"] if chosen_backend == "surrogate" and rel_sur_cal else rel_ref.fit
            chosen_mtbf = rel_sur_cal["mtbf"] if chosen_backend == "surrogate" and rel_sur_cal else rel_ref.mtbf
            chosen_status = ident.identification_status if ident.identification_status == "partial_match" else rel_ref.status

            comment_parts = [x for x in [ident.comment, rel_ref.comment] if x]
            if rel_sur_cal is not None:
                comment_parts.append(
                    f"surrogate target={rel_sur_cal['target_kind']} calibr={rel_sur_cal.get('calibration_factor', 1.0):.2f} decision={backend_decision['decision_reason']}"
                )
            line_results.append(
                {
                    "source_file": row.source_file,
                    "source_sheet": row.source_sheet,
                    "row_index": row.row_index,
                    "raw_description": row.raw_description,
                    "normalized_description": row.normalized_description,
                    "manufacturer": row.manufacturer,
                    "mpn": row.mpn,
                    "qty": row.qty,
                    "family": ident.family,
                    "subfamily": ident.subfamily,
                    "extracted_features": ident.extracted_features,
                    "identification_confidence": ident.confidence,
                    "identification_status": ident.identification_status,
                    "matched_reference": ident.matched_reference,
                    "selected_method": rel_ref.selected_method,
                    "status": chosen_status,
                    "lambda_value": chosen_lambda,
                    "unit_lambda_value": rel_ref.unit_lambda_value,
                    "fit": chosen_fit,
                    "mtbf": chosen_mtbf,
                    "assumptions": rel_ref.assumptions,
                    "comment": "; ".join(comment_parts) if comment_parts else None,
                    "ref_designator": row.ref_designator,
                    "model_backend_requested": options.reliability_backend,
                    "model_backend": chosen_backend,
                    "backend_decision_reason": backend_decision["decision_reason"],
                    "surrogate_accepted": backend_decision["surrogate_accepted"],
                    "reference_ratio_after_calibration": backend_decision.get("reference_ratio_after_calibration"),
                    "reference_lambda_value": rel_ref.lambda_value,
                    "reference_fit": rel_ref.fit,
                    "reference_mtbf": rel_ref.mtbf,
                    "surrogate_lambda_value": rel_sur_cal["lambda_value"] if rel_sur_cal else None,
                    "surrogate_fit": rel_sur_cal["fit"] if rel_sur_cal else None,
                    "surrogate_mtbf": rel_sur_cal["mtbf"] if rel_sur_cal else None,
                    "surrogate_lambda_value_raw": rel_sur_cal.get("lambda_value_raw") if rel_sur_cal else None,
                    "surrogate_fit_raw": rel_sur_cal.get("fit_raw") if rel_sur_cal else None,
                    "surrogate_mtbf_raw": rel_sur_cal.get("mtbf_raw") if rel_sur_cal else None,
                    "surrogate_calibration_factor": rel_sur_cal.get("calibration_factor") if rel_sur_cal else None,
                }
            )

        df = pd.DataFrame(line_results)
        if not df.empty:
            df["assumptions_json"] = df["assumptions"].apply(lambda x: str(x))
            df["extracted_features_json"] = df["extracted_features"].apply(lambda x: str(x))
        summary = build_summary(
            df,
            environment=options.environment,
            quality=options.quality,
            operating_temp_c=options.operating_temp_c,
            selected_sheets=options.selected_sheets,
            reliability_backend=options.reliability_backend,
        )
        result = PipelineResult(line_results=df, summary=summary)
        should_persist = self.persistence_enabled if persist_db is None else persist_db
        if should_persist and self.repository is not None:
            run_id = self.repository.save_pipeline_result(
                source_file=Path(path).name,
                source_kind="bom_upload",
                result=result,
                pipeline_options=summary.get("pipeline_options", {}),
            )
            result.summary["storage_run_id"] = run_id
        return result

    def evaluate_query(
        self,
        *,
        description: str,
        manufacturer: str | None = None,
        mpn: str | None = None,
        qty: int = 1,
        quality: str | None = None,
        environment: str | None = None,
        operating_temp_c: float | None = None,
        reliability_backend: str = DEFAULT_RELIABILITY_BACKEND,
    ) -> dict:
        return evaluate_part_query(
            description=description,
            manufacturer=manufacturer,
            mpn=mpn,
            qty=qty,
            classifier=self.classifier,
            surrogate=self.surrogate,
            repository=self.repository,
            quality=quality or self.default_quality,
            environment=environment or self.default_environment,
            operating_temp_c=operating_temp_c,
            reliability_backend=reliability_backend,
        )

    def search_parts(self, query: str, limit: int = 25) -> list[dict]:
        if self.repository is None:
            return []
        return self.repository.search_parts(query, limit=limit)

    def list_recent_runs(self, limit: int = 20) -> list[dict]:
        if self.repository is None:
            return []
        return self.repository.list_recent_runs(limit=limit)
