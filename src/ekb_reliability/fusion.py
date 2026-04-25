from __future__ import annotations

from ekb_reliability.rules import classify_by_rules
from ekb_reliability.schemas import IdentificationResult


def fuse_identification(row, classifier, catalog) -> IdentificationResult:
    rule_result = classify_by_rules(row.normalized_description)

    # Trust explicit high-confidence rules first for strongly patterned BOM items
    if rule_result.family != "unknown" and rule_result.confidence >= 0.94 and rule_result.identification_status != "manual_review_required":
        return rule_result

    match = catalog.match(row.mpn) if catalog else None
    if match:
        return IdentificationResult(
            family=match.family,
            subfamily=match.subfamily,
            confidence=max(rule_result.confidence, 0.97),
            identification_status="calculated" if rule_result.family != "unknown" else "partial_match",
            matched_reference=match.source,
            extracted_features=rule_result.extracted_features,
            comment=f"catalog match by MPN ({match.source})",
        )

    if classifier and classifier.is_available:
        ml = classifier.predict(row.normalized_description, row.manufacturer, row.mpn)
        if rule_result.family != "unknown" and rule_result.confidence >= 0.90 and ml["family"] != rule_result.family:
            return rule_result
        if ml["confidence"] >= 0.80:
            return IdentificationResult(
                family=ml["family"],
                subfamily=ml["subfamily"],
                confidence=ml["confidence"],
                identification_status="calculated" if ml["confidence"] >= 0.90 else "partial_match",
                extracted_features=rule_result.extracted_features,
                comment="ml classifier decision",
            )
        if rule_result.family != "unknown" and rule_result.confidence >= 0.70:
            return rule_result
        if ml["confidence"] >= 0.55:
            return IdentificationResult(
                family=ml["family"],
                subfamily=ml["subfamily"],
                confidence=ml["confidence"],
                identification_status="manual_review_required",
                extracted_features=rule_result.extracted_features,
                comment="low-confidence ML prediction",
            )

    return rule_result
