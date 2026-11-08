"""Test bundle generation includes requires_one_of products."""
import pytest
from app.main import app
from app.services.eligibility.engine import EligibilityEngine
from app.schemas.eligibility import RecommendationRequest, BusinessProfile


def test_bundles_not_empty_for_eligible_profile():
    catalogue = app.state.catalogue
    engine = EligibilityEngine(catalogue)
    profile = BusinessProfile(
        business_type="office",
        segment="prof",
        city_tier=1,
        employees=15,
        sites=2,
        gstin_active=True,
    )
    request = RecommendationRequest(profile=profile)
    response = engine.recommend(request)
    bundles = {b.name: b for b in response.bundles}
    assert "essential" in bundles
    assert len(bundles["essential"].product_ids) >= 1, "Essential bundle must have at least 1 product"
    assert len(bundles["recommended"].product_ids) >= 1, "Recommended bundle must have at least 1 product"


def test_requires_one_of_products_included_in_advanced():
    catalogue = app.state.catalogue
    engine = EligibilityEngine(catalogue)
    profile = BusinessProfile(
        business_type="office",
        segment="multi",
        city_tier=1,
        employees=20,
        sites=3,
        gstin_active=True,
    )
    request = RecommendationRequest(profile=profile)
    response = engine.recommend(request)
    advanced = next((b for b in response.bundles if b.name == "advanced"), None)
    assert advanced is not None
    for pid in advanced.product_ids:
        p = catalogue[pid]
        if p.requires_one_of:
            assert p.requires_one_of.intersection(set(advanced.product_ids)), \
                f"{pid} in bundle but its dependency is not"


def test_bundle_validation_passes():
    catalogue = app.state.catalogue
    engine = EligibilityEngine(catalogue)
    profile = BusinessProfile(
        business_type="shop",
        segment="micro",
        city_tier=2,
        employees=3,
        sites=1,
        gstin_active=False,
    )
    request = RecommendationRequest(profile=profile)
    response = engine.recommend(request)
    for bundle in response.bundles:
        if bundle.product_ids:
            decisions = engine.validate_bundle(bundle.product_ids, request)
            assert all(d.eligible for d in decisions), \
                f"Bundle {bundle.name} contains ineligible products"
