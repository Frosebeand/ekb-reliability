from __future__ import annotations

import io
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd

from ekb_reliability.taxonomy import RAW_CATEGORY_TO_TAXONOMY


def iter_curated_text_rows(zip_path: str | Path):
    zip_path = Path(zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            file_name = Path(name).name
            if file_name not in RAW_CATEGORY_TO_TAXONOMY:
                continue
            family, subfamily = RAW_CATEGORY_TO_TAXONOMY[file_name]
            if not file_name.endswith(".csv"):
                continue
            df = pd.read_csv(io.BytesIO(zf.read(name)))
            if "Description" not in df.columns:
                continue
            for desc in df["Description"].dropna():
                yield {
                    "text": str(desc),
                    "family": family,
                    "subfamily": subfamily,
                    "label": f"{family}::{subfamily}",
                    "source_file": file_name,
                }


def load_curated_text_dataset(zip_path: str | Path) -> pd.DataFrame:
    rows = list(iter_curated_text_rows(zip_path))
    out = pd.DataFrame(rows).drop_duplicates(subset=["text", "label"]).reset_index(drop=True)
    return out


def summarize_curated_text_dataset(zip_path: str | Path) -> dict:
    raw_rows = list(iter_curated_text_rows(zip_path))
    raw_df = pd.DataFrame(raw_rows)
    if raw_df.empty:
        return {
            "raw_rows": 0,
            "curated_rows": 0,
            "duplicate_rows_removed": 0,
            "unique_labels": 0,
            "source_files": {},
            "labels": {},
        }
    curated_df = raw_df.drop_duplicates(subset=["text", "label"]).reset_index(drop=True)
    return {
        "raw_rows": int(len(raw_df)),
        "curated_rows": int(len(curated_df)),
        "duplicate_rows_removed": int(len(raw_df) - len(curated_df)),
        "unique_labels": int(curated_df["label"].nunique()),
        "source_files": {str(k): int(v) for k, v in Counter(curated_df["source_file"]).most_common()},
        "labels": {str(k): int(v) for k, v in Counter(curated_df["label"]).most_common()},
    }


def augment_bom_style_text(text: str) -> list[str]:
    t = text
    variants = {
        t,
        t.lower(),
        t.replace(",", " "),
        t.replace(" ±", " +/-"),
        t.replace("CERAMIC", "CER"),
        t.replace("CAPACITOR", "CAP"),
        t.replace("RESISTOR", "RES"),
        t.replace(" OHM", "R"),
    }
    return [v for v in variants if v]
