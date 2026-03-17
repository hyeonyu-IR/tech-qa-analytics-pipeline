"""
Common parsing and normalization utilities for Tech-QA pipelines.
"""
from __future__ import annotations

import hashlib
import re
from typing import Dict, Tuple

import pandas as pd

COL_ALIASES: Dict[str, str] = {
    "Appt Dept": "Dept",
    "Appointment Dept": "Dept",
    "Dept.": "Dept",
    "Tech Name": "Technologist",
    "Tech": "Technologist",
    "Technologist Name": "Technologist",
    "Reviewed By": "User",
    "Reviewer": "User",
    "Signing Physician": "Signing Physicians",
    "Signing Physician(s)": "Signing Physicians",
    "Signing Physicians (All)": "Signing Physicians",
    "Comment": "Comments",
    "QA Comment": "Comments",
}

REQUIRED_COLUMNS = ["Dept", "Technologist", "Reason", "Comments", "Signing Physicians", "User"]

_REASON_RE = re.compile(r"^(Tech Reviewed|Rad QA)\s*\(([A-Z])\)\s*(.*)$", re.IGNORECASE)

def harmonize_columns(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    rename = {c: COL_ALIASES[c] for c in df.columns if c in COL_ALIASES}
    if rename:
        df = df.rename(columns=rename)
    df = df.loc[:, ~pd.Index(df.columns).duplicated(keep="first")]
    return df

def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def normalize_procedure(proc) -> str:
    if proc is None or (isinstance(proc, float) and pd.isna(proc)):
        return ""
    s = normalize_whitespace(str(proc)).upper()
    for pat, rep in [
        (r"\bW\s*CONTRAST\b", "W/IV CONTRAST"),
        (r"\bW\s*IV\s*CONTRAST\s*ONLY\b", "W/IV CONTRAST"),
        (r"\bWITH\s*CONTRAST\b", "W/IV CONTRAST"),
        (r"\bWO\s*CONTRAST\b", "W/O CONTRAST"),
        (r"\bW\s*/\s*O\s*CONTRAST\b", "W/O CONTRAST"),
        (r"\bWITHOUT\s*CONTRAST\b", "W/O CONTRAST"),
        (r"\bW\s*WO\s*CONTRAST\b", "W/WO CONTRAST"),
        (r"\bW\s*/\s*WO\s*CONTRAST\b", "W/WO CONTRAST"),
        (r"\bWITH\s*AND\s*WITHOUT\s*CONTRAST\b", "W/WO CONTRAST"),
    ]:
        s = re.sub(pat, rep, s)
    return normalize_whitespace(s)

def parse_dept(dept) -> Tuple[str, str, str, str]:
    if dept is None or (isinstance(dept, float) and pd.isna(dept)):
        return "OTHER", "OTHER", "", ""
    raw = normalize_whitespace(str(dept)).upper()
    tokens = raw.split()

    modality = "OTHER"
    if "CT" in tokens:
        modality = "CT"
    elif "MRI" in tokens or "MR" in tokens:
        modality = "MR"
    elif "US" in tokens or "ULTRASOUND" in tokens:
        modality = "US"
    elif "DIAG" in tokens or "XR" in tokens or "X-RAY" in raw:
        modality = "XR"
    elif "FLUORO" in tokens or "FLUOR" in tokens or "FL" in tokens:
        modality = "FL"

    site = "OTHER"
    if "BLUE" in tokens and "2801" in tokens:
        site = "BLUE_2801"
    elif "ORTHO" in tokens and ("ACC" in tokens or "AMBULATORY" in tokens):
        site = "ORTHO_ACC"
    elif "HILLSBOROUGH" in tokens or "HBR" in tokens:
        site = "HBR"
    elif "NEUROSCIENCE" in tokens or "UNCNH" in tokens:
        site = "UNCNH"
    elif "CHILDRENS" in tokens or "UNCCH" in tokens:
        site = "UNCCH"
    elif "WOMENS" in tokens or "UNCW" in tokens:
        site = "UNCW"
    elif "EASTOWNE" in tokens:
        site = "EASTOWNE"
    elif "SPINE" in tokens and "CENTER" in tokens:
        site = "RLGH"
    else:
        for key in ["UNCNH", "HBR", "RLGH", "UNCCH", "UNCW", "EASTOWNE"]:
            if key in tokens:
                site = key
                break

    detail_tokens = tokens.copy()
    if detail_tokens and detail_tokens[0] == "IMG":
        detail_tokens = detail_tokens[1:]
    if detail_tokens and detail_tokens[0] in ["CT", "MRI", "MR", "US", "DIAG", "FLUORO", "XR"]:
        detail_tokens = detail_tokens[1:]
    location_detail = " ".join(detail_tokens).strip()

    return modality, site, location_detail, raw

def parse_reason(reason) -> Tuple[str, str | None, str, str]:
    if reason is None or (isinstance(reason, float) and pd.isna(reason)):
        return ("UNKNOWN", None, "", "Educational")
    raw = normalize_whitespace(str(reason))
    m = _REASON_RE.match(raw)
    if not m:
        return ("UNKNOWN", None, raw, "Educational")

    source = m.group(1).strip().upper().replace(" ", "_")
    code = m.group(2).upper()
    label = m.group(3).strip()

    if code == "A":
        sentiment = "Positive"
    elif code in ["G", "T"]:
        sentiment = "Educational"
    else:
        sentiment = "Corrective"

    return (source, code, label, sentiment)

def classify_qa(reason_label: str, comment: str, sentiment: str):
    r = (reason_label or "").lower()
    c = (comment or "").lower()

    qa_category = "Other"
    subcats = []
    root_cause = "Unknown"
    severity = 2

    if "good job" in r or sentiment == "Positive":
        qa_category = "Positive practice"
        subcats = ["Positive feedback"]
        root_cause = "N/A"
        severity = 1
    elif "suboptimal centering" in r and "fov" in r:
        qa_category = "Positioning"
        subcats = ["Centering", "FOV"]
        root_cause = "Technique"
    elif "incorrect positioning" in r:
        qa_category = "Positioning"
        subcats = ["Positioning"]
        root_cause = "Technique"
    elif "incorrect imaging protocol" in r:
        qa_category = "Protocol"
        subcats = ["Protocol deviation"]
        root_cause = "Protocol"
        severity = 3
    elif "mpr" in r or "post-processing" in r or "post processing" in r or "obliquit" in r:
        qa_category = "Post-processing"
        subcats = ["MPR / Reformats"]
        root_cause = "Technique"
    elif "expected views" in r or "not in pacs" in r or "images not in pacs" in r:
        qa_category = "Documentation-PACS"
        subcats = ["Missing images"]
        root_cause = "System"
        severity = 3
    elif "physics consult" in r:
        qa_category = "Artifact-Physics"
        subcats = ["Physics consult recommended"]
        root_cause = "System"
        severity = 3
    elif "other limitation not addressed" in r:
        qa_category = "Other"
        subcats = ["Other limitation"]

    if any(k in c for k in ["centering", "centered", "position", "positioning", "rotation", "rotated", "chin up", "chin down", "tilt", "angulation", "decub"]):
        if qa_category == "Other":
            qa_category = "Positioning"
        if ("centering" in c or "centered" in c) and "Centering" not in subcats:
            subcats.append("Centering")
        if "decub" in c and "Decubitus technique" not in subcats:
            subcats.append("Decubitus technique")
        if root_cause == "Unknown":
            root_cause = "Technique"

    if any(k in c for k in ["fov", "field of view", "coverage", "cut off", "cutoff", "missing anatomy", "not include", "not included"]):
        if "FOV / Coverage" not in subcats:
            subcats.append("FOV / Coverage")
        if root_cause == "Unknown":
            root_cause = "Technique"

    if any(k in c for k in ["pacs", "not in pacs", "not stacked", "not sent", "not transferred", "missing images", "series missing"]):
        qa_category = "Documentation-PACS"
        if "Missing images" not in subcats:
            subcats.append("Missing images")
        root_cause = "System"
        severity = max(severity, 3)

    if sentiment == "Corrective":
        severity = max(severity, 2)

    feedback_provided = bool(re.search(r"\b(shared with|reviewed with|discussed with|feedback)\b", c))
    education_recommended = sentiment in ["Educational", "Corrective"] or bool(re.search(r"\b(training|education)\b", c))
    action_required = (severity >= 3) or (qa_category in ["Protocol", "Documentation-PACS", "Artifact-Physics"])
    protocol_revision_flag = (qa_category == "Protocol" and severity >= 3)

    subcats = [normalize_whitespace(s) for s in subcats if s]
    subcats = list(dict.fromkeys(subcats))
    qa_subcategory = "; ".join(subcats)

    return qa_category, qa_subcategory, root_cause, severity, education_recommended, action_required, protocol_revision_flag, feedback_provided

def compute_qa_id(row: dict, year: int, month: int, idx: int) -> str:
    key = "|".join([
        str(year), str(month),
        str(row.get("Procedure", "")),
        str(row.get("Dept", "")),
        str(row.get("Technologist", "")),
        str(row.get("Reason", "")),
        str(row.get("Comments", "")),
        str(row.get("Signing Physicians", "")),
        str(row.get("User", "")),
        str(idx),
    ])
    h = hashlib.sha1(key.encode("utf-8", errors="ignore")).hexdigest()
    return f"qa_{year}{month:02d}_{h[:12]}"
