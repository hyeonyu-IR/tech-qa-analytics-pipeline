#!/usr/bin/env python3
"""
Historical backfill pipeline: rebuild the master dataset from multiple monthly raw files.

Usage:
  python pipelines/backfill/tech_qa_backfill_master.py --inputs <folder> --outdir <outputs_dir>
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
import sys

import pandas as pd

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
    ap.add_argument("--inputs", required=True, help="Folder with monthly raw files named YYYY_MM.csv/xlsx")
    ap.add_argument("--outdir", required=True, help="Output directory")
    args = ap.parse_args()

    in_dir = Path(args.inputs)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    files = sorted([p for p in in_dir.iterdir() if re.match(r"^20\d{2}[_-]\d{2}\.(csv|xlsx|xls)$", p.name, re.IGNORECASE)])
    if not files:
        raise SystemExit("No monthly files found. Expect names like YYYY_MM.csv or YYYY_MM.xlsx")

    skipped = []
    all_structured = []

    for path in files:
        try:
            year, month = infer_year_month_from_filename(path)
            df_raw = harmonize_columns(load_raw(path))
        except Exception as e:
            skipped.append({"raw_file": path.name, "reason": f"read_failed: {e}"})
            continue

        missing = [c for c in REQUIRED_COLUMNS if c not in df_raw.columns]
        if missing:
            skipped.append({"raw_file": path.name, "reason": f"missing_required_columns: {missing}", "found_columns": list(df_raw.columns)})
            continue

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
        df_struct.to_csv(outdir / f"Tech_QA_Structured_{tag}.csv", index=False)
        with pd.ExcelWriter(outdir / f"Tech_QA_Structured_{tag}.xlsx", engine="openpyxl") as w:
            df_struct.to_excel(w, index=False, sheet_name="structured")

        all_structured.append(df_struct)

    if not all_structured:
        raise SystemExit("No valid monthly files were ingested.")

    master = pd.concat(all_structured, ignore_index=True).drop_duplicates(subset=["qa_id"], keep="last")
    master = master.sort_values(["year", "month", "qa_id"]).reset_index(drop=True)

    master_csv = outdir / "tech_qa_master.csv"
    master_xlsx = outdir / "tech_qa_master.xlsx"
    master.to_csv(master_csv, index=False)
    with pd.ExcelWriter(master_xlsx, engine="openpyxl") as w:
        master.to_excel(w, index=False, sheet_name="master")

    pd.DataFrame(skipped).to_csv(outdir / "backfill_qc_skipped_files.csv", index=False)

    print(f"Built master: {master_csv} (rows={len(master)})")

if __name__ == "__main__":
    main()
