from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> dict:
    env = os.environ.copy()
    root = Path(__file__).resolve().parents[3]
    src = root / "src"
    env["PYTHONPATH"] = str(src) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return {
        "cmd": cmd,
        "returncode": int(proc.returncode),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--classifier-dataset-zip")
    parser.add_argument("--classifier-model", default="models/component_classifier.joblib")
    parser.add_argument("--surrogate-model", default="models/surrogate_regressor.joblib")
    parser.add_argument("--regression-samples", type=int, default=5000)
    parser.add_argument("--surrogate-eval-samples", type=int, default=300)
    parser.add_argument("--bom-file", action="append", default=[])
    args = parser.parse_args()

    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    report_dir = output_root / "ml_evaluation"
    audit_dir = output_root / "dataset_audit"
    lstm_dir = output_root / "lstm_experiment"
    summary = {"steps": []}

    if args.classifier_dataset_zip:
        summary["steps"].append(
            _run(
                [
                    sys.executable,
                    "-m",
                    "ekb_reliability.ml.train_classifier",
                    "--dataset-zip",
                    args.classifier_dataset_zip,
                    "--output",
                    args.classifier_model,
                    "--metrics-output",
                    str(report_dir / "classifier_metrics.json"),
                ]
            )
        )

    summary["steps"].append(
        _run(
            [
                sys.executable,
                "-m",
                "ekb_reliability.ml.train_surrogate",
                "--output",
                args.surrogate_model,
                "--metrics-output",
                str(report_dir / "surrogate_metrics.json"),
                "--n-samples",
                str(args.regression_samples),
            ]
        )
    )

    summary["steps"].append(
        _run([sys.executable, "-m", "ekb_reliability.ml.train_lstm", "--output-dir", str(lstm_dir)])
    )

    audit_cmd = [
        sys.executable,
        "-m",
        "ekb_reliability.ml.dataset_audit",
        "--output-dir",
        str(audit_dir),
        "--regression-samples",
        str(args.regression_samples),
    ]
    if args.classifier_dataset_zip:
        audit_cmd += ["--classifier-dataset-zip", args.classifier_dataset_zip]
    for bom in args.bom_file:
        audit_cmd += ["--bom-file", bom]
    summary["steps"].append(_run(audit_cmd))

    report_cmd = [
        sys.executable,
        "-m",
        "ekb_reliability.ml.generate_evaluation_report",
        "--output-dir",
        str(report_dir),
        "--surrogate-model",
        args.surrogate_model,
        "--surrogate-eval-samples",
        str(args.surrogate_eval_samples),
    ]
    if args.classifier_dataset_zip:
        report_cmd += ["--classifier-model", args.classifier_model, "--dataset-zip", args.classifier_dataset_zip]
    summary["steps"].append(_run(report_cmd))

    summary["ok"] = all(step["returncode"] == 0 for step in summary["steps"])
    (output_root / "training_suite_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
