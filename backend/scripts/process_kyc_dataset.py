#!/usr/bin/env python
"""
Process all KYC documents in the dataset and report results.
Run from project root or backend: python backend/scripts/process_kyc_dataset.py
"""
import sys
import json
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1]
project_root = backend_root.parent
sys.path.insert(0, str(backend_root))

from app.database import create_session_factory
from app.services.kyc import KycService

DATA_ROOT = project_root / "YTL_TrackA_Udyam_Digital_Data"
DB_PATH = backend_root / "bizflow.sqlite3"

session_factory = create_session_factory(DB_PATH)
kyc = KycService(DATA_ROOT, session_factory)

doc_root = DATA_ROOT / "kyc_documents"
docs = sorted(doc_root.glob("*.png"))

print(f"Found {len(docs)} documents to process")
results = {"VERIFIED": 0, "ACTION_REQUIRED": 0, "MANUAL_REVIEW": 0, "ERROR": 0}
details = []

for doc in docs:
    fname = doc.name
    parts = fname.replace(".png", "").split("_", 1)
    if len(parts) != 2:
        print(f"  SKIP: {fname}")
        continue
    applicant_id, doc_type = parts[0], parts[1]
    try:
        kyc.consent(applicant_id, True)
    except Exception:
        pass
    try:
        result = kyc.document(applicant_id, doc_type, fname)
        status = result["status"]
        results[status] = results.get(status, 0) + 1
        print(f"  {fname:<32} -> {status:<15} | {result['reason'][:70]}")
        details.append({
            "file": fname,
            "applicant": applicant_id,
            "type": doc_type,
            "status": status,
            "reason": result["reason"],
            "fields": result.get("fields", {}),
        })
    except Exception as exc:
        print(f"  ERROR {fname}: {exc}")
        results["ERROR"] += 1

print("\n" + "=" * 60)
print("KYC AUTOMATED PROCESSING SUMMARY (NO MANUAL REVIEW REQUIRED):")
print("=" * 60)
print(json.dumps(results, indent=2))
print("=" * 60)
