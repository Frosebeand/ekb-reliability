from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BOMRow(BaseModel):
    source_file: str | None = None
    source_sheet: str | None = None
    row_index: int
    raw_description: str
    normalized_description: str = ""
    manufacturer: str | None = None
    mpn: str | None = None
    qty: int = 1
    ref_designator: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class IdentificationResult(BaseModel):
    family: str = "unknown"
    subfamily: str = "unknown"
    confidence: float = 0.0
    identification_status: str = "manual_review_required"
    matched_reference: str | None = None
    extracted_features: dict[str, Any] = Field(default_factory=dict)
    comment: str | None = None


class ReliabilityResult(BaseModel):
    selected_method: str
    status: str
    lambda_value: float
    fit: float
    mtbf: float | None
    unit_lambda_value: float | None = None
    assumptions: dict[str, Any] = Field(default_factory=dict)
    comment: str | None = None


class PipelineLineResult(BaseModel):
    source_file: str | None = None
    source_sheet: str | None = None
    row_index: int | None = None
    raw_description: str
    normalized_description: str
    manufacturer: str | None = None
    mpn: str | None = None
    qty: int = 1
    family: str
    subfamily: str
    extracted_features: dict[str, Any] = Field(default_factory=dict)
    identification_confidence: float
    identification_status: str = "manual_review_required"
    matched_reference: str | None = None
    selected_method: str
    status: str
    lambda_value: float
    unit_lambda_value: float | None = None
    fit: float
    mtbf: float | None
    assumptions: dict[str, Any] = Field(default_factory=dict)
    comment: str | None = None
    ref_designator: str | None = None
    model_backend_requested: str = "reference"
    model_backend: str = "reference"
    backend_decision_reason: str | None = None
    surrogate_accepted: bool = False
    reference_ratio_after_calibration: float | None = None
    reference_lambda_value: float | None = None
    reference_fit: float | None = None
    reference_mtbf: float | None = None
    surrogate_lambda_value: float | None = None
    surrogate_fit: float | None = None
    surrogate_mtbf: float | None = None
    surrogate_lambda_value_raw: float | None = None
    surrogate_fit_raw: float | None = None
    surrogate_mtbf_raw: float | None = None
    surrogate_calibration_factor: float | None = None


class PipelineOptions(BaseModel):
    environment: str = "ground_fixed"
    quality: str = "commercial"
    operating_temp_c: float | None = None
    selected_sheets: list[str] | None = None
    reliability_backend: str = "reference"


class PipelineResult(BaseModel):
    line_results: Any
    summary: dict[str, Any]
