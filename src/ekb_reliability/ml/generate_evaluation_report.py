from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

os.makedirs("/tmp/mplconfig", exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
import matplotlib

matplotlib.use("Agg")
import joblib
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from ekb_reliability.ml.dataset_builder import load_curated_text_dataset
from ekb_reliability.ml.synthetic import build_reference_regression_dataset
from ekb_reliability.ml.surrogate import SurrogateRegressor

FEATURE_IMPORTANCE_TOP_N = 20


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _plot_feature_importance(feature_df: pd.DataFrame, output_path: Path):
    if feature_df.empty:
        return
    top = (
        feature_df.groupby("feature", as_index=False)["abs_weight"]
        .max()
        .sort_values("abs_weight", ascending=False)
        .head(FEATURE_IMPORTANCE_TOP_N)
    )
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(top["feature"][::-1], top["abs_weight"][::-1])
    ax.set_xlabel("|weight|")
    ax.set_title("Top classifier features")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def _plot_confusion_matrix(labels: list[str], matrix: list[list[int]], output_path: Path):
    fig, ax = plt.subplots(figsize=(10, 10))
    disp = ConfusionMatrixDisplay(confusion_matrix=np.asarray(matrix), display_labels=labels)
    disp.plot(ax=ax, xticks_rotation=90, colorbar=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def _legacy_classifier_report(metrics_path: Path, model_path: str | Path | None, output_dir: Path) -> dict:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    labels = list(metrics.get("labels") or [])
    if labels and metrics.get("confusion_matrix"):
        pd.DataFrame(metrics["confusion_matrix"], index=labels, columns=labels).to_csv(output_dir / "classifier_confusion_matrix.csv")
        _plot_confusion_matrix(labels, metrics["confusion_matrix"], output_dir / "classifier_confusion_matrix.png")

    feature_rows = []
    top_features = metrics.get("top_features") or {}
    for label, rows in top_features.items():
        for row in rows:
            feature_rows.append(
                {
                    "label": label,
                    "feature": str(row.get("feature")),
                    "weight": float(row.get("weight", 0.0)),
                    "abs_weight": abs(float(row.get("weight", 0.0))),
                }
            )
    feature_df = pd.DataFrame(feature_rows)
    if not feature_df.empty:
        feature_df.to_csv(output_dir / "classifier_top_features.csv", index=False)
        _plot_feature_importance(feature_df, output_dir / "classifier_feature_importance.png")

    artifact_notes = []
    if model_path:
        try:
            model = joblib.load(model_path)
            classes = list(getattr(model, "classes_", []))
            (output_dir / "classifier_model_classes.json").write_text(json.dumps(classes, ensure_ascii=False, indent=2), encoding="utf-8")
            try:
                tfidf = model.named_steps["tfidf"]
                clf = model.named_steps["clf"]
                feature_names = tfidf.get_feature_names_out()
                model_feature_rows = []
                for idx, label in enumerate(classes or list(clf.classes_)):
                    weights = clf.coef_[idx]
                    top_idx = weights.argsort()[-FEATURE_IMPORTANCE_TOP_N:][::-1]
                    for i in top_idx:
                        model_feature_rows.append({
                            "label": label,
                            "feature": str(feature_names[i]),
                            "weight": float(weights[i]),
                            "abs_weight": abs(float(weights[i])),
                        })
                model_feature_df = pd.DataFrame(model_feature_rows)
                if not model_feature_df.empty and not (output_dir / "classifier_top_features.csv").exists():
                    model_feature_df.to_csv(output_dir / "classifier_top_features.csv", index=False)
                    _plot_feature_importance(model_feature_df, output_dir / "classifier_feature_importance.png")
            except Exception:
                artifact_notes.append("Unable to extract feature importance directly from the legacy classifier artifact.")
        except Exception:
            artifact_notes.append("Unable to inspect the legacy classifier artifact.")

    if not (output_dir / "classifier_confusion_matrix.png").exists():
        artifact_notes.append("Confusion matrix and ROC curves are unavailable in the current workspace because the original classifier dataset zip is missing.")

    summary = {
        "status": "legacy_metrics_only",
        "accuracy": float(metrics.get("accuracy", 0.0)),
        "macro_f1": float(metrics.get("macro_f1", metrics.get("classification_report", {}).get("macro avg", {}).get("f1-score", 0.0))),
        "weighted_f1": float(metrics.get("weighted_f1", metrics.get("classification_report", {}).get("weighted avg", {}).get("f1-score", 0.0))),
        "n_test": int(metrics.get("n_test", 0)),
        "note": "Classification dataset zip was not provided. Final package uses legacy classifier metrics and regenerates plots from available artifacts only.",
        "artifact_notes": artifact_notes,
    }
    if artifact_notes:
        (output_dir / "classifier_artifact_note.md").write_text(
            "# Classifier artifact notes\n\n" + "\n".join(f"- {note}" for note in artifact_notes) + "\n",
            encoding="utf-8",
        )
    (output_dir / "classifier_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "classifier_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def generate_classifier_report(dataset_zip: str | Path, model_path: str | Path, output_dir: Path) -> dict:
    df = load_curated_text_dataset(dataset_zip)
    _, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label"])
    X_test = test_df["text"].tolist()
    y_test = test_df["label"].tolist()
    model = joblib.load(model_path)
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)
    labels = list(model.classes_)
    (output_dir / "classifier_model_classes.json").write_text(json.dumps(labels, ensure_ascii=False, indent=2), encoding="utf-8")

    metrics = {
        "accuracy": float((pd.Series(y_test) == pd.Series(preds)).mean()),
        "classification_report": classification_report(y_test, preds, output_dict=True),
        "labels": labels,
        "confusion_matrix": confusion_matrix(y_test, preds, labels=labels).tolist(),
        "n_test": int(len(y_test)),
    }
    (output_dir / "classifier_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(metrics["confusion_matrix"], index=labels, columns=labels).to_csv(output_dir / "classifier_confusion_matrix.csv")
    _plot_confusion_matrix(labels, metrics["confusion_matrix"], output_dir / "classifier_confusion_matrix.png")

    roc_info = {}
    y_test_bin = pd.get_dummies(pd.Series(y_test)).reindex(columns=labels, fill_value=0)
    fig, ax = plt.subplots(figsize=(8, 8))
    for idx, label in enumerate(labels):
        try:
            auc = roc_auc_score(y_test_bin.iloc[:, idx], probs[:, idx])
            roc_info[label] = {"auc": float(auc)}
            RocCurveDisplay.from_predictions(y_test_bin.iloc[:, idx], probs[:, idx], name=label, ax=ax)
        except Exception:
            continue
    ax.set_title("Classifier ROC curves (OvR)")
    fig.tight_layout()
    fig.savefig(output_dir / "classifier_roc_curves.png", dpi=180)
    plt.close(fig)
    (output_dir / "classifier_roc_auc.json").write_text(json.dumps(roc_info, ensure_ascii=False, indent=2), encoding="utf-8")

    tfidf = model.named_steps["tfidf"]
    clf = model.named_steps["clf"]
    feature_names = tfidf.get_feature_names_out()
    feature_rows = []
    for idx, label in enumerate(labels):
        weights = clf.coef_[idx]
        top_idx = weights.argsort()[-FEATURE_IMPORTANCE_TOP_N:][::-1]
        for i in top_idx:
            feature_rows.append(
                {
                    "label": label,
                    "feature": str(feature_names[i]),
                    "weight": float(weights[i]),
                    "abs_weight": abs(float(weights[i])),
                }
            )
    feature_df = pd.DataFrame(feature_rows)
    feature_df.to_csv(output_dir / "classifier_top_features.csv", index=False)
    _plot_feature_importance(feature_df, output_dir / "classifier_feature_importance.png")

    macro_f1 = float(metrics["classification_report"].get("macro avg", {}).get("f1-score", 0.0))
    weighted_f1 = float(metrics["classification_report"].get("weighted avg", {}).get("f1-score", 0.0))
    summary = {
        "status": "ok",
        "accuracy": metrics["accuracy"],
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "n_test": metrics["n_test"],
    }
    (output_dir / "classifier_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def generate_surrogate_report(model_path: str | Path, output_dir: Path, n_samples: int = 600) -> dict:
    surrogate = SurrogateRegressor(model_path)
    df = build_reference_regression_dataset(n_samples)
    pred_rows = []
    for _, row in df.iterrows():
        pred = surrogate.predict(
            family=row["family"],
            subfamily=row["subfamily"],
            features={
                "resistance_ohm": row["resistance_ohm"],
                "capacitance_f": row["capacitance_f"],
                "inductance_h": row["inductance_h"],
                "voltage_ratio": row["voltage_ratio"],
                "power_ratio": row["power_ratio"],
                "current_ratio": row["current_ratio"],
                "pin_count": row["pin_count"],
                "contact_count": row["contact_count"],
                "frequency_hz": row["frequency_hz"],
            },
            qty=int(row["qty"]),
            operating_temp_c=float(row["temperature_c"]),
            quality=str(row["quality"]),
            environment=str(row["environment"]),
        )
        pred_rows.append(
            {
                "true_mtbf_hours": float(row["target_mtbf_hours"]),
                "predicted_mtbf_hours": float(pred["mtbf"]),
                "family": row["family"],
                "subfamily": row["subfamily"],
            }
        )
    pred_df = pd.DataFrame(pred_rows)
    pred_df["abs_error_hours"] = (pred_df["true_mtbf_hours"] - pred_df["predicted_mtbf_hours"]).abs()
    pred_df["error_hours"] = pred_df["predicted_mtbf_hours"] - pred_df["true_mtbf_hours"]
    pred_df["ape_pct"] = pred_df["abs_error_hours"] / pred_df["true_mtbf_hours"].clip(lower=1.0) * 100.0
    metrics = {
        "MAE_mtbf_hours": float(mean_absolute_error(pred_df["true_mtbf_hours"], pred_df["predicted_mtbf_hours"])),
        "RMSE_mtbf_hours": float(mean_squared_error(pred_df["true_mtbf_hours"], pred_df["predicted_mtbf_hours"]) ** 0.5),
        "R2": float(r2_score(pred_df["true_mtbf_hours"], pred_df["predicted_mtbf_hours"])),
        "MAPE_mtbf_pct": float(pred_df["ape_pct"].mean()),
        "median_APE_mtbf_pct": float(pred_df["ape_pct"].median()),
        "n_eval": int(len(pred_df)),
        "model_version": surrogate.metadata.model_version,
        "target_kind": surrogate.metadata.target_kind,
    }
    (output_dir / "surrogate_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    pred_df.nlargest(50, "abs_error_hours").to_csv(output_dir / "surrogate_top_errors.csv", index=False)
    family_df = pred_df.groupby("family")[["abs_error_hours", "ape_pct"]].mean().sort_values("ape_pct")
    family_df.to_csv(output_dir / "surrogate_family_error_breakdown.csv")

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(pred_df["true_mtbf_hours"], pred_df["predicted_mtbf_hours"], alpha=0.4)
    max_val = max(float(pred_df["true_mtbf_hours"].max()), float(pred_df["predicted_mtbf_hours"].max()))
    ax.plot([0.0, max_val], [0.0, max_val], linestyle="--")
    ax.set_xlabel("True MTBF, h")
    ax.set_ylabel("Predicted MTBF, h")
    ax.set_title("Random Forest surrogate: true vs predicted MTBF")
    fig.tight_layout()
    fig.savefig(output_dir / "surrogate_true_vs_predicted_mtbf.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(pred_df["true_mtbf_hours"], pred_df["error_hours"], alpha=0.4)
    ax.axhline(0.0, linestyle="--")
    ax.set_xlabel("True MTBF, h")
    ax.set_ylabel("Prediction error, h")
    ax.set_title("Random Forest surrogate residuals")
    fig.tight_layout()
    fig.savefig(output_dir / "surrogate_mtbf_residuals.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 6))
    family_plot = family_df.sort_values("ape_pct", ascending=True)
    ax.barh(family_plot.index.tolist(), family_plot["ape_pct"].tolist())
    ax.set_xlabel("Mean APE, %")
    ax.set_title("Surrogate MTBF error by family")
    fig.tight_layout()
    fig.savefig(output_dir / "surrogate_family_error_breakdown.png", dpi=180)
    plt.close(fig)
    return metrics


def write_summary(output_dir: Path, classifier_summary: dict[str, Any] | None, surrogate_summary: dict[str, Any] | None, notes: list[str] | None = None):
    lines = ["# ML evaluation report", ""]
    if notes:
        lines += ["## Notes", *[f"- {note}" for note in notes], ""]
    if classifier_summary:
        lines += [
            "## Classification",
            f"- Status: {classifier_summary['status']}",
            f"- Accuracy: {classifier_summary['accuracy']:.4f}",
            f"- Macro F1: {classifier_summary['macro_f1']:.4f}",
            f"- Weighted F1: {classifier_summary.get('weighted_f1', 0.0):.4f}",
            f"- Test rows: {classifier_summary['n_test']}",
            "",
        ]
    if surrogate_summary:
        lines += [
            "## Surrogate regression",
            f"- Model version: {surrogate_summary['model_version']}",
            f"- Target kind: {surrogate_summary['target_kind']}",
            f"- MAE MTBF, h: {surrogate_summary['MAE_mtbf_hours']:.6f}",
            f"- RMSE MTBF, h: {surrogate_summary['RMSE_mtbf_hours']:.6f}",
            f"- MAPE MTBF, %: {surrogate_summary['MAPE_mtbf_pct']:.6f}",
            f"- Median APE MTBF, %: {surrogate_summary['median_APE_mtbf_pct']:.6f}",
            f"- R²: {surrogate_summary['R2']:.6f}",
            f"- Evaluation rows: {surrogate_summary['n_eval']}",
            "",
        ]
    (output_dir / "evaluation_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--classifier-model")
    parser.add_argument("--dataset-zip")
    parser.add_argument("--legacy-classifier-metrics")
    parser.add_argument("--surrogate-model")
    parser.add_argument("--surrogate-eval-samples", type=int, default=600)
    args = parser.parse_args()

    output_dir = _ensure_dir(Path(args.output_dir))
    classifier_summary = None
    surrogate_summary = None
    notes: list[str] = []
    if args.classifier_model and args.dataset_zip:
        classifier_summary = generate_classifier_report(args.dataset_zip, args.classifier_model, output_dir)
    elif args.legacy_classifier_metrics:
        classifier_summary = _legacy_classifier_report(Path(args.legacy_classifier_metrics), args.classifier_model, output_dir)
        notes.append("Classifier section uses legacy metrics because the original training dataset zip is not available in the current workspace.")
    if args.surrogate_model:
        surrogate_summary = generate_surrogate_report(args.surrogate_model, output_dir, n_samples=args.surrogate_eval_samples)
    write_summary(output_dir, classifier_summary, surrogate_summary, notes=notes)


if __name__ == "__main__":
    main()
