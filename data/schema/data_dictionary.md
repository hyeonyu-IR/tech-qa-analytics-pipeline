# Tech_QA_Structured v1.0 — Data Dictionary

This dictionary defines the columns produced by `tech_qa_transform.py`. The model is designed for longitudinal QA trend analysis while preserving the original narrative fields for auditability.

## Identity & Time
- **qa_id** (string): Deterministic identifier (`qa_YYYYMM_<hash>`). Used for de-duplication across re-runs.
- **year** (int): Parsed from file name `YYYY_MM.xlsx` (fallback: current year).
- **month** (int): Parsed from file name `YYYY_MM.xlsx` (fallback: current month).

## Exam & Location
- **procedure_raw** (text): Original `Procedure` field.
- **procedure_normalized** (text): Uppercased and standardized contrast wording (e.g., `W/IV CONTRAST`, `W/O CONTRAST`, `W/WO CONTRAST`).
- **dept_raw** (text): Original `Dept` field.
- **modality** (categorical): One of `CT`, `MR`, `US`, `XR`, `FL`, `OTHER` derived from `dept_raw`.
- **site** (categorical): Normalized site derived from `dept_raw` (e.g., `UNCNH`, `HBR`, `RLGH`, `UNCCH`, `UNCW`, `EASTOWNE`, `BLUE_2801`, `ORTHO_ACC`, `OTHER`).
- **location_detail** (text): Remaining Dept tokens after removing leading `IMG` and the modality token.

## Personnel
- **technologist** (text): From source `Technologist`.
- **reviewer_display** (text): From source `User` (as logged).
- **signing_physicians** (text): From source `Signing Physicians` (preserved as-is).

## QA Signal & Classification
- **review_source** (categorical): `TECH_REVIEWED`, `RAD_QA`, or `UNKNOWN` derived from `Reason`.
- **reason_code** (categorical): Single-letter code in `Reason` parentheses, if present (e.g., `A`, `G`, `T`, `F`, ...).
- **reason_label** (text): Text following the code in `Reason` (trimmed).
- **qa_sentiment** (categorical): `Positive`, `Educational`, or `Corrective` (rule-based from `reason_code` and label).
- **qa_category** (categorical): High-level domain, e.g. `Positioning`, `Protocol`, `Post-processing`, `Documentation-PACS`, `Artifact-Physics`, `Positive practice`, `Other`.
- **qa_subcategory** (text): Semi-colon delimited sublabels (multi-label allowed), derived from controlled-vocabulary rules.
- **root_cause** (categorical): `Technique`, `Protocol`, `Training`, `System`, `Communication`, `Unknown`, `N/A`.
- **severity** (int): Ordinal 1–3 (1=informational/positive; 2=educational; 3=potential clinical impact/system failure).

## Actionability Flags
- **education_recommended** (bool): True if educational/corrective sentiment or training/feedback language detected.
- **action_required** (bool): True if severity ≥ 3 or category implies operational follow-up.
- **protocol_revision_flag** (bool): True for high-severity protocol deviations (v1.0 heuristic).
- **feedback_provided** (bool): True if comment contains “shared with”, “reviewed with”, “feedback”, “discussed with”.

## Raw Text Preservation
- **reason_raw** (text): Original Reason (verbatim).
- **comment_raw** (text): Original Comments (verbatim; empty string if missing).
