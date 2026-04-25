from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ekb_reliability.ml.synthetic import build_reference_regression_dataset


FEATURE_COLS = [
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
CAT_COLS = ["family", "subfamily", "quality", "environment"]
NUM_COLS = [c for c in FEATURE_COLS if c not in CAT_COLS]


def build_model() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
            ("num", "passthrough", NUM_COLS),
        ]
    )

    return Pipeline(
        steps=[
            ("prep", preprocessor),
            (
                "rf",
                RandomForestRegressor(
                    n_estimators=300,
                    random_state=42,
                    n_jobs=1,
                    min_samples_leaf=1,
                ),
            ),
        ]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--metrics-output")
    parser.add_argument("--n-samples", type=int, default=8000)
    args = parser.parse_args()

    df = build_reference_regression_dataset(args.n_samples)

    target = "target_mtbf_hours"
    target_kind = "target_log_mtbf_hours"
    X = df[FEATURE_COLS]
    y = np.log10(df[target].clip(lower=1.0))

    model = build_model()

    X_train, X_test, y_train, y_test_log = train_test_split(X, y, random_state=42, test_size=0.2)
    model.fit(X_train, y_train)
    preds_log = model.predict(X_test)

    y_test = np.power(10.0, y_test_log)
    preds = np.power(10.0, preds_log)
    abs_error = np.abs(y_test - preds)
    ape = abs_error / np.clip(y_test, 1.0, None) * 100.0
    metrics = {
        "target": target,
        "target_kind": target_kind,
        "target_transform": "log10",
        "MAE_mtbf_hours": float(mean_absolute_error(y_test, preds)),
        "RMSE_mtbf_hours": float(mean_squared_error(y_test, preds) ** 0.5),
        "R2": float(r2_score(y_test, preds)),
        "MAPE_mtbf_pct": float(ape.mean()),
        "median_APE_mtbf_pct": float(np.median(ape)),
        "n_test": int(len(y_test)),
        "n_train": int(len(y_train)),
    }
    print(metrics)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": model,
        "metadata": {
            "target_kind": target_kind,
            "target_transform": "log10",
            "feature_cols": FEATURE_COLS,
            "model_version": "rf_mtbf_bundle_v3",
            "training_rows": int(len(df)),
        },
    }
    joblib.dump(payload, output)

    if args.metrics_output:
        metrics_path = Path(args.metrics_output)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
