from pathlib import Path

import pytest

from app.services.catalogue.loader import load_catalogue


def test_catalogue_contains_all_products(catalogue):
    assert len(catalogue) == 25
    assert set(catalogue) == {f"P{index:02d}" for index in range(1, 26)}


def test_catalogue_dependencies_are_parsed(catalogue):
    assert catalogue["P09"].requires_one_of == frozenset({"P01", "P02", "P03", "P05", "P06"})
    assert catalogue["P10"].requires_one_of == frozenset({"P01", "P02", "P03", "P05", "P06"})
    assert catalogue["P21"].requires_one_of == frozenset({"P01", "P02", "P03", "P05", "P06"})


def test_catalogue_price_ranges_are_valid(catalogue):
    assert all(
        product.price_min_inr_per_month <= product.price_max_inr_per_month
        for product in catalogue.values()
    )


def test_all_catalogue_dependencies_reference_known_products(catalogue):
    product_ids = set(catalogue)

    assert all(
        product.requires_one_of <= product_ids
        for product in catalogue.values()
    )


def test_loader_rejects_missing_columns():
    path = Path(__file__).parent / "_invalid_missing_columns.csv"
    try:
        path.write_text("product_id,product_name\nP01,Example\n", encoding="utf-8")

        with pytest.raises(ValueError, match="missing columns"):
            load_catalogue(path)
    finally:
        path.unlink(missing_ok=True)


def test_loader_rejects_unknown_dependency():
    source = (
        Path(__file__).resolve().parents[2]
        / "YTL_TrackA_Udyam_Digital_Data"
        / "product_catalogue.csv"
    )
    content = source.read_text(encoding="utf-8")
    content = content.replace("P01|P02|P03|P05|P06", "P999", 1)
    path = Path(__file__).parent / "_invalid_dependency.csv"
    try:
        path.write_text(content, encoding="utf-8")

        with pytest.raises(ValueError, match="unknown dependencies"):
            load_catalogue(path)
    finally:
        path.unlink(missing_ok=True)
