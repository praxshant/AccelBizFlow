from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/products")
def list_products(request: Request):
    catalogue = request.app.state.catalogue
    return {
        "total": len(catalogue),
        "products": [
            {
                "product_id": p.product_id,
                "product_name": p.product_name,
                "category": p.category,
                "unit": p.unit,
                "price_min_inr_per_month": p.price_min_inr_per_month,
                "price_max_inr_per_month": p.price_max_inr_per_month,
                "one_time_setup_inr": p.one_time_setup_inr,
                "min_contract_months": p.min_contract_months,
                "target_segments": list(p.target_segments),
                "available_city_tiers": list(p.available_city_tiers),
                "requires_gstin": p.requires_gstin,
                "min_employees": p.min_employees,
                "min_sites": p.min_sites,
                "requires_one_of": list(p.requires_one_of) if p.requires_one_of else [],
            }
            for p in catalogue.values()
        ],
    }


@router.get("/products/{product_id}")
def get_product(product_id: str, request: Request):
    catalogue = request.app.state.catalogue
    if product_id not in catalogue:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found.")
    p = catalogue[product_id]
    return {
        "product_id": p.product_id,
        "product_name": p.product_name,
        "category": p.category,
        "unit": p.unit,
        "price_min_inr_per_month": p.price_min_inr_per_month,
        "price_max_inr_per_month": p.price_max_inr_per_month,
        "one_time_setup_inr": p.one_time_setup_inr,
        "min_contract_months": p.min_contract_months,
        "target_segments": list(p.target_segments),
        "available_city_tiers": list(p.available_city_tiers),
        "requires_gstin": p.requires_gstin,
        "min_employees": p.min_employees,
        "min_sites": p.min_sites,
        "requires_one_of": list(p.requires_one_of) if p.requires_one_of else [],
        "standalone": not p.requires_one_of,
    }
