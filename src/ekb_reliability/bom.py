from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ekb_reliability.schemas import BOMRow
from ekb_reliability.utils import is_missing

CANONICAL_COLUMN_ALIASES = {
    "raw_description": ["description", "desc", "component description", "part description"],
    "manufacturer": ["mfg name", "manufacturer", "vendor", "brand"],
    "mpn": ["manufacturer part number", "mfg part number", "mpn", "part number", "manufacturer p/n"],
    "qty": ["qty", "quantity", "count", "qty2"],
    "ref_designator": ["ref designator", "reference", "refdes", "refs"],
}


def _normalize_column(col: str) -> str:
    return str(col).strip().lower()


def infer_column_mapping(columns: list[str]) -> dict[str, str]:
    normalized = {_normalize_column(c): c for c in columns}
    mapping: dict[str, str] = {}
    for target, aliases in CANONICAL_COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[target] = normalized[alias]
                break
    return mapping


def inspect_bom_file(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    info: dict[str, Any] = {
        "file_name": path.name,
        "suffix": path.suffix.lower(),
        "sheet_names": [],
        "sheet_info": [],
    }

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        mapping = infer_column_mapping(list(df.columns))
        info["sheet_info"].append(
            {
                "sheet_name": None,
                "row_count": int(len(df)),
                "column_count": int(len(df.columns)),
                "columns": [str(c) for c in df.columns],
                "column_mapping": mapping,
                "is_bom_like": "raw_description" in mapping,
            }
        )
        return info

    if path.suffix.lower() == ".xlsx":
        xls = pd.ExcelFile(path)
        info["sheet_names"] = list(xls.sheet_names)
        for sheet in xls.sheet_names:
            df = pd.read_excel(path, sheet_name=sheet)
            mapping = infer_column_mapping(list(df.columns))
            info["sheet_info"].append(
                {
                    "sheet_name": sheet,
                    "row_count": int(len(df)),
                    "column_count": int(len(df.columns)),
                    "columns": [str(c) for c in df.columns],
                    "column_mapping": mapping,
                    "is_bom_like": "raw_description" in mapping,
                }
            )
        return info

    raise ValueError(f"Unsupported file type: {path.suffix}")


def dataframe_to_bom_rows(df: pd.DataFrame, source_file: str, source_sheet: str | None = None) -> list[BOMRow]:
    mapping = infer_column_mapping(list(df.columns))
    if "raw_description" not in mapping:
        return []

    rows: list[BOMRow] = []
    for idx, record in df.iterrows():
        raw_desc = record.get(mapping["raw_description"])
        if is_missing(raw_desc):
            continue

        qty = record.get(mapping.get("qty", ""), 1) if mapping.get("qty") else 1
        try:
            qty_int = int(float(qty))
        except Exception:
            qty_int = 1

        row = BOMRow(
            source_file=source_file,
            source_sheet=source_sheet,
            row_index=int(idx),
            raw_description=str(raw_desc),
            manufacturer=None if not mapping.get("manufacturer") else str(record.get(mapping["manufacturer"])) if not is_missing(record.get(mapping["manufacturer"])) else None,
            mpn=None if not mapping.get("mpn") else str(record.get(mapping["mpn"])) if not is_missing(record.get(mapping["mpn"])) else None,
            qty=max(qty_int, 1),
            ref_designator=None if not mapping.get("ref_designator") else str(record.get(mapping["ref_designator"])) if not is_missing(record.get(mapping["ref_designator"])) else None,
            extra={str(k): (None if is_missing(v) else v) for k, v in record.to_dict().items()},
        )
        rows.append(row)
    return rows


def load_bom_file(path: str | Path, selected_sheets: list[str] | None = None) -> list[BOMRow]:
    path = Path(path)
    rows: list[BOMRow] = []

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        rows.extend(dataframe_to_bom_rows(df, source_file=path.name))
        return rows

    if path.suffix.lower() == ".xlsx":
        xls = pd.ExcelFile(path)
        allowed = set(selected_sheets or xls.sheet_names)
        for sheet in xls.sheet_names:
            if sheet not in allowed:
                continue
            df = pd.read_excel(path, sheet_name=sheet)
            sheet_rows = dataframe_to_bom_rows(df, source_file=path.name, source_sheet=sheet)
            rows.extend(sheet_rows)
        return rows

    raise ValueError(f"Unsupported file type: {path.suffix}")
