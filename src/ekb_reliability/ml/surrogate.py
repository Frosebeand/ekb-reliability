from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from ekb_reliability.config import SURROGATE_MODEL_PATH


@dataclass
class SurrogateMetadata:
    target_kind: str = "target_log_lambda"
    feature_cols: list[str] | None = None
    model_version: str = "legacy"


class SurrogateRegressor:
    def __init__(self, model_path: str | Path | None = None):
        self.model_path = Path(model_path or SURROGATE_MODEL_PATH)
        self.model = None
        self.metadata = SurrogateMetadata()
        if self.model_path.exists():
            payload = joblib.load(self.model_path)
            if isinstance(payload, dict) and "model" in payload:
                self.model = payload["model"]
                meta = payload.get("metadata") or {}
                self.metadata = SurrogateMetadata(
                    target_kind=meta.get("target_kind", "target_mtbf_hours"),
                    feature_cols=list(meta.get("feature_cols") or []),
                    model_version=str(meta.get("model_version") or "bundle"),
                )
            else:
                self.model = payload
                self.metadata = SurrogateMetadata(
                    target_kind="target_log_lambda",
                    feature_cols=self._infer_feature_cols(payload),
                    model_version="legacy_pipeline",
                )

    @property
    def is_available(self) -> bool:
        return self.model is not None

    def _infer_feature_cols(self, model) -> list[str]:
        try:
            prep = model.named_steps["prep"]
            cols: list[str] = []
            for _, _, tr_cols in prep.transformers:
                if isinstance(tr_cols, list):
                    cols.extend(tr_cols)
            return cols
        except Exception:
            return [
                "family",
                "subfamily",
                "qty",
                "temperature_c",
                "quality",
                "environment",
                "resistance_ohm",
                "capacitance_f",
                "inductance_h",
                "voltage_ratio",
                "power_ratio",
                "current_ratio",
                "pin_count",
                "contact_count",
                "frequency_hz",
            ]

    def _build_feature_frame(
        self,
        *,
        family: str,
        subfamily: str,
        features: dict[str, Any],
        qty: int,
        operating_temp_c: float | None,
        quality: str,
        environment: str,
    ) -> pd.DataFrame:
        row = {
            "family": family,
            "subfamily": subfamily,
            "qty": int(qty),
            "temperature_c": float(operating_temp_c or 25.0),
            "quality": quality,
            "environment": environment,
            "resistance_ohm": float(features.get("resistance_ohm") or 0.0),
            "capacitance_f": float(features.get("capacitance_f") or 0.0),
            "inductance_h": float(features.get("inductance_h") or 0.0),
            "voltage_ratio": float(features.get("voltage_ratio") or 0.0),
            "power_ratio": float(features.get("power_ratio") or 0.0),
            "current_ratio": float(features.get("current_ratio") or 0.0),
            "pin_count": int(features.get("pin_count") or 0),
            "contact_count": int(features.get("contact_count") or 0),
            "frequency_hz": float(features.get("frequency_hz") or 0.0),
        }
        feature_cols = self.metadata.feature_cols or list(row.keys())
        for col in feature_cols:
            row.setdefault(col, 0.0 if col not in {"family", "subfamily", "quality", "environment"} else "unknown")
        return pd.DataFrame([{c: row.get(c) for c in feature_cols}])

    def _convert_prediction(self, pred: float) -> dict[str, Any]:
        target_kind = self.metadata.target_kind
        if target_kind == "target_mtbf_hours":
            mtbf = max(pred, 1.0)
            lambda_value = 1.0 / mtbf
        elif target_kind == "target_lambda":
            lambda_value = max(pred, 1e-15)
            mtbf = 1.0 / lambda_value
        elif target_kind == "target_log_mtbf_hours":
            mtbf = max(10.0 ** pred, 1.0)
            lambda_value = 1.0 / mtbf
        else:
            lambda_value = max(10.0 ** pred, 1e-15)
            mtbf = 1.0 / lambda_value
        return {
            "target_kind": target_kind,
            "lambda_value": lambda_value,
            "fit": lambda_value * 1e9,
            "mtbf": mtbf,
            "raw_prediction": pred,
            "model_version": self.metadata.model_version,
        }

    def predict_many(self, requests: list[dict[str, Any]]) -> list[dict[str, Any] | None]:
        if self.model is None:
            return [None for _ in requests]
        if not requests:
            return []
        frames = [
            self._build_feature_frame(
                family=req["family"],
                subfamily=req["subfamily"],
                features=req.get("features") or {},
                qty=req.get("qty") or 1,
                operating_temp_c=req.get("operating_temp_c"),
                quality=req.get("quality") or "commercial",
                environment=req.get("environment") or "ground_fixed",
            )
            for req in requests
        ]
        X = pd.concat(frames, ignore_index=True)
        preds = self.model.predict(X)
        return [self._convert_prediction(float(pred)) for pred in preds]

    def predict(
        self,
        *,
        family: str,
        subfamily: str,
        features: dict[str, Any],
        qty: int,
        operating_temp_c: float | None,
        quality: str,
        environment: str,
    ) -> dict[str, Any] | None:
        if self.model is None:
            return None
        pred = self.predict_many([
            {
                "family": family,
                "subfamily": subfamily,
                "features": features,
                "qty": qty,
                "operating_temp_c": operating_temp_c,
                "quality": quality,
                "environment": environment,
            }
        ])
        return pred[0] if pred else None
