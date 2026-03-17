# Setup

This is a short setup guide for running the Tech-QA analytics pipeline on a new workstation.

## 1. Clone the repository

```powershell
git clone https://github.com/hyeonyu-IR/tech-qa-analytics-pipeline.git
cd tech-qa-analytics-pipeline
```

## 2. Create the conda environment

```powershell
conda env create -f environment.yml
conda activate tech-qa
```

If the environment already exists:

```powershell
conda activate tech-qa
```

## 3. Confirm the safe reference files exist

These are synthetic example files for testing the workflow:

- `data/raw_examples/2025_06_sample.csv`
- `outputs/examples/tech_qa_master_example.csv`

## 4. Run a test monthly transform

```powershell
python pipelines/monthly/tech_qa_transform.py --input data/raw_examples/2025_06_sample.csv --master outputs/tech_qa_master.csv --outdir outputs
```

This will create:

- `outputs/Tech_QA_Structured_2025_06.csv`
- `outputs/Tech_QA_Structured_2025_06.xlsx`
- `outputs/tech_qa_master.csv`
- `outputs/tech_qa_master.xlsx`

## 5. Generate a report

```powershell
python reporting/tech_qa_make_report.py --master outputs/tech_qa_master.csv --outdir outputs/reports
```

## 6. Run validation

```powershell
python validation/structural_validation.py --master outputs/tech_qa_master.csv --outdir outputs/validation
```

## 7. Operational monthly use

For a real monthly run, place the new raw file locally and name it like:

- `2026_03.csv`
- `2026_03.xlsx`

Then run:

```powershell
python pipelines/monthly/tech_qa_transform.py --input path/to/2026_03.csv --master outputs/tech_qa_master.csv --outdir outputs
python reporting/tech_qa_make_report.py --master outputs/tech_qa_master.csv --outdir outputs/reports
python validation/structural_validation.py --master outputs/tech_qa_master.csv --outdir outputs/validation
```

## Notes

- Do not commit institutional raw data, master datasets, backups, or generated reports.
- The repository is configured to ignore those sensitive files going forward.
- Keep local working data under ignored paths only.
