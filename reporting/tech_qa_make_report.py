#!/usr/bin/env python3
"""
tech_qa_make_report_v3.py

Generate a PDF report + charts from a Tech_QA master CSV.
Designed for longitudinal (multi-month) datasets.

Usage:
  python tech_qa_make_report_v3.py --master /path/to/tech_qa_master.csv --outdir /path/to/out
"""
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

def save_bar(series, title, xlabel, ylabel, out_png, top_n=20):
    s = series.copy()
    if top_n and len(s) > top_n:
        s = s.head(top_n)
    plt.figure(figsize=(10, 5))
    s.plot(kind="bar")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()

def save_line(df, xcol, ycol, title, xlabel, ylabel, out_png):
    plt.figure(figsize=(10, 5))
    plt.plot(df[xcol], df[ycol], marker="o")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()

def add_page_title(c, title, subtitle):
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 740, title)
    c.setFont("Helvetica", 10)
    c.drawString(72, 722, subtitle)

def add_image_page(c, title, subtitle, img_path):
    add_page_title(c, title, subtitle)
    img = ImageReader(str(img_path))
    w, h = img.getSize()
    max_w, max_h = 468, 520  # within letter margins
    scale = min(max_w / w, max_h / h)
    draw_w, draw_h = w * scale, h * scale
    x = 72
    y = 180
    c.drawImage(img, x, y, width=draw_w, height=draw_h, preserveAspectRatio=True, mask="auto")
    c.showPage()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    master_path = Path(args.master)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(master_path)
    df["year_month"] = df.apply(lambda r: f"{int(r['year']):04d}-{int(r['month']):02d}", axis=1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"Tech_QA_Report_{ts}"

    # --- Aggregations
    monthly_total = df.groupby("year_month")["qa_id"].count().rename("total").sort_index()
    monthly_modality = df.groupby(["year_month", "modality"])["qa_id"].count().reset_index(name="count")
    monthly_site = df.groupby(["year_month", "site"])["qa_id"].count().reset_index(name="count")
    monthly_category = df.groupby(["year_month", "qa_category"])["qa_id"].count().reset_index(name="count")
    monthly_reviewer = df.groupby(["year_month", "reviewer_display"])["qa_id"].count().reset_index(name="count")

    # --- Charts
    png_total = outdir / f"{prefix}_01_total.png"
    save_line(monthly_total.reset_index(), "year_month", "total",
              "Monthly total Tech_QA volume", "Month", "Count", png_total)

    # For multi-month trends per modality/site/category/reviewer, use stacked bar-ish via top-N series per month
    # Here: create a "top overall" list then pivot to line charts for clarity when time grows.
    def top_items(col, n=6):
        return df[col].value_counts().head(n).index.tolist()

    for label, col, fname, ylab in [
        ("Modality", "modality", "02_modality_trends.png", "Count"),
        ("Site", "site", "03_site_trends.png", "Count"),
        ("Issue category", "qa_category", "04_category_trends.png", "Count"),
        ("Reviewer (Radiologist)", "reviewer_display", "05_reviewer_trends.png", "Count"),
    ]:
        top = top_items(col, n=6)
        pivot = (df[df[col].isin(top)]
                 .groupby(["year_month", col])["qa_id"].count()
                 .reset_index()
                 .pivot(index="year_month", columns=col, values="qa_id")
                 .fillna(0)
                 .sort_index())
        plt.figure(figsize=(10, 5))
        for k in pivot.columns:
            plt.plot(pivot.index, pivot[k], marker="o", label=str(k))
        plt.title(f"Monthly trend by {label} (top 6 overall)")
        plt.xlabel("Month")
        plt.ylabel(ylab)
        plt.xticks(rotation=45, ha="right")
        plt.legend(fontsize=8, loc="best")
        plt.tight_layout()
        out_png = outdir / f"{prefix}_{fname}"
        plt.savefig(out_png, dpi=200)
        plt.close()

    # Positive technologists table
    pos = df[df["qa_sentiment"].astype(str).str.lower() == "positive"].copy()
    pos_counts = (pos.groupby("technologist")["qa_id"].count()
                  .sort_values(ascending=False)
                  .rename("positive_count")
                  .reset_index())
    pos_csv = outdir / f"{prefix}_positive_technologists.csv"
    pos_counts.to_csv(pos_csv, index=False)

    # --- PDF assembly
    pdf_path = outdir / f"{prefix}.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    subtitle = f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Source: {master_path.name} | Rows: {len(df)}"

    add_page_title(c, "Tech_QA Longitudinal Report", subtitle)
    c.setFont("Helvetica", 11)
    c.drawString(72, 690, "Contents")
    c.setFont("Helvetica", 10)
    items = [
        "1) Monthly total volume",
        "2) Monthly trend by modality (top 6 overall)",
        "3) Monthly trend by site (top 6 overall)",
        "4) Monthly trend by issue category (top 6 overall)",
        "5) Monthly trend by reviewer (top 6 overall)",
        "6) Positive technologists (CSV output)",
    ]
    y = 670
    for it in items:
        c.drawString(92, y, f"- {it}")
        y -= 16
    c.drawString(72, 540, f"Positive technologists table saved as: {pos_csv.name}")
    c.showPage()

    add_image_page(c, "Monthly total Tech_QA volume", subtitle, png_total)
    for fname, title in [
        ("02_modality_trends.png", "Monthly trend by Modality (top 6 overall)"),
        ("03_site_trends.png", "Monthly trend by Site (top 6 overall)"),
        ("04_category_trends.png", "Monthly trend by Issue category (top 6 overall)"),
        ("05_reviewer_trends.png", "Monthly trend by Reviewer (top 6 overall)"),
    ]:
        add_image_page(c, title, subtitle, outdir / f"{prefix}_{fname}")

    c.save()

    print(str(pdf_path))
    print(str(pos_csv))

if __name__ == "__main__":
    main()
