# Monthly Run Manual

## Purpose
This manual defines the monthly operational workflow for Tech-QA ingestion, validation, reporting, and rollback safety.

## Scope
Applies to:
- Raw monthly Tech-QA file ingestion
- Structured monthly output generation
- Master dataset update
- Validation output review
- Monthly report package generation

## Prerequisites
1. Environment: `conda` environment `medimg`
2. Required packages: `pandas`, `openpyxl`, `matplotlib`, `reportlab`
3. Repository root:
`/Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline`

## Input File Rules
1. Filename format: `YYYY_MM.csv` or `YYYY_MM.xlsx` (example: `2026_02.csv`)
2. Place file in:
`/Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/data/raw_examples`
3. Required source columns (or recognized aliases):
- `Dept`
- `Technologist`
- `Reason`
- `Comments`
- `Signing Physicians`
- `User`

## Monthly Workflow
1. Backup current master before ingestion.
```bash
mkdir -p /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/backups
cp /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/tech_qa_master.csv \
   /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/backups/tech_qa_master_pre_update_$(date +%Y%m%d_%H%M%S).csv
```

2. Run monthly ingestion (example for February 2026).
```bash
conda run -n medimg python /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/pipelines/monthly/tech_qa_transform.py \
  --input /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/data/raw_examples/2026_02.csv \
  --master /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/tech_qa_master.csv \
  --outdir /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/outputs
```

3. Run structural validation.
```bash
conda run -n medimg python /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/validation/structural_validation.py \
  --master /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/tech_qa_master.csv \
  --outdir /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/outputs/validation
```

4. Generate monthly report package.
```bash
conda run -n medimg python /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/reporting/tech_qa_make_report.py \
  --master /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/tech_qa_master.csv \
  --outdir /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/reporting/2026_february
```

## Expected Outputs
1. Structured monthly files:
- `/outputs/Tech_QA_Structured_YYYY_MM.csv`
- `/outputs/Tech_QA_Structured_YYYY_MM.xlsx`

2. Updated master files:
- `/tech_qa_master.csv`
- `/tech_qa_master.xlsx`

3. Validation outputs:
- `/outputs/validation/structural_integrity_summary.csv`
- `/outputs/validation/missingness_key_fields.csv`
- `/outputs/validation/structural_validation_by_month.csv`

4. Report outputs:
- PDF report
- Trend PNG charts
- Positive technologist files in `CSV`, `XLSX`, and `PNG`

## QA Sign-Off Checklist
1. New month appears in `structural_validation_by_month.csv`
2. `duplicate_rows` is zero in `structural_integrity_summary.csv`
3. Report PDF and all PNG files open successfully
4. Positive technologist PNG shows clear bar labels and counts
5. No PHI-containing raw source files are committed to remote repository

## Rollback Procedure
If ingestion or rule changes need reversal:

1. Identify backup snapshot in:
`/Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/backups`

2. Restore previous master.
```bash
cp /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/backups/<backup_file>.csv \
   /Users/hyeonyu/Documents/miniconda_medimg_env/tech-qa-analytics-pipeline/tech_qa_master.csv
```

3. Re-run validation and reporting.

## Recommendations
1. Keep one immutable backup snapshot per monthly run.
2. Maintain a short change log for rule updates in `pipelines/common.py`.
3. For publication-quality QI reporting, add semantic validation with blinded dual-review and inter-rater agreement.
