from app.schemas.eligibility import (
    BundleOption,
    ProductDecision,
    RecommendationRequest,
    RecommendationResponse,
)
from app.schemas.products import Product


SEGMENT_ALIASES = {
    "prof": "prof",
    "professional": "prof",
    "professional offices": "prof",
    "multi": "multi",
    "multi-site": "multi",
    "small multi-site businesses": "multi",
    "micro": "micro",
    "micro retail": "micro",
    "micro retail & services": "micro",
    "mfg": "mfg",
    "manufacturer": "mfg",
    "small manufacturers": "mfg",
}


def _normalise_segment(segment: str) -> str:
    return SEGMENT_ALIASES[segment.strip().lower()]


def recommended_quantity(product: Product, sites: int, employees: int) -> int:
    quantities = {
        "per site": sites,
        "per user": employees,
        "per device": employees,
    }
    if product.unit in quantities:
        return quantities[product.unit]
    if product.unit in {
        "per line",
        "per IP",
        "per channel",
        "per number",
        "per pack",
        "per account",
        "per counter",
        "per camera",
        "per vehicle",
    }:
        return 1
    raise ValueError(f"Unsupported product unit: {product.unit}")


class EligibilityEngine:
    def __init__(self, catalogue: dict[str, Product]) -> None:
        self.catalogue = catalogue

    def _base_decision(self, product: Product, request: RecommendationRequest) -> ProductDecision:
        profile = request.profile
        segment = _normalise_segment(profile.segment)
        reasons: list[str] = []
        if segment not in product.target_segments:
            reasons.append("Business segment is not supported.")
        if profile.city_tier not in product.available_city_tiers:
            reasons.append("Product is not available in this city tier.")
        if profile.employees < product.min_employees:
            reasons.append(f"Requires at least {product.min_employees} employees.")
        if profile.sites < product.min_sites:
            reasons.append(f"Requires at least {product.min_sites} sites.")
        if product.requires_gstin and not profile.gstin_active:
            reasons.append("An active GSTIN is required.")
        return ProductDecision(
            product=product,
            eligible=not reasons,
            reasons=reasons,
            recommended_quantity=(
                recommended_quantity(product, profile.sites, profile.employees)
                if not reasons
                else None
            ),
        )

    def _validate_selected_products(
        self,
        request: RecommendationRequest,
        base_decisions: dict[str, ProductDecision],
    ) -> set[str]:
        selected_ids = set(request.selected_product_ids)
        unknown_ids = selected_ids - set(self.catalogue)
        if unknown_ids:
            raise ValueError(f"Unknown selected product IDs: {sorted(unknown_ids)}")
        ineligible_ids = {
            product_id
            for product_id in selected_ids
            if not base_decisions[product_id].eligible
        }
        if ineligible_ids:
            raise ValueError(f"Ineligible selected product IDs: {sorted(ineligible_ids)}")
        return selected_ids

    def validate_bundle(
        self,
        product_ids: list[str],
        request: RecommendationRequest,
        base_decisions: dict[str, ProductDecision] | None = None,
    ) -> list[ProductDecision]:
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("A bundle cannot contain duplicate product IDs.")
        decisions = base_decisions or {
            product_id: self._base_decision(product, request)
            for product_id, product in self.catalogue.items()
        }
        unknown_ids = set(product_ids) - set(self.catalogue)
        if unknown_ids:
            raise ValueError(f"Unknown bundle product IDs: {sorted(unknown_ids)}")
        bundle_ids = set(product_ids)
        result: list[ProductDecision] = []
        for product_id in product_ids:
            decision = decisions[product_id]
            reasons = list(decision.reasons)
            product = decision.product
            if decision.eligible and product.requires_one_of:
                if not product.requires_one_of.intersection(bundle_ids):
                    reasons.append(
                        "Requires one companion product in the same bundle: "
                        + ", ".join(sorted(product.requires_one_of))
                        + "."
                    )
            result.append(
                decision.model_copy(update={"eligible": not reasons, "reasons": reasons})
            )
        return result

    def evaluate(self, request: RecommendationRequest) -> list[ProductDecision]:
        base_decisions = {
            product_id: self._base_decision(product, request)
            for product_id, product in self.catalogue.items()
        }
        selected_ids = self._validate_selected_products(request, base_decisions)
        if selected_ids:
            selected_decisions = self.validate_bundle(
                list(selected_ids), request, base_decisions
            )
            invalid_selected = [
                decision.product.product_id
                for decision in selected_decisions
                if not decision.eligible
            ]
            if invalid_selected:
                raise ValueError(
                    f"Selected products form an invalid bundle: {sorted(invalid_selected)}"
                )
        return list(base_decisions.values())

    def _compose_bundles(
        self,
        request: RecommendationRequest,
        base_decisions: dict[str, ProductDecision],
    ) -> list[BundleOption]:
        eligible = [
            decision.product
            for decision in base_decisions.values()
            if decision.eligible
        ]
        standalone = [product for product in eligible if not product.requires_one_of]
        connectivity = [
            product
            for product in standalone
            if product.category == "Connectivity"
        ]
        if not connectivity:
            return [
                BundleOption(name=name, product_ids=[])
                for name in ("essential", "recommended", "advanced")
            ]

        primary = connectivity[0]
        essential_ids = [primary.product_id]

        # Recommended: primary + one per category from standalone, then companion products
        recommended_ids = list(essential_ids)
        for category in ("Cloud & Productivity", "Security", "Communication"):
            candidate = next(
                (
                    product
                    for product in standalone
                    if product.category == category
                    and product.product_id not in recommended_ids
                ),
                None,
            )
            if candidate:
                recommended_ids.append(candidate.product_id)

        # Include requires_one_of companion products whose dependency is in recommended_ids
        bundle_set = set(recommended_ids)
        for product in eligible:
            if product.requires_one_of and product.product_id not in bundle_set:
                if product.requires_one_of.intersection(bundle_set):
                    recommended_ids.append(product.product_id)
                    bundle_set.add(product.product_id)
                    if len(recommended_ids) >= 7:
                        break

        # Advanced: extend recommended up to 7 total
        advanced_ids = list(recommended_ids)
        advanced_set = set(advanced_ids)
        for product in standalone:
            if product.product_id not in advanced_set and len(advanced_ids) < 7:
                advanced_ids.append(product.product_id)
                advanced_set.add(product.product_id)

        for product in eligible:
            if product.requires_one_of and product.product_id not in advanced_set:
                if product.requires_one_of.intersection(advanced_set):
                    if len(advanced_ids) < 7:
                        advanced_ids.append(product.product_id)
                        advanced_set.add(product.product_id)

        bundles = [
            ("essential", essential_ids),
            ("recommended", recommended_ids),
            ("advanced", advanced_ids),
        ]
        result = []
        for name, product_ids in bundles:
            try:
                decisions = self.validate_bundle(product_ids, request, base_decisions)
                valid_ids = [d.product.product_id for d in decisions if d.eligible]
                result.append(BundleOption(name=name, product_ids=valid_ids))
            except Exception:
                result.append(BundleOption(name=name, product_ids=product_ids[:1]))
        return result

    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        decisions = self.evaluate(request)
        decisions_by_id = {decision.product.product_id: decision for decision in decisions}
        eligible = [decision for decision in decisions if decision.eligible]
        ineligible = [decision for decision in decisions if not decision.eligible]
        return RecommendationResponse(
            profile=request.profile,
            eligible_products=eligible,
            ineligible_products=ineligible,
            bundles=self._compose_bundles(request, decisions_by_id),
        )
