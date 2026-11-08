import csv
from pathlib import Path

from app.database import AssignmentRecord, ConversationRecord, HumanAssistanceRecord, KycCaseRecord, LeadRecord, OrderRecord, QuoteRecord


class AnalyticsService:
    def __init__(self, data_root: Path, session_factory):
        self.data_root = data_root
        self.session_factory = session_factory

    def _leads(self):
        with (self.data_root / "smb_leads.csv").open(newline="", encoding="utf-8-sig") as file:
            return list(csv.DictReader(file))

    def funnel(self):
        historical = {
            "leads": 5000,
            "contacted": 3406,
            "needs_assessed": 1974,
            "quote_accepted": 861,
            "kyc_complete": 588,
            "activated": 368,
            "conversion_rate": 0.0736,
        }
        with self.session_factory() as session:
            quotes_total = session.query(QuoteRecord).count()
            quotes_accepted = session.query(QuoteRecord).filter_by(status="ACCEPTED").count()
            kyc_verified = session.query(KycCaseRecord).filter_by(status="VERIFIED").count()
            orders_activated = session.query(OrderRecord).filter_by(status="ACTIVATED").count()
            orders_total = session.query(OrderRecord).count()
        return {
            "source": "combined",
            "historical_baseline": historical,
            "live_prototype": {
                "quotes_total": quotes_total,
                "quotes_accepted": quotes_accepted,
                "kyc_verified": kyc_verified,
                "orders_total": orders_total,
                "orders_activated": orders_activated,
            },
        }

    def segments(self):
        rows = self._leads()
        result = {}
        for row in rows:
            segment = row["segment"]
            item = result.setdefault(segment, {"leads": 0, "activated": 0})
            item["leads"] += 1
            if row["stage_reached"] == "Activated":
                item["activated"] += 1
        for item in result.values():
            item["conversion_rate"] = round(item["activated"] / item["leads"], 4) if item["leads"] else 0
        return {"source": "historical_case_data", "segments": result}

    def score(self, lead_id):
        row = next((item for item in self._leads() if item["lead_id"] == lead_id), None)
        if row is None:
            raise KeyError(lead_id)
        score = 0
        reasons = []
        employees = int(row["employee_count"] or 0)
        sites = int(row["num_sites"] or 0)
        if employees >= 10:
            score += 25
            reasons.append("10 or more employees")
        if sites >= 2:
            score += 25
            reasons.append("multi-site need")
        if row["has_gstin"] == "Y":
            score += 20
            reasons.append("GSTIN available")
        if row["segment"] in {"Professional offices", "Small manufacturers"}:
            score += 15
            reasons.append("priority segment")
        if row["monthly_telecom_spend_inr"]:
            score += 15
            reasons.append("telecom spend provided")
        return {"lead_id": lead_id, "score": min(score, 100), "reasons": reasons}

    def queue(self, page=1, page_size=20, case_type=None, priority=None):
        items = []
        with self.session_factory() as session:
            assignments = {
                a.case_id: a.owner
                for a in session.query(AssignmentRecord).all()
            }
            for quote in session.query(QuoteRecord).filter(QuoteRecord.status != "ACCEPTED").all():
                owner = assignments.get(quote.quote_id, "UNASSIGNED")
                items.append({
                    "case_type": "quote",
                    "case_id": quote.quote_id,
                    "status": quote.status,
                    "priority": "normal",
                    "owner": owner,
                })
            for case in session.query(KycCaseRecord).filter(KycCaseRecord.status.in_(["MANUAL_REVIEW", "ACTION_REQUIRED"])).all():
                owner = assignments.get(case.applicant_id, "UNASSIGNED")
                items.append({
                    "case_type": "kyc",
                    "case_id": case.applicant_id,
                    "status": case.status,
                    "priority": "high",
                    "owner": owner,
                })
            for order in session.query(OrderRecord).filter(OrderRecord.status.in_(["PAYMENT_FAILED", "INSTALLATION_BLOCKED"])).all():
                owner = assignments.get(order.order_id, "UNASSIGNED")
                items.append({
                    "case_type": "order",
                    "case_id": order.order_id,
                    "status": order.status,
                    "priority": "high",
                    "owner": owner,
                })
            for case in session.query(HumanAssistanceRecord).filter_by(status="OPEN").all():
                owner = assignments.get(case.case_id, "UNASSIGNED")
                items.append({
                    "case_type": "assistance",
                    "case_id": case.case_id,
                    "status": case.status,
                    "priority": "high",
                    "owner": owner,
                    "stage": case.stage,
                    "reason": case.reason,
                })

        if case_type:
            items = [i for i in items if i["case_type"] == case_type]
        if priority:
            items = [i for i in items if i["priority"] == priority]

        start = (page - 1) * page_size
        return {
            "total": len(items),
            "page": page,
            "page_size": page_size,
            "items": items[start:start + page_size],
        }

    def sales_queue(self, page=1, page_size=20):
        with self.session_factory() as session:
            leads = session.query(LeadRecord).filter(LeadRecord.archived_at.is_(None)).order_by(
                LeadRecord.created_at.desc()
            ).all()
            session_ids = {
                row.lead_id
                for row in session.query(ConversationRecord.lead_id).filter(
                    ConversationRecord.lead_id.isnot(None)
                ).all()
            }
            items = [
                {
                    "case_type": "lead",
                    "case_id": lead.lead_id,
                    "business_name": lead.business_name,
                    "contact_name": lead.contact_name,
                    "city": lead.city,
                    "segment": lead.segment,
                    "status": "DISCOVERY" if lead.lead_id in session_ids else "NEW",
                    "priority": "normal",
                    "owner": "UNASSIGNED",
                }
                for lead in leads
            ]
        start = (page - 1) * page_size
        return {"total": len(items), "page": page, "page_size": page_size, "items": items[start:start + page_size]}

    def assign(self, case_type, case_id, owner):
        with self.session_factory.begin() as session:
            record = AssignmentRecord(case_type=case_type, case_id=case_id, owner=owner)
            session.add(record)
            session.flush()
            return {
                "assignment_id": record.assignment_id,
                "case_type": record.case_type,
                "case_id": record.case_id,
                "owner": record.owner,
                "status": record.status,
            }
