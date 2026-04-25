from __future__ import annotations

from ekb_reliability.backend_selection import choose_backend
from ekb_reliability.catalog import InMemoryCatalog
from ekb_reliability.fusion import fuse_identification
from ekb_reliability.normalization import normalize_bom_row
from ekb_reliability.reliability.engine import ReliabilityEngine
from ekb_reliability.schemas import BOMRow


def evaluate_part_query(
    *,
    description: str,
    manufacturer: str | None,
    mpn: str | None,
    qty: int,
    classifier,
    surrogate,
    repository,
    quality: str,
    environment: str,
    operating_temp_c: float | None = None,
    reliability_backend: str = "reference",
):
    row = BOMRow(
        source_file="manual_search",
        source_sheet="search",
        row_index=0,
        raw_description=description,
        manufacturer=manufacturer,
        mpn=mpn,
        qty=max(int(qty or 1), 1),
    )
    row = normalize_bom_row(row)
    catalog = InMemoryCatalog()
    exact = repository.find_exact_mpn(row.mpn) if repository is not None else None
    if exact:
        catalog.add(
            exact["mpn"],
            exact["family"],
            exact["subfamily"],
            manufacturer=exact.get("manufacturer"),
            source=exact.get("source", "db_history"),
        )
    ident = fuse_identification(row, classifier, catalog)
    engine = ReliabilityEngine(quality=quality, environment=environment)
    rel = engine.evaluate(
        family=ident.family,
        subfamily=ident.subfamily,
        features=ident.extracted_features,
        qty=row.qty,
        identification_confidence=ident.confidence,
        operating_temp_c=operating_temp_c,
    )
    sur = None
    if surrogate and surrogate.is_available and ident.family != "unknown":
        sur = surrogate.predict(
            family=ident.family,
            subfamily=ident.subfamily,
            features=ident.extracted_features,
            qty=row.qty,
            operating_temp_c=operating_temp_c,
            quality=quality,
            environment=environment,
        )
    backend_decision = choose_backend(
        requested_backend=reliability_backend,
        family=ident.family,
        identification_status=ident.identification_status,
        reference_result=rel,
        surrogate_payload=sur,
    )
    sur_cal = backend_decision.get("calibrated_surrogate")
    chosen_backend = backend_decision["chosen_backend"]
    chosen_status = ident.identification_status if ident.identification_status == "partial_match" else rel.status
    return {
        "raw_description": row.raw_description,
        "normalized_description": row.normalized_description,
        "manufacturer": row.manufacturer,
        "mpn": row.mpn,
        "qty": row.qty,
        "family": ident.family,
        "subfamily": ident.subfamily,
        "identification_confidence": ident.confidence,
        "identification_status": ident.identification_status,
        "matched_reference": ident.matched_reference,
        "extracted_features": ident.extracted_features,
        "selected_method": rel.selected_method,
        "status": chosen_status,
        "lambda_value": sur_cal["lambda_value"] if chosen_backend == "surrogate" and sur_cal else rel.lambda_value,
        "unit_lambda_value": rel.unit_lambda_value,
        "fit": sur_cal["fit"] if chosen_backend == "surrogate" and sur_cal else rel.fit,
        "mtbf": sur_cal["mtbf"] if chosen_backend == "surrogate" and sur_cal else rel.mtbf,
        "assumptions": rel.assumptions,
        "comment": "; ".join([x for x in [ident.comment, rel.comment, backend_decision['decision_reason']] if x]) or None,
        "model_backend_requested": reliability_backend,
        "model_backend": chosen_backend,
        "backend_decision_reason": backend_decision["decision_reason"],
        "surrogate_accepted": backend_decision["surrogate_accepted"],
        "reference_ratio_after_calibration": backend_decision.get("reference_ratio_after_calibration"),
        "reference_lambda_value": rel.lambda_value,
        "reference_fit": rel.fit,
        "reference_mtbf": rel.mtbf,
        "surrogate_lambda_value": sur_cal["lambda_value"] if sur_cal else None,
        "surrogate_fit": sur_cal["fit"] if sur_cal else None,
        "surrogate_mtbf": sur_cal["mtbf"] if sur_cal else None,
        "surrogate_lambda_value_raw": sur_cal.get("lambda_value_raw") if sur_cal else None,
        "surrogate_fit_raw": sur_cal.get("fit_raw") if sur_cal else None,
        "surrogate_mtbf_raw": sur_cal.get("mtbf_raw") if sur_cal else None,
        "surrogate_calibration_factor": sur_cal.get("calibration_factor") if sur_cal else None,
    }
