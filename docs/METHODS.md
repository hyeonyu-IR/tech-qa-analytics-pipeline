# Methods Summary

## Data sources
Monthly technologist QA logs are obtained as spreadsheets generated during routine radiology QA activities. These logs contain both structured metadata and unstructured narrative comments.

## Data ingestion and harmonization
Two deterministic pipelines are implemented: (1) historical backfill and (2) prospective monthly ingestion. Both standardize heterogeneous column naming conventions and normalize free-text fields using rule-based parsing.

## Structured variable derivation
Narrative QA comments are transformed into structured variables including modality/site, QA category/subcategory, sentiment, root cause, severity tier, and action flags. Classification rules are iteratively refined with domain expert review to maintain clinical relevance while preserving reproducibility.

## Longitudinal master dataset
All records are stored in a single master table indexed by a deterministic QA identifier derived from stable row attributes, supporting lossless ingestion, duplicate prevention, and auditability.

## Reporting
Automated scripts generate longitudinal visualizations (monthly volume, trends by modality/site/category/reviewer) and recognition tables for positive technologist feedback.

## Validation
Structural validation outputs quantify duplicates, missingness, and month-level completeness. The repository includes a scaffold for semantic validation using expert review and agreement metrics.
