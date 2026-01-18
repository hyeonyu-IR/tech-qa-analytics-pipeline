#!/usr/bin/env python3
"""
Monthly ingestion pipeline: transform one raw Tech-QA file and append to a master dataset.

Usage:
  python pipelines/monthly/tech_qa_transform.py --input <YYYY_MM.csv|xlsx> --master <master.csv> --outdir <outputs_dir>
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
import sys

import pandas as pd

# allow local imports when running as a script
sys.path.append(str(Path(__file__).resolve().parents[1]))  # pipelines/
from common import (
    REQUIRED_COLUMNS,
    harmonize_columns,
    parse_dept,
    parse_reason,
    classify_qa,
    normalize_procedure,
    compute_qa_id,
)

def infer_year_month_from_filename(path: Path) -> tuple[int, int]:
    m = re.search(r"(20\d{2})[_-](\d{2})", path.stem)
    if not m:
        raise ValueError(f"Cannot infer year/month from filename: {path.name}")
    return int(m.group(1)), int(m.group(2))

def load_raw(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in [".xlsx", ".xls"]:
        return pd.read_excel(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported file type: {path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--master", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    in_path = Path(args.input)
    master_path = Path(args.master)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    year, month = infer_year_month_from_filename(in_path)

    df_raw = harmonize_columns(load_raw(in_path))
    missing = [c for c in REQUIRED_COLUMNS if c not in df_raw.columns]
    if missing:
        raise ValueError(f"{in_path.name}: missing required columns {missing}. Found {list(df_raw.columns)}")

    if "Procedure" not in df_raw.columns:
        df_raw["Procedure"] = ""

    rows = []
    for i, rec in df_raw.iterrows():
        row = {k: ("" if pd.isna(rec.get(k, "")) else rec.get(k, "")) for k in REQUIRED_COLUMNS + ["Procedure"]}

        modality, site, location_detail, _ = parse_dept(row["Dept"])
        review_source, reason_code, reason_label, qa_sentiment = parse_reason(row["Reason"])
        qa_category, qa_subcategory, root_cause, severity, education_recommended, action_required, protocol_revision_flag, feedback_provided = classify_qa(
            reason_label, str(row["Comments"]), qa_sentiment
        )

        rows.append({
            "qa_id": compute_qa_id(row, year, month, i),
            "year": year,
            "month": month,
            "procedure_raw": str(row.get("Procedure", "")),
            "procedure_normalized": normalize_procedure(row.get("Procedure", "")),
            "dept_raw": str(row.get("Dept", "")),
            "modality": modality,
            "site": site,
            "location_detail": location_detail,
            "technologist": str(row.get("Technologist", "")),
            "reviewer_display": str(row.get("User", "")),
            "signing_physicians": str(row.get("Signing Physicians", "")),
            "review_source": review_source,
            "reason_code": reason_code,
            "reason_label": reason_label,
            "qa_sentiment": qa_sentiment,
            "qa_category": qa_category,
            "qa_subcategory": qa_subcategory,
            "root_cause": root_cause,
            "severity": int(severity),
            "education_recommended": bool(education_recommended),
            "action_required": bool(action_required),
            "protocol_revision_flag": bool(protocol_revision_flag),
            "feedback_provided": bool(feedback_provided),
            "reason_raw": str(row.get("Reason", "")),
            "comment_raw": str(row.get("Comments", "")),
        })

    df_struct = pd.DataFrame(rows)

    tag = f"{year}_{month:02d}"
    month_csv = outdir / f"Tech_QA_Structured_{tag}.csv"
    month_xlsx = outdir / f"Tech_QA_Structured_{tag}.xlsx"
    df_struct.to_csv(month_csv, index=False)
    with pd.ExcelWriter(month_xlsx, engine="openpyxl") as w:
        df_struct.to_excel(w, index=False, sheet_name="structured")

    if master_path.exists():
        df_master = pd.read_csv(master_path)
        df_master = pd.concat([df_master, df_struct], ignore_index=True)
    else:
        df_master = df_struct.copy()

    df_master = df_master.drop_duplicates(subset=["qa_id"], keep="last")
    df_master = df_master.sort_values(["year", "month", "qa_id"]).reset_index(drop=True)

    master_path.parent.mkdir(parents=True, exist_ok=True)
    df_master.to_csv(master_path, index=False)

    master_xlsx = master_path.with_suffix(".xlsx")
    with pd.ExcelWriter(master_xlsx, engine="openpyxl") as w:
        df_master.to_excel(w, index=False, sheet_name="master")

    print(f"Wrote: {month_csv} and updated master: {master_path} (rows={len(df_master)})")

if __name__ == "__main__":
    main()
