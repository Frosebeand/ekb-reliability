from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.makedirs("/tmp/mplconfig", exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def build_synthetic_sequences(n_samples: int, seq_len: int = 24):
    rng = np.random.default_rng(42)
    X = []
    y = []
    raw_sequences = []
    for _ in range(n_samples):
        base = rng.uniform(0.001, 0.02)
        trend = rng.uniform(-0.0001, 0.0006)
        seasonal = 0.0007 * np.sin(np.linspace(0, 2 * np.pi, seq_len))
        noise = rng.normal(0.0, 0.0006, size=seq_len)
        seq = np.maximum(base + trend * np.arange(seq_len) + seasonal + noise, 1e-5)
        target = float(max(seq[-1] + trend + rng.normal(0.0, 0.0002), 1e-5))
        X.append(seq[:, None])
        y.append(target)
        raw_sequences.append(seq)
    return np.asarray(X, dtype="float32"), np.asarray(y, dtype="float32"), np.asarray(raw_sequences, dtype="float32")


def _write_placeholder_summary(out_dir: Path, exc: Exception, sequences: np.ndarray, y_test: np.ndarray):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(sequences[0])
    ax.set_title("Synthetic failure-rate series example")
    ax.set_xlabel("Time step")
    ax.set_ylabel("Failure rate proxy")
    fig.tight_layout()
    fig.savefig(out_dir / "lstm_series_example.png", dpi=180)
    plt.close(fig)

    summary = {
        "status": "tensorflow_not_available",
        "message": str(exc),
        "note": "LSTM experimental module requires TensorFlow under the target Python 3.11 environment.",
        "n_test": int(len(y_test)),
        "sequence_length": int(sequences.shape[1]),
    }
    (out_dir / "lstm_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--n-samples", type=int, default=1200)
    parser.add_argument("--epochs", type=int, default=8)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    X, y, raw_sequences = build_synthetic_sequences(args.n_samples)
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    try:
        import tensorflow as tf  # noqa: F401
        from tensorflow import keras
    except Exception as exc:
        _write_placeholder_summary(out_dir, exc, raw_sequences[split:], y_test)
        return

    model = keras.Sequential(
        [
            keras.layers.Input(shape=(X.shape[1], X.shape[2])),
            keras.layers.LSTM(32),
            keras.layers.Dense(16, activation="relu"),
            keras.layers.Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mae", metrics=[keras.metrics.RootMeanSquaredError(name="rmse")])
    history = model.fit(X_train, y_train, validation_split=0.2, epochs=args.epochs, batch_size=32, verbose=0)
    evaluation = model.evaluate(X_test, y_test, verbose=0, return_dict=True)
    preds = model.predict(X_test, verbose=0).reshape(-1)

    model.save(out_dir / "lstm_failure_timeseries.keras")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(history.history.get("loss", []), label="train_loss")
    ax.plot(history.history.get("val_loss", []), label="val_loss")
    ax.set_title("LSTM training history")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("MAE")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "lstm_loss_curve.png", dpi=180)
    plt.close(fig)

    compare_count = min(80, len(preds))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(y_test[:compare_count], label="actual")
    ax.plot(preds[:compare_count], label="predicted")
    ax.set_title("LSTM forecast vs actual")
    ax.set_xlabel("Sample index")
    ax.set_ylabel("Failure rate proxy")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "lstm_forecast_vs_actual.png", dpi=180)
    plt.close(fig)

    summary = {
        "status": "ok",
        "test_mae": float(evaluation.get("loss", 0.0)),
        "test_rmse": float(evaluation.get("rmse", 0.0)),
        "history": {k: [float(vv) for vv in vals] for k, vals in history.history.items()},
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "sequence_length": int(X.shape[1]),
        "forecast_preview": {
            "actual": [float(v) for v in y_test[:compare_count]],
            "predicted": [float(v) for v in preds[:compare_count]],
        },
    }
    (out_dir / "lstm_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
