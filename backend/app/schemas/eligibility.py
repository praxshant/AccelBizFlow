from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.products import Product


class BusinessProfile(BaseModel):
    business_type: str = Field(min_length=1)
    segment: str = Field(min_length=1)
    city_tier: Literal[1, 2]
    employees: int = Field(ge=1)
    sites: int = Field(ge=1)
    gstin_active: bool = False

    @field_validator("segment")
    @classmethod
    def validate_segment(cls, value: str) -> str:
        normalised = " ".join(value.strip().lower().split())
        aliases = {
            "prof",
            "professional",
            "professional offices",
            "multi",
            "multi-site",
            "small multi-site businesses",
            "micro",
            "micro retail",
            "micro retail & services",
            "mfg",
            "manufacturer",
            "small manufacturers",
        }
        if normalised not in aliases:
            raise ValueError(f"Unsupported business segment: {value}")
        return normalised


class ProductDecision(BaseModel):
    product: Product
    eligible: bool
    reasons: list[str] = Field(default_factory=list)
    recommended_quantity: int | None = None


class RecommendationRequest(BaseModel):
    profile: BusinessProfile
    selected_product_ids: list[str] = Field(default_factory=list)


class BundleOption(BaseModel):
    name: Literal["essential", "recommended", "advanced"]
    product_ids: list[str]


class RecommendationResponse(BaseModel):
    profile: BusinessProfile
    eligible_products: list[ProductDecision]
    ineligible_products: list[ProductDecision]
    bundles: list[BundleOption]


class QuoteItemInput(BaseModel):
    product_id: str = Field(min_length=1)
    quantity: int = Field(ge=1)


class QuoteCreateRequest(BaseModel):
    profile: BusinessProfile
    items: list[QuoteItemInput] = Field(min_length=1)
    idempotency_key: str | None = None


class QuoteItemResponse(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price_inr: str
    monthly_total_inr: str
    setup_total_inr: str
    min_contract_months: int


class QuoteResponse(BaseModel):
    quote_id: str
    status: Literal["DRAFT", "GENERATED", "ACCEPTED"]
    pricing_version: str
    profile: BusinessProfile
    items: list[QuoteItemResponse]
    monthly_total_inr: str
    setup_total_inr: str
    accepted_at: str | None = None


class QuoteItemsPatchRequest(BaseModel):
    items: list[QuoteItemInput] = Field(min_length=1)
