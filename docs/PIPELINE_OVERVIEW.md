# Pipeline Overview

This repository implements a modular QA analytics architecture with clear separation of concerns.

## 1) Backfill Pipeline (`pipelines/backfill/`)
Rebuilds the master dataset from multiple historical monthly logs. Use this for retrospective reconstruction or when you obtain older months that must be integrated consistently.

## 2) Monthly Ingestion Pipeline (`pipelines/monthly/`)
Transforms a single new monthly raw log and appends it to the master dataset. Use this for routine operations going forward.

## 3) Reporting (`reporting/`)
Generates a longitudinal PDF report and associated charts from the master dataset.

## 4) Validation (`validation/`)
Performs structural validation (duplicates, missingness, monthly completeness). A semantic-validation scaffold is included for expert agreement studies.
