import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.database import QuoteItemRecord, QuoteRecord
from app.schemas.eligibility import (
    BusinessProfile,
    QuoteCreateRequest,
    QuoteItemsPatchRequest,
    QuoteResponse,
)
from app.services.eligibility.engine import EligibilityEngine, recommended_quantity
from app.schemas.eligibility import RecommendationRequest
from app.services.pricing import RateCard, calculate_quote


class QuoteService:
    def __init__(self, session: Session, catalogue: dict, eligibility: EligibilityEngine):
        self.session = session
        self.catalogue = catalogue
        self.eligibility = eligibility
        self.rate_card = RateCard()

    def _validate_items(self, profile: BusinessProfile, items):
        request = RecommendationRequest(
            profile=profile, selected_product_ids=[item.product_id for item in items]
        )
        decisions = self.eligibility.evaluate(request)
        eligible_ids = {decision.product.product_id for decision in decisions if decision.eligible}
        selected_ids = {item.product_id for item in items}
        if not selected_ids <= eligible_ids:
            raise ValueError("Quote contains products ineligible for this business profile.")
        for item in items:
            product = self.catalogue[item.product_id]
            if product.unit in ("per site",):
                min_qty = profile.sites
            elif product.unit in ("per user", "per device"):
                min_qty = profile.employees
            else:
                min_qty = 1
            if item.quantity < min_qty:
                raise ValueError(
                    f"{item.product_id} requires a minimum quantity of {min_qty} for this profile."
                )
        bundle = self.eligibility.validate_bundle(list(selected_ids), request)
        if not all(decision.eligible for decision in bundle):
            raise ValueError("Quote contains an invalid product dependency combination.")
        return calculate_quote(self.catalogue, items, self.rate_card)

    def create(self, request: QuoteCreateRequest) -> QuoteResponse:
        if request.idempotency_key:
            existing = self.session.query(QuoteRecord).filter_by(
                idempotency_key=request.idempotency_key
            ).first()
            if existing:
                return self._response(existing)
        lines, monthly, setup = self._validate_items(request.profile, request.items)
        record = QuoteRecord(
            quote_id=str(uuid.uuid4()),
            status="GENERATED",
            pricing_version=self.rate_card.version,
            profile_json=request.profile.model_dump_json(),
            items_json=json.dumps([line.__dict__ | {
                "unit_price": str(line.unit_price),
                "monthly_total": str(line.monthly_total),
                "setup_total": str(line.setup_total),
            } for line in lines]),
            monthly_total_minor=int(monthly * 100),
            setup_total_minor=int(setup * 100),
            idempotency_key=request.idempotency_key,
        )
        self.session.add(record)
        self.session.flush()
        for line in lines:
            prod = self.catalogue.get(line.product_id)
            unit_val = getattr(prod, "unit", "per item") if prod else "per item"
            self.session.add(QuoteItemRecord(
                quote_id=record.quote_id,
                product_id=line.product_id,
                quantity=line.quantity,
                unit=unit_val,
                monthly_price_minor=int(line.monthly_total * 100),
                setup_price_minor=int(line.setup_total * 100),
            ))
        self.session.commit()
        return self._response(record)

    def get(self, quote_id: str) -> QuoteResponse:
        record = self.session.get(QuoteRecord, quote_id)
        if record is None:
            raise KeyError(quote_id)
        return self._response(record)

    def update_items(self, quote_id: str, request: QuoteItemsPatchRequest) -> QuoteResponse:
        record = self.session.get(QuoteRecord, quote_id)
        if record is None:
            raise KeyError(quote_id)
        if record.status == "ACCEPTED":
            raise ValueError("Accepted quotes cannot be modified.")
        profile = BusinessProfile.model_validate_json(record.profile_json)
        lines, monthly, setup = self._validate_items(profile, request.items)
        record.items_json = json.dumps([line.__dict__ | {
            "unit_price": str(line.unit_price),
            "monthly_total": str(line.monthly_total),
            "setup_total": str(line.setup_total),
        } for line in lines])
        record.monthly_total_minor = int(monthly * 100)
        record.setup_total_minor = int(setup * 100)
        self.session.commit()
        return self._response(record)

    def accept(self, quote_id: str) -> QuoteResponse:
        record = self.session.get(QuoteRecord, quote_id)
        if record is None:
            raise KeyError(quote_id)
        if record.status == "ACCEPTED":
            return self._response(record)
        record.status = "ACCEPTED"
        record.accepted_at = datetime.now(timezone.utc)
        self.session.commit()
        return self._response(record)

    def _response(self, record: QuoteRecord) -> QuoteResponse:
        items = json.loads(record.items_json)
        return QuoteResponse(
            quote_id=record.quote_id,
            status=record.status,
            pricing_version=record.pricing_version,
            profile=BusinessProfile.model_validate_json(record.profile_json),
            items=[
                {
                    "product_id": item["product_id"],
                    "product_name": item["product_name"],
                    "quantity": item["quantity"],
                    "unit_price_inr": item["unit_price"],
                    "monthly_total_inr": item["monthly_total"],
                    "setup_total_inr": item["setup_total"],
                    "min_contract_months": item["min_contract_months"],
                }
                for item in items
            ],
            monthly_total_inr=f"{Decimal(record.monthly_total_minor) / 100:.2f}",
            setup_total_inr=f"{Decimal(record.setup_total_minor) / 100:.2f}",
            accepted_at=(
                record.accepted_at.replace(tzinfo=timezone.utc).isoformat()
                if record.accepted_at
                else None
            ),
        )
