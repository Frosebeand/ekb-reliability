from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], root: Path) -> dict:
    env = os.environ.copy()
    src = root / "src"
    env["PYTHONPATH"] = str(src) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=root, env=env)
    return {
        "cmd": cmd,
        "returncode": int(proc.returncode),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _write_summary(summary_dir: Path, run_log: dict, classifier_status: str, surrogate_metrics: dict | None, lstm_summary: dict | None):
    lines = [
        "# Final release summary",
        "",
        "## Sections",
        f"- Classifier: {classifier_status}",
        f"- Surrogate MTBF: {'ok' if surrogate_metrics else 'missing'}",
        f"- LSTM: {lstm_summary.get('status') if lstm_summary else 'missing'}",
        "",
    ]
    if surrogate_metrics:
        lines += [
            "## Surrogate MTBF metrics",
            f"- MAE, h: {surrogate_metrics['MAE_mtbf_hours']:.6f}",
            f"- RMSE, h: {surrogate_metrics['RMSE_mtbf_hours']:.6f}",
            f"- MAPE, %: {surrogate_metrics['MAPE_mtbf_pct']:.6f}",
            f"- Median APE, %: {surrogate_metrics['median_APE_mtbf_pct']:.6f}",
            f"- R²: {surrogate_metrics['R2']:.6f}",
            "",
        ]
    if lstm_summary:
        lines += ["## LSTM", f"- Status: {lstm_summary.get('status')}"]
        if lstm_summary.get("status") == "ok":
            lines += [
                f"- Test MAE: {lstm_summary.get('test_mae', 0.0):.6f}",
                f"- Test RMSE: {lstm_summary.get('test_rmse', 0.0):.6f}",
            ]
        else:
            lines += [f"- Note: {lstm_summary.get('note', '')}"]
        lines += [""]
    lines += [
        "## Reproducibility",
        "- Final release artifacts are collected under reports/final_release/.",
        "- Intermediate report folders remain historical and should not be treated as final.",
        "",
        "## Run log",
        f"- Steps executed: {len(run_log.get('steps', []))}",
        f"- Overall status: {'ok' if run_log.get('ok') else 'has_failures'}",
        "",
    ]
    (summary_dir / "final_metrics_summary.md").write_text("\n".join(lines), encoding="utf-8")
    (summary_dir / "final_release_run_log.json").write_text(json.dumps(run_log, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="reports/final_release")
    parser.add_argument("--classifier-dataset-zip")
    parser.add_argument("--classifier-model", default="models/component_classifier.joblib")
    parser.add_argument("--legacy-classifier-metrics", default="artifacts/archive_legacy/data/classifier_metrics.json")
    parser.add_argument("--surrogate-model", default="models/surrogate_regressor.joblib")
    parser.add_argument("--surrogate-train-samples", type=int, default=8000)
    parser.add_argument("--surrogate-eval-samples", type=int, default=800)
    parser.add_argument("--lstm-samples", type=int, default=1200)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[3]
    output_root = root / args.output_root
    classifier_dir = output_root / "classifier"
    surrogate_dir = output_root / "surrogate_mtbf"
    lstm_dir = output_root / "lstm"
    summary_dir = output_root / "summary"
    for path in [classifier_dir, surrogate_dir, lstm_dir, summary_dir]:
        path.mkdir(parents=True, exist_ok=True)

    run_log = {"steps": []}

    run_log["steps"].append(
        _run(
            [
                sys.executable,
                "-m",
                "ekb_reliability.ml.train_surrogate",
                "--output",
                args.surrogate_model,
                "--metrics-output",
                str(surrogate_dir / "surrogate_train_metrics.json"),
                "--n-samples",
                str(args.surrogate_train_samples),
            ],
            root,
        )
    )

    report_cmd = [
        sys.executable,
        "-m",
        "ekb_reliability.ml.generate_evaluation_report",
        "--output-dir",
        str(surrogate_dir),
        "--surrogate-model",
        args.surrogate_model,
        "--surrogate-eval-samples",
        str(args.surrogate_eval_samples),
    ]
    classifier_status = "missing"
    if args.classifier_dataset_zip:
        report_cmd += [
            "--classifier-model",
            args.classifier_model,
            "--dataset-zip",
            args.classifier_dataset_zip,
        ]
        classifier_status = "fresh"
    else:
        report_cmd += [
            "--classifier-model",
            args.classifier_model,
            "--legacy-classifier-metrics",
            args.legacy_classifier_metrics,
        ]
        classifier_status = "legacy"
    run_log["steps"].append(_run(report_cmd, root))

    for name in [
        "classifier_metrics.json",
        "classifier_summary.json",
        "classifier_confusion_matrix.csv",
        "classifier_confusion_matrix.png",
        "classifier_roc_auc.json",
        "classifier_roc_curves.png",
        "classifier_top_features.csv",
        "classifier_feature_importance.png",
        "classifier_model_classes.json",
    ]:
        src = surrogate_dir / name
        if src.exists():
            shutil.move(str(src), str(classifier_dir / name))

    run_log["steps"].append(
        _run(
            [
                sys.executable,
                "-m",
                "ekb_reliability.ml.train_lstm",
                "--output-dir",
                str(lstm_dir),
                "--n-samples",
                str(args.lstm_samples),
            ],
            root,
        )
    )

    run_log["ok"] = all(step["returncode"] == 0 for step in run_log["steps"])

    surrogate_metrics = None
    if (surrogate_dir / "surrogate_metrics.json").exists():
        surrogate_metrics = json.loads((surrogate_dir / "surrogate_metrics.json").read_text(encoding="utf-8"))
    lstm_summary = None
    if (lstm_dir / "lstm_summary.json").exists():
        lstm_summary = json.loads((lstm_dir / "lstm_summary.json").read_text(encoding="utf-8"))

    _write_summary(summary_dir, run_log, classifier_status, surrogate_metrics, lstm_summary)


if __name__ == "__main__":
    main()
