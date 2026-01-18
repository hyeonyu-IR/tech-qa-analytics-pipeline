#!/usr/bin/env python3
"""
Structural validation for Tech-QA master dataset.

Usage:
  python validation/structural_validation.py --master outputs/tech_qa_master.csv --outdir outputs/validation
"""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

KEY_FIELDS = [
    "qa_id","year","month","dept_raw","modality","site","technologist",
    "reviewer_display","reason_raw","comment_raw","qa_category","qa_sentiment"
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    master_path = Path(args.master)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(master_path)

    integrity = pd.DataFrame([{
        "master_file": master_path.name,
        "total_rows": int(len(df)),
        "unique_qa_id": int(df["qa_id"].nunique()) if "qa_id" in df.columns else None,
        "duplicate_rows": int(len(df) - df["qa_id"].nunique()) if "qa_id" in df.columns else None,
    }])
    integrity.to_csv(outdir / "structural_integrity_summary.csv", index=False)

    miss = []
    for col in KEY_FIELDS:
        if col in df.columns:
            miss.append({
                "field": col,
                "missing_count": int(df[col].isna().sum()),
                "missing_rate": float(df[col].isna().mean()),
            })
    pd.DataFrame(miss).to_csv(outdir / "missingness_key_fields.csv", index=False)

    if set(["year","month"]).issubset(df.columns):
        df["year_month"] = df.apply(lambda r: f"{int(r['year']):04d}-{int(r['month']):02d}", axis=1)
        monthly = df.groupby("year_month")["qa_id"].count().rename("rows").reset_index().sort_values("year_month")
        monthly.to_csv(outdir / "structural_validation_by_month.csv", index=False)

    print(f"Wrote validation outputs to: {outdir.resolve()}")

if __name__ == "__main__":
    main()
