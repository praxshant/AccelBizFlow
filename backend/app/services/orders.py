import json
import uuid
from datetime import datetime, timedelta, timezone

from app.database import (
    InstallationRecord,
    KycCaseRecord,
    OrderEventRecord,
    OrderRecord,
    PaymentRecord,
    QuoteRecord,
)


TRANSITIONS = {
    "DRAFT": {"QUOTE_ACCEPTED", "CANCELLED"},
    "QUOTE_ACCEPTED": {"KYC_PENDING", "CANCELLED"},
    "KYC_PENDING": {"KYC_VERIFIED", "KYC_ACTION_REQUIRED", "KYC_MANUAL_REVIEW", "KYC_REJECTED", "CANCELLED"},
    "KYC_ACTION_REQUIRED": {"KYC_PENDING", "CANCELLED"},
    "KYC_MANUAL_REVIEW": {"KYC_PENDING", "KYC_VERIFIED", "KYC_REJECTED", "CANCELLED"},
    "KYC_VERIFIED": {"FEASIBILITY_CLEARED", "FEASIBILITY_SURVEY_REQUIRED", "FEASIBILITY_UNAVAILABLE", "CANCELLED"},
    "FEASIBILITY_SURVEY_REQUIRED": {"FEASIBILITY_CLEARED", "FEASIBILITY_UNAVAILABLE", "CANCELLED"},
    "FEASIBILITY_CLEARED": {"PAYMENT_PENDING", "CANCELLED"},
    "PAYMENT_PENDING": {"PAYMENT_CONFIRMED", "PAYMENT_FAILED", "CANCELLED"},
    "PAYMENT_FAILED": {"PAYMENT_PENDING", "CANCELLED"},
    "PAYMENT_CONFIRMED": {"INSTALLATION_SCHEDULED", "CANCELLED"},
    "INSTALLATION_SCHEDULED": {"INSTALLATION_IN_PROGRESS", "INSTALLATION_BLOCKED", "CANCELLED"},
    "INSTALLATION_BLOCKED": {"INSTALLATION_SCHEDULED", "CANCELLED"},
    "INSTALLATION_IN_PROGRESS": {"SERVICE_INSTALLED", "INSTALLATION_BLOCKED"},
    "SERVICE_INSTALLED": {"ACTIVATED"},
    "ACTIVATED": set(),
    "KYC_REJECTED": set(),
    "FEASIBILITY_UNAVAILABLE": set(),
    "CANCELLED": set(),
}


class OrderService:
    def __init__(self, session_factory, catalogue, feasibility):
        self.session_factory = session_factory
        self.catalogue = catalogue
        self.quote_service = catalogue
        self.feasibility = feasibility

    def _events(self, session, order_id):
        return session.query(OrderEventRecord).filter_by(order_id=order_id).order_by(OrderEventRecord.event_id).all()

    def _response(self, session, order):
        return {
            "order_id": order.order_id,
            "quote_id": order.quote_id,
            "status": order.status,
            "payment_status": order.payment_status,
            "installation_status": order.installation_status,
            "snapshot": json.loads(order.snapshot_json),
            "events": [
                {
                    "actor": event.actor,
                    "previous_state": event.previous_state,
                    "new_state": event.new_state,
                    "reason": event.reason,
                    "at": event.created_at.isoformat(),
                }
                for event in self._events(session, order.order_id)
            ],
        }

    def create(self, quote_id, applicant_id, location):
        with self.session_factory.begin() as session:
            quote = session.get(QuoteRecord, quote_id)
            if quote is None:
                raise KeyError("Quote not found.")
            if quote.status != "ACCEPTED":
                raise ValueError("Only accepted quotes can create orders.")
            existing = session.query(OrderRecord).filter_by(quote_id=quote_id).first()
            if existing:
                return self._response(session, existing)
            snapshot = {
                "quote_id": quote.quote_id,
                "profile": json.loads(quote.profile_json),
                "items": json.loads(quote.items_json),
                "monthly_total_minor": quote.monthly_total_minor,
                "setup_total_minor": quote.setup_total_minor,
                "applicant_id": applicant_id,
                "location": location,
            }
            order = OrderRecord(
                order_id=str(uuid.uuid4()),
                quote_id=quote_id,
                status="QUOTE_ACCEPTED",
                applicant_id=applicant_id,
                snapshot_json=json.dumps(snapshot),
            )
            session.add(order)
            session.flush()
            session.add(OrderEventRecord(
                order_id=order.order_id, actor="system", previous_state="DRAFT",
                new_state="QUOTE_ACCEPTED", reason="Accepted quote converted to order.",
            ))
            return self._response(session, order)

    def get(self, order_id):
        with self.session_factory() as session:
            order = session.get(OrderRecord, order_id)
            if order is None:
                raise KeyError(order_id)
            return self._response(session, order)

    def transition(self, order_id, new_state, reason, actor):
        with self.session_factory.begin() as session:
            order = session.get(OrderRecord, order_id)
            if order is None:
                raise KeyError(order_id)
            if new_state not in TRANSITIONS.get(order.status, set()):
                raise ValueError(f"Invalid order transition {order.status} -> {new_state}.")

            # KYC verification gate: if a KYC case exists, it must be VERIFIED
            if new_state == "KYC_VERIFIED":
                applicant_id = order.applicant_id or json.loads(order.snapshot_json).get("applicant_id")
                if applicant_id:
                    kyc_case = session.get(KycCaseRecord, applicant_id)
                    if kyc_case is not None and kyc_case.status != "VERIFIED":
                        raise ValueError(
                            "Order cannot advance to KYC_VERIFIED: KYC case is not VERIFIED."
                        )

            # Feasibility gate: if transitioning to FEASIBILITY_CLEARED, ensure site is feasible
            if new_state == "FEASIBILITY_CLEARED":
                snapshot = json.loads(order.snapshot_json)
                location = snapshot.get("location")
                if location and self.feasibility:
                    res = self.feasibility([location])["sites"][0]
                    if res.get("status") == "NOT_FEASIBLE":
                        raise ValueError("Order cannot advance to FEASIBILITY_CLEARED: Location is NOT_FEASIBLE.")

            previous = order.status
            order.status = new_state
            order.updated_at = datetime.now(timezone.utc)
            session.add(OrderEventRecord(
                order_id=order_id, actor=actor, previous_state=previous,
                new_state=new_state, reason=reason,
            ))
            return self._response(session, order)

    def payment(self, order_id, outcome, reason):
        with self.session_factory.begin() as session:
            order = session.get(OrderRecord, order_id)
            if order is None:
                raise KeyError(order_id)
            if order.status != "PAYMENT_PENDING":
                raise ValueError("Payment is only available while payment is pending.")
            status = "CONFIRMED" if outcome == "SUCCESS" else "FAILED"
            order.payment_status = status
            new_state = "PAYMENT_CONFIRMED" if status == "CONFIRMED" else "PAYMENT_FAILED"
            session.add(PaymentRecord(
                payment_id=str(uuid.uuid4()), order_id=order_id, status=status,
                reference_id=str(uuid.uuid4()) if status == "CONFIRMED" else None,
                reason=reason or ("Simulated payment success." if status == "CONFIRMED" else "Simulated payment failure."),
            ))
            previous = order.status
            order.status = new_state
            session.add(OrderEventRecord(
                order_id=order_id, actor="payment-simulator", previous_state=previous,
                new_state=new_state, reason=reason or "Deterministic payment simulation.",
            ))
            return self._response(session, order)

    def schedule(self, order_id, location):
        with self.session_factory.begin() as session:
            order = session.get(OrderRecord, order_id)
            if order is None:
                raise KeyError(order_id)
            if order.status != "PAYMENT_CONFIRMED":
                raise ValueError("Installation requires confirmed payment.")
            result = self.feasibility([location])["sites"][0]
            if result["status"] == "NOT_FEASIBLE":
                raise ValueError("A non-feasible site cannot receive an installation slot.")

            snapshot = json.loads(order.snapshot_json)
            items = snapshot.get("items", [])

            # Lookup product typical_install_days from catalogue
            install_days_list = []
            if isinstance(self.catalogue, dict):
                for item in items:
                    pid = item.get("product_id")
                    prod = self.catalogue.get(pid)
                    if prod and hasattr(prod, "typical_install_days") and prod.typical_install_days is not None:
                        install_days_list.append(int(prod.typical_install_days))
            elif isinstance(self.catalogue, list):
                for item in items:
                    pid = item.get("product_id")
                    for prod in self.catalogue:
                        if getattr(prod, "product_id", None) == pid and hasattr(prod, "typical_install_days") and prod.typical_install_days is not None:
                            install_days_list.append(int(prod.typical_install_days))

            product_install_days = max(install_days_list) if install_days_list else 5

            feasibility_adjustment = {
                "AVAILABLE": 0,
                "ALTERNATIVE_AVAILABLE": 3,
                "SURVEY_REQUIRED": 7,
            }.get(result["status"], 0)

            if len(items) > 3:
                feasibility_adjustment += 2

            total_days = product_install_days + feasibility_adjustment
            status = "SCHEDULED"
            eta = datetime.now(timezone.utc) + timedelta(days=total_days)
            session.add(InstallationRecord(
                installation_id=str(uuid.uuid4()), order_id=order_id, location=location,
                status=status, eta=eta, reason=f"Derived from product typical install days ({product_install_days}d) + feasibility SLA ({result['status']}). {result['reason']}",
            ))
            previous = order.status
            order.status = "INSTALLATION_SCHEDULED"
            order.installation_status = status
            session.add(OrderEventRecord(
                order_id=order_id, actor="scheduler", previous_state=previous,
                new_state=order.status, reason=f"ETA: {total_days} days (product={product_install_days}d, feasibility={result['status']}).",
            ))
            return self._response(session, order)
