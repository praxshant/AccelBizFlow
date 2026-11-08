import csv
import difflib
import json
import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.database import ConsentRecord, KycAuditRecord, KycCaseRecord, KycDocumentRecord


class KycService:
    ALLOWED_DOCUMENTS = {
        "gst_certificate",
        "udyam_certificate",
        "address_proof",
        "signatory_id",
    }
    KYC_REFERENCE_DATE = datetime(2026, 7, 15, tzinfo=timezone.utc)
    ADDRESS_PROOF_MAX_DAYS = 90
    _easyocr_reader = None

    def __init__(self, data_root: Path, session_factory):
        self.data_root = data_root.resolve()
        self.document_root = (self.data_root / "kyc_documents").resolve()
        self.session_factory = session_factory
        self.gstin = self._load_registry("mock_gstin_registry.csv")
        self.udyam = self._load_registry("mock_udyam_registry.csv")

    def _load_registry(self, filename):
        path = self.data_root / filename
        with path.open(newline="", encoding="utf-8-sig") as file:
            rows = list(csv.DictReader(file))
        return {str(row[next(iter(row))]).strip(): row for row in rows}

    def _case(self, session, applicant_id):
        case = session.get(KycCaseRecord, applicant_id)
        if case is None:
            case = KycCaseRecord(
                applicant_id=applicant_id, status="ACTION_REQUIRED", reasons_json="[]"
            )
            session.add(case)
            session.flush()
        return case

    def _audit(self, session, applicant_id, event, details):
        session.add(
            KycAuditRecord(
                applicant_id=applicant_id,
                event=event,
                detail_json=json.dumps(details, separators=(",", ":")),
            )
        )

    def create_case(self, applicant_id: str):
        """Explicitly create a KYC case for an applicant (idempotent)."""
        with self.session_factory.begin() as session:
            case = self._case(session, applicant_id)
            self._audit(session, applicant_id, "case_created", {"applicant_id": applicant_id})
        return self.status(applicant_id)

    def consent(self, applicant_id: str, granted: bool):
        with self.session_factory.begin() as session:
            session.add(ConsentRecord(applicant_id=applicant_id, granted=granted))
            self._case(session, applicant_id)
            self._audit(session, applicant_id, "consent_changed", {"granted": granted})
        return {
            "applicant_id": applicant_id,
            "granted": granted,
            "consented_at": datetime.now(timezone.utc).isoformat() if granted else None,
        }

    def _require_consent(self, session, applicant_id):
        consent = (
            session.query(ConsentRecord)
            .filter_by(applicant_id=applicant_id)
            .order_by(ConsentRecord.consent_id.desc())
            .first()
        )
        if consent is None or not consent.granted:
            raise PermissionError("Explicit consent is required before document processing.")

    def feasibility(self, locations):
        now = datetime.now(timezone.utc)
        sites = []
        for location in locations:
            normalized = location.strip().lower()
            if not normalized:
                status, reason, scheduling = "SURVEY_REQUIRED", "Location is missing.", False
            elif "remote" in normalized or "unserviceable" in normalized:
                status, reason, scheduling = "NOT_FEASIBLE", "Simulation has no supported service coverage.", False
            elif "survey" in normalized or "new area" in normalized or "review" in normalized:
                status, reason, scheduling = "SURVEY_REQUIRED", "Simulation requires a site survey before confirming coverage.", False
            elif "alternative" in normalized or "4g only" in normalized or "wireless only" in normalized:
                status, reason, scheduling = "ALTERNATIVE_AVAILABLE", "Wireless or 4G alternative available; fibre not confirmed.", True
            else:
                status, reason, scheduling = "AVAILABLE", "Simulation indicates supported coverage.", True
            sites.append(
                {
                    "location": location,
                    "status": status,
                    "reason": reason,
                    "scheduling_available": scheduling,
                }
            )
        return {
            "sites": sites,
            "checked_at": now.isoformat(),
            "valid_until_hours": 24,
        }

    def _get_ocr_reader(self):
        if self._easyocr_reader is None:
            try:
                import easyocr
                self._easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            except Exception:
                self._easyocr_reader = False
        return self._easyocr_reader if self._easyocr_reader is not False else None

    def _extract_ocr(self, path):
        reader = self._get_ocr_reader()
        if not reader:
            return "", 0.0
        try:
            results = reader.readtext(str(path), detail=1)
            if not results:
                return "", 0.0
            texts = [item[1] for item in results]
            confidences = [item[2] for item in results]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            return " ".join(texts), float(avg_confidence)
        except Exception:
            return "", 0.0

    def _extract_fields(self, text, document_type):
        fields = {}
        text_clean = text.replace("\n", " ")

        gstin_match = re.search(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z])\b", text_clean)
        if gstin_match:
            fields["gstin"] = gstin_match.group(1).upper()
        else:
            tokens = [t.strip(",.:;~|/") for t in text_clean.split() if len(t.strip(",.:;~|/")) >= 10]
            for token in tokens:
                matches = difflib.get_close_matches(token.upper(), self.gstin.keys(), n=1, cutoff=0.75)
                if matches:
                    fields["gstin"] = matches[0]
                    break

        udyam_match = re.search(r"\b(UDYAM-[A-Z]{2}-\d{2}-\d{7})\b", text_clean, re.IGNORECASE)
        if udyam_match:
            fields["udyam_number"] = udyam_match.group(1).upper()
        else:
            for udyam_num, u_rec in self.udyam.items():
                ent_name = u_rec.get("enterprise_name", "")
                if ent_name and len(ent_name) > 6 and ent_name.lower() in text_clean.lower():
                    fields["udyam_number"] = udyam_num
                    break

        date_iso = re.findall(r"\b(20\d{2}[/\-]\d{2}[/\-]\d{2})\b", text_clean)
        date_dmy = re.findall(r"\b(\d{2}[/\-]\d{2}[/\-](?:20)?\d{2,4})\b", text_clean)
        if date_iso:
            fields["dates_found"] = date_iso[0]
        elif date_dmy:
            fields["dates_found"] = date_dmy[0]

        pin = re.search(r"\b([1-9]\d{5})\b", text_clean)
        if pin:
            fields["pincode"] = pin.group(1)

        return fields

    def _parse_date(self, date_str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None

    def _kyc_decision(self, document_type, fields, confidence, text_found):
        if not text_found and confidence == 0.0:
            return "MANUAL_REVIEW", "OCR could not read document; manual review required."

        if document_type == "gst_certificate":
            if "gstin" in fields:
                reg = self.registry("GSTIN", fields["gstin"])
                if reg["status"] == "VALID":
                    return "VERIFIED", f"GSTIN {fields['gstin'][:6]}*** is active and verified in registry."
                elif reg["status"] == "INVALID":
                    return "ACTION_REQUIRED", f"GSTIN {fields['gstin'][:6]}*** registration is cancelled/suspended."
                else:
                    return "MANUAL_REVIEW", "GSTIN not found in synthetic registry; review required."
            if confidence >= 0.5:
                return "MANUAL_REVIEW", "GST certificate processed; GSTIN requires confirmation."
            return "ACTION_REQUIRED", "GSTIN number could not be extracted; please re-upload."

        elif document_type == "udyam_certificate":
            if "udyam_number" in fields:
                reg = self.registry("UDYAM", fields["udyam_number"])
                if reg["status"] == "VALID":
                    return "VERIFIED", f"Udyam registration {fields['udyam_number'][:10]}*** verified in registry."
                else:
                    return "MANUAL_REVIEW", "Udyam registration not found in registry."
            if confidence >= 0.5:
                return "MANUAL_REVIEW", "Udyam certificate processed; registration number requires confirmation."
            return "ACTION_REQUIRED", "Udyam registration number could not be extracted; please re-upload."

        elif document_type == "address_proof":
            if "dates_found" in fields:
                doc_date = self._parse_date(fields["dates_found"])
                if doc_date:
                    age_days = (self.KYC_REFERENCE_DATE - doc_date).days
                    if age_days > self.ADDRESS_PROOF_MAX_DAYS:
                        return "ACTION_REQUIRED", f"Address proof is {age_days} days old (maximum {self.ADDRESS_PROOF_MAX_DAYS} days allowed)."
                    return "VERIFIED", f"Address proof verified and current ({age_days} days old)."
            if confidence >= 0.4:
                return "VERIFIED", "Address proof document verified within acceptable parameters."
            return "MANUAL_REVIEW", "Address proof requires manual verification."

        elif document_type == "signatory_id":
            if confidence >= 0.4:
                return "VERIFIED", "Signatory identity document quality is acceptable."
            elif confidence >= 0.2:
                return "MANUAL_REVIEW", "Signatory identity confidence is marginal; review required."
            else:
                return "ACTION_REQUIRED", "Signatory ID image quality is too low; please re-upload."

        return "MANUAL_REVIEW", "Document processed; manual review recommended."

    def document(self, applicant_id, document_type, file_name):
        if document_type not in self.ALLOWED_DOCUMENTS:
            raise ValueError("Unsupported document type.")
        if Path(file_name).name != file_name or Path(file_name).suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            raise ValueError("Only synthetic PNG or JPEG documents are accepted.")
        path = (self.document_root / file_name).resolve()
        if self.document_root not in path.parents or path.stat().st_size > 10 * 1024 * 1024:
            raise ValueError("Document is outside the permitted storage policy.")
        with self.session_factory.begin() as session:
            self._require_consent(session, applicant_id)

            # Image decoding validation with OpenCV
            try:
                import cv2
                image = cv2.imread(str(path))
                if image is None:
                    raise ValueError("Image could not be decoded.")
            except (ValueError, OSError) as exc:
                raise ValueError(str(exc)) from exc

            # Real OCR text extraction
            raw_text, confidence = self._extract_ocr(path)
            fields = self._extract_fields(raw_text, document_type) if raw_text else {}
            status, reason = self._kyc_decision(document_type, fields, confidence, bool(raw_text))

            case = self._case(session, applicant_id)
            case.status = status
            reasons = json.loads(case.reasons_json)
            reasons.append(reason)
            case.reasons_json = json.dumps(reasons)
            session.add(KycDocumentRecord(
                applicant_id=applicant_id,
                document_type=document_type,
                file_name=file_name,
                status=status,
                confidence=round(confidence, 3),
                reason=reason,
                extracted_fields_json=json.dumps(fields),
            ))
            self._audit(session, applicant_id, "document_processed", {
                "document_type": document_type,
                "status": status,
                "confidence": round(confidence, 3),
                "fields_extracted": list(fields.keys()),
            })

        return {
            "applicant_id": applicant_id,
            "document_type": document_type,
            "status": status,
            "fields": fields,
            "field_confidence": {"document": round(confidence, 3)},
            "reason": reason,
        }

    def document_upload(self, applicant_id, document_type, filename, content):
        if not filename or Path(filename).suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            raise ValueError("Only PNG or JPEG uploads are accepted.")
        if len(content) > 10 * 1024 * 1024:
            raise ValueError("Uploaded document exceeds the 10 MB limit.")
        self.document_root.mkdir(parents=True, exist_ok=True)
        stored_name = f"upload_{uuid.uuid4().hex}{Path(filename).suffix.lower()}"
        path = self.document_root / stored_name
        path.write_bytes(content)
        try:
            return self.document(applicant_id, document_type, stored_name)
        finally:
            path.unlink(missing_ok=True)

    def registry(self, registry, identifier):
        normalized = registry.upper()
        if normalized not in {"GSTIN", "UDYAM"}:
            raise ValueError("Registry must be GSTIN or UDYAM.")
        if len(identifier) > 40 or not identifier.isalnum() and "-" not in identifier:
            raise ValueError("Invalid registry identifier format.")
        masked = identifier[:3] + "***" + identifier[-2:] if len(identifier) > 5 else "***"
        records = self.gstin if normalized == "GSTIN" else self.udyam
        if identifier not in records:
            status = "MANUAL_REVIEW"
            reason = "No synthetic match; review is required."
        else:
            record = records[identifier]
            rec_status = record.get("status", record.get("Status", "")).strip()
            if normalized == "GSTIN" and rec_status.lower() in {"cancelled", "suspended"}:
                status = "INVALID"
                reason = f"GSTIN registration is {rec_status.lower()}."
            else:
                status = "VALID"
                reason = "Synthetic registry record matched."
        return {
            "registry": normalized,
            "identifier_masked": masked,
            "status": status,
            "reason": reason,
        }

    def status(self, applicant_id):
        with self.session_factory() as session:
            case = session.get(KycCaseRecord, applicant_id)
            if case is None:
                raise KeyError(applicant_id)
            events = (
                session.query(KycAuditRecord)
                .filter_by(applicant_id=applicant_id)
                .order_by(KycAuditRecord.event_id)
                .all()
            )
            return {
                "applicant_id": applicant_id,
                "status": case.status,
                "reasons": json.loads(case.reasons_json),
                "audit": [
                    {"event": event.event, **json.loads(event.detail_json), "at": event.created_at.isoformat()}
                    for event in events
                ],
            }

    def review(self, applicant_id, status, reason, reviewer_id=None, reviewer_role=None, reviewer_identity=None):
        allowed = {"VERIFIED", "ACTION_REQUIRED", "MANUAL_REVIEW", "REJECTED"}
        reviewer = reviewer_id or reviewer_identity
        if status not in allowed or not reviewer:
            raise PermissionError("An authenticated reviewer identity is required.")
        with self.session_factory.begin() as session:
            case = session.get(KycCaseRecord, applicant_id)
            if case is None:
                raise KeyError(applicant_id)
            allowed_transitions = {
                "ACTION_REQUIRED": {"VERIFIED", "MANUAL_REVIEW", "REJECTED", "ACTION_REQUIRED"},
                "MANUAL_REVIEW": {"VERIFIED", "ACTION_REQUIRED", "REJECTED", "MANUAL_REVIEW"},
                "VERIFIED": {"VERIFIED"},
                "REJECTED": {"REJECTED"},
            }
            if status not in allowed_transitions.get(case.status, set()):
                raise ValueError(f"Invalid KYC transition {case.status} -> {status}.")
            previous = case.status
            case.status = status
            reasons = json.loads(case.reasons_json)
            reasons.append(reason)
            case.reasons_json = json.dumps(reasons)
            self._audit(session, applicant_id, "status_changed", {
                "previous": previous, "status": status, "reviewer": reviewer,
            })
        return self.status(applicant_id)
