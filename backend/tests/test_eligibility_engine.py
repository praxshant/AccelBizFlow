from app.schemas.eligibility import BusinessProfile, RecommendationRequest
from app.services.eligibility.engine import EligibilityEngine


def request(**overrides):
    values = {
        "business_type": "clinic",
        "segment": "prof",
        "city_tier": 2,
        "employees": 12,
        "sites": 1,
        "gstin_active": True,
    }
    values.update(overrides)
    profile = BusinessProfile(**values)
    return RecommendationRequest(profile=profile)


def decisions_by_id(engine, recommendation_request):
    decisions = engine.evaluate(recommendation_request)
    return {decision.product.product_id: decision for decision in decisions}


def test_professional_office_gets_expected_products(catalogue):
    decisions = decisions_by_id(EligibilityEngine(catalogue), request())

    assert decisions["P02"].eligible
    assert decisions["P16"].eligible
    assert decisions["P20"].eligible
    assert not decisions["P10"].eligible
    assert "Business segment is not supported." in decisions["P10"].reasons


def test_multi_site_business_with_ten_employees_can_use_sdwan(catalogue):
    decisions = decisions_by_id(
        EligibilityEngine(catalogue),
        request(
            business_type="restaurant chain",
            segment="multi",
            employees=10,
            sites=3,
        ),
    )

    assert decisions["P10"].eligible
    assert decisions["P10"].recommended_quantity == 3


def test_sdwan_rejected_when_employee_threshold_fails(catalogue):
    decisions = decisions_by_id(
        EligibilityEngine(catalogue),
        request(segment="multi", employees=5, sites=3),
    )

    assert not decisions["P10"].eligible
    assert "Requires at least 10 employees." in decisions["P10"].reasons


def test_gstin_required_products_are_rejected_without_active_gstin(catalogue):
    decisions = decisions_by_id(
        EligibilityEngine(catalogue),
        request(gstin_active=False),
    )

    assert not decisions["P03"].eligible
    assert "An active GSTIN is required." in decisions["P03"].reasons
    assert not decisions["P10"].eligible


def test_tier_one_only_product_is_rejected_for_tier_two(catalogue):
    decisions = decisions_by_id(
        EligibilityEngine(catalogue),
        request(segment="mfg", employees=25, city_tier=2),
    )

    assert not decisions["P03"].eligible
    assert "Product is not available in this city tier." in decisions["P03"].reasons


def test_dependent_product_requires_an_eligible_connectivity_companion(catalogue):
    engine = EligibilityEngine(catalogue)
    profile = request(segment="prof").profile
    decisions = engine.validate_bundle(
        ["P09"],
        RecommendationRequest(profile=profile),
    )
    decision = decisions[0]

    assert not decision.eligible
    assert "Requires one companion product in the same bundle" in decision.reasons[0]


def test_dependent_product_is_valid_only_when_companion_is_in_same_bundle(catalogue):
    engine = EligibilityEngine(catalogue)
    profile = request(segment="prof").profile
    decisions = engine.validate_bundle(
        ["P02", "P09"],
        RecommendationRequest(profile=profile),
    )

    assert all(decision.eligible for decision in decisions)


def test_unknown_selected_product_is_rejected(catalogue):
    engine = EligibilityEngine(catalogue)

    try:
        engine.evaluate(
            RecommendationRequest(
                profile=request().profile,
                selected_product_ids=["P999"],
            )
        )
    except ValueError as error:
        assert "Unknown selected product IDs" in str(error)
    else:
        raise AssertionError("Unknown selected product should be rejected.")


def test_generated_bundles_have_valid_dependencies(catalogue):
    engine = EligibilityEngine(catalogue)
    response = engine.recommend(request())

    for bundle in response.bundles:
        decisions = engine.validate_bundle(bundle.product_ids, request())
        assert all(decision.eligible for decision in decisions)


def test_every_catalogue_unit_has_a_safe_quantity(catalogue):
    engine = EligibilityEngine(catalogue)
    decisions = engine.evaluate(request(segment="multi", employees=25, sites=3))

    for decision in decisions:
        if decision.eligible:
            assert decision.recommended_quantity >= 1


def test_all_recommendations_are_eligible_or_explain_failure(catalogue):
    decisions = EligibilityEngine(catalogue).evaluate(request())

    assert len(decisions) == 25
    assert all(decision.eligible or decision.reasons for decision in decisions)
