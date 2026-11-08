import csv
from pathlib import Path

from app.schemas.products import Product, SUPPORTED_UNITS


REQUIRED_COLUMNS = {
    "product_id",
    "category",
    "product_name",
    "description",
    "unit",
    "price_min_inr_per_month",
    "price_max_inr_per_month",
    "one_time_setup_inr",
    "min_contract_months",
    "available_city_tiers",
    "min_employees",
    "min_sites",
    "requires_gstin",
    "requires_one_of",
    "typical_install_days",
    "target_segments",
}


def _parse_int_set(value: str) -> frozenset[int]:
    return frozenset(int(item) for item in value.split(";") if item)


def _parse_str_set(value: str, separator: str = "|") -> frozenset[str]:
    return frozenset(item.strip() for item in value.split(separator) if item.strip())


def load_catalogue(path: Path) -> dict[str, Product]:
    if not path.is_file():
        raise FileNotFoundError(f"Product catalogue not found: {path}")

    products: dict[str, Product] = {}
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        columns = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - columns
        if missing_columns:
            raise ValueError(f"Catalogue is missing columns: {sorted(missing_columns)}")
        for row in reader:
            if not row["product_id"].strip():
                raise ValueError("Catalogue contains a product with an empty ID")
            if not row["product_name"].strip():
                raise ValueError(f"Product {row['product_id']} has an empty name")
            if row["unit"].strip() not in SUPPORTED_UNITS:
                raise ValueError(f"Product {row['product_id']} has an unsupported unit")
            if row["requires_gstin"].strip().upper() not in {"Y", "N"}:
                raise ValueError(
                    f"Product {row['product_id']} has an invalid requires_gstin value"
                )
            product = Product(
                product_id=row["product_id"],
                category=row["category"],
                product_name=row["product_name"],
                description=row["description"],
                unit=row["unit"],
                price_min_inr_per_month=int(row["price_min_inr_per_month"]),
                price_max_inr_per_month=int(row["price_max_inr_per_month"]),
                one_time_setup_inr=int(row["one_time_setup_inr"]),
                min_contract_months=int(row["min_contract_months"]),
                available_city_tiers=_parse_int_set(row["available_city_tiers"]),
                min_employees=int(row["min_employees"]),
                min_sites=int(row["min_sites"]),
                requires_gstin=row["requires_gstin"].strip().upper() == "Y",
                requires_one_of=_parse_str_set(row["requires_one_of"]),
                typical_install_days=int(row["typical_install_days"]),
                target_segments=_parse_str_set(row["target_segments"], separator=";"),
            )
            if product.product_id in products:
                raise ValueError(f"Duplicate product ID: {product.product_id}")
            if product.price_min_inr_per_month > product.price_max_inr_per_month:
                raise ValueError(f"Invalid price range: {product.product_id}")
            products[product.product_id] = product

    if len(products) != 25:
        raise ValueError(f"Expected 25 catalogue products, found {len(products)}")
    product_ids = set(products)
    for product in products.values():
        missing_dependencies = product.requires_one_of - product_ids
        if missing_dependencies:
            raise ValueError(
                f"Product {product.product_id} references unknown dependencies: "
                f"{sorted(missing_dependencies)}"
            )
    return products
