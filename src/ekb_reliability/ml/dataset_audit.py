from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ekb_reliability.bom import inspect_bom_file, load_bom_file
from ekb_reliability.ml.dataset_builder import summarize_curated_text_dataset
from ekb_reliability.ml.synthetic import build_reference_regression_dataset


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def audit_classifier_dataset(dataset_zip: str | Path) -> dict:
    summary = summarize_curated_text_dataset(dataset_zip)
    summary["status"] = "ok"
    return summary


def audit_regression_dataset(n_samples: int = 5000) -> tuple[dict, pd.DataFrame]:
    df = build_reference_regression_dataset(n_samples)
    summary = {
        "status": "ok",
        "rows": int(len(df)),
        "families": {str(k): int(v) for k, v in df["family"].value_counts().to_dict().items()},
        "subfamilies": {str(k): int(v) for k, v in df["subfamily"].value_counts().to_dict().items()},
        "qualities": {str(k): int(v) for k, v in df["quality"].value_counts().to_dict().items()},
        "environments": {str(k): int(v) for k, v in df["environment"].value_counts().to_dict().items()},
        "mtbf_hours": {
            "min": float(df["target_mtbf_hours"].min()),
            "median": float(df["target_mtbf_hours"].median()),
            "max": float(df["target_mtbf_hours"].max()),
        },
    }
    return summary, df


def audit_bom_files(paths: list[str | Path]) -> list[dict]:
    results = []
    for path in paths:
        p = Path(path)
        info = inspect_bom_file(p)
        rows = load_bom_file(p)
        sheet_breakdown: dict[str, int] = {}
        if rows and rows[0].source_sheet:
            s = pd.Series([r.source_sheet or "(default)" for r in rows])
            sheet_breakdown = {str(k): int(v) for k, v in s.value_counts().to_dict().items()}
        results.append(
            {
                "path": str(p),
                "exists": p.exists(),
                "file_type": info.get("file_type"),
                "sheet_names": info.get("sheet_names", []),
                "detected_columns": info.get("detected_columns", {}),
                "rows_loaded": int(len(rows)),
                "sheet_breakdown": sheet_breakdown,
            }
        )
    return results


def write_markdown_report(output_dir: Path, summary: dict):
    lines = [
        "# Dataset audit",
        "",
        "## Classification dataset",
    ]
    cls = summary.get("classification_dataset")
    if cls:
        lines += [
            f"- Rows before deduplication: {cls['raw_rows']}",
            f"- Rows after deduplication: {cls['curated_rows']}",
            f"- Removed duplicates: {cls['duplicate_rows_removed']}",
            f"- Unique labels: {cls['unique_labels']}",
            "",
            "### Labels",
        ]
        for label, count in cls.get("labels", {}).items():
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- Classification dataset not provided.")

    reg = summary["regression_dataset"]
    lines += [
        "",
        "## Regression dataset",
        f"- Rows: {reg['rows']}",
        f"- MTBF range, h: {reg['mtbf_hours']['min']:.3f} .. {reg['mtbf_hours']['max']:.3f}",
        f"- Median MTBF, h: {reg['mtbf_hours']['median']:.3f}",
        "",
        "### Family distribution",
    ]
    for family, count in reg.get("families", {}).items():
        lines.append(f"- {family}: {count}")

    if summary.get("bom_files"):
        lines += ["", "## BOM samples"]
        for item in summary["bom_files"]:
            lines.append(f"- {item['path']}: {item['rows_loaded']} rows")
            if item.get("sheet_breakdown"):
                for sheet, count in item["sheet_breakdown"].items():
                    lines.append(f"  - {sheet}: {count}")

    (output_dir / "dataset_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--classifier-dataset-zip")
    parser.add_argument("--regression-samples", type=int, default=5000)
    parser.add_argument("--bom-file", action="append", default=[])
    args = parser.parse_args()

    output_dir = _ensure_dir(Path(args.output_dir))
    summary: dict = {}
    if args.classifier_dataset_zip:
        summary["classification_dataset"] = audit_classifier_dataset(args.classifier_dataset_zip)
    reg_summary, reg_df = audit_regression_dataset(args.regression_samples)
    summary["regression_dataset"] = reg_summary
    reg_df.to_csv(output_dir / "regression_dataset_sample.csv", index=False)
    if args.bom_file:
        summary["bom_files"] = audit_bom_files(args.bom_file)
    (output_dir / "dataset_audit.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(output_dir, summary)


if __name__ == "__main__":
    main()
