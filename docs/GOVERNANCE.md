# Data Governance and Safety

## Do not commit institutional data
- Do not commit raw QA logs
- Do not commit any protected health information (PHI)
- Prefer de-identified examples for demonstration

## Operational separation
Historical backfill and prospective monthly ingestion are implemented as separate pipelines to prevent:
- Data duplication
- Chronological corruption
- Retrospective contamination of prospective datasets

## Intended use
This pipeline supports non-punitive quality improvement and educational feedback. It is not intended for individual performance evaluation.

## Institutional responsibility
Users are responsible for IRB/QI oversight and compliance with institutional policies.
