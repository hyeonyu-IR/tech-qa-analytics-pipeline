# Tech-QA Analytics Pipeline

A reproducible data-engineering and analytics pipeline for transforming unstructured technologist quality assurance (Tech-QA) logs into structured, longitudinal datasets for quality improvement, surveillance, and research.

## What it does
- Standardizes heterogeneous monthly QA logs
- Converts narrative comments into structured, analyzable variables
- Maintains a longitudinal master dataset (CSV/Excel)
- Generates longitudinal QA reports (PDF + chart images)
- Provides structural validation outputs (duplicates, missingness, monthly completeness)

## Repository Structure

```
tech-qa-analytics-pipeline/
├── pipelines/
│   ├── backfill/          # Historical reconstruction (rebuild master from many months)
│   └── monthly/           # Prospective monthly ingestion (append one month)
├── reporting/             # Automated QA reports
├── validation/            # Validation tools
├── data/
│   ├── raw_examples/      # De-identified sample raw logs (optional)
│   └── schema/            # Data dictionary
├── outputs/               # Local outputs (ignored by git)
├── docs/                  # Methods + governance documentation
├── environment.yml
└── .gitignore
```

## Quickstart

### Historical backfill (one-time)
```bash
python pipelines/backfill/tech_qa_backfill_master.py --inputs data/raw_examples --outdir outputs
```

### Monthly update (operational)
```bash
python pipelines/monthly/tech_qa_transform.py --input data/raw_new/2026_01.csv --master outputs/tech_qa_master.csv --outdir outputs
```

### Report generation
```bash
python reporting/tech_qa_make_report.py --master outputs/tech_qa_master.csv --outdir outputs/reports
```

### Structural validation
```bash
python validation/structural_validation.py --master outputs/tech_qa_master.csv --outdir outputs/validation
```

## Data Governance
Do **not** commit institutional QA logs or any PHI. Use de-identified examples only.
See: `docs/GOVERNANCE.md`.
