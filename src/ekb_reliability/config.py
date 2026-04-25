from __future__ import annotations

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
BASE_DIR = PROJECT_DIR

DEFAULT_ENVIRONMENT = "ground_fixed"
DEFAULT_QUALITY = "commercial"
DEFAULT_RELIABILITY_BACKEND = "reference"

MODEL_DIR = PROJECT_DIR / "models"
DATA_DIR = PROJECT_DIR / "data"

CLASSIFIER_MODEL_CANDIDATES = (
    MODEL_DIR / "component_classifier.joblib",
    MODEL_DIR / "component_classifier_retrained.joblib",
)
SURROGATE_MODEL_PATH = MODEL_DIR / "surrogate_regressor.joblib"


def resolve_classifier_model_path() -> Path:
    for candidate in CLASSIFIER_MODEL_CANDIDATES:
        if candidate.exists():
            return candidate
    return CLASSIFIER_MODEL_CANDIDATES[0]


CLASSIFIER_MODEL_PATH = resolve_classifier_model_path()
