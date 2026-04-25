from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np

from ekb_reliability.config import CLASSIFIER_MODEL_PATH


class ComponentClassifier:
    def __init__(self, model_path: str | Path | None = None):
        self.model_path = Path(model_path or CLASSIFIER_MODEL_PATH)
        self.model = None
        self.load_error: str | None = None
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
            except Exception as exc:  # pragma: no cover - defensive runtime guard
                self.load_error = str(exc)
                self.model = None

    @property
    def is_available(self) -> bool:
        return self.model is not None

    def predict(self, text: str, manufacturer: str | None = None, mpn: str | None = None) -> dict[str, Any]:
        if self.model is None:
            return {"family": "unknown", "subfamily": "unknown", "confidence": 0.0}

        full_text = " | ".join([x for x in [text, manufacturer, mpn] if x])
        probs = self.model.predict_proba([full_text])[0]
        idx = int(np.argmax(probs))
        label = self.model.classes_[idx]
        family, subfamily = label.split("::", 1)
        return {
            "family": family,
            "subfamily": subfamily,
            "confidence": float(probs[idx]),
        }
