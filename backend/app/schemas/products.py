from typing import FrozenSet

from pydantic import BaseModel, ConfigDict, Field, field_validator


SUPPORTED_UNITS = frozenset(
    {
        "per site",
        "per line",
        "per IP",
        "per channel",
        "per number",
        "per pack",
        "per user",
        "per account",
        "per counter",
        "per device",
        "per camera",
        "per vehicle",
    }
)


class Product(BaseModel):
    model_config = ConfigDict(frozen=True)

    product_id: str = Field(min_length=1)
    category: str
    product_name: str = Field(min_length=1)
    description: str
    unit: str
    price_min_inr_per_month: int = Field(ge=0)
    price_max_inr_per_month: int = Field(ge=0)
    one_time_setup_inr: int = Field(ge=0)
    min_contract_months: int = Field(gt=0)
    available_city_tiers: FrozenSet[int]
    min_employees: int = Field(ge=1)
    min_sites: int = Field(ge=1)
    requires_gstin: bool
    requires_one_of: FrozenSet[str] = Field(default_factory=frozenset)
    typical_install_days: int = Field(gt=0)
    target_segments: FrozenSet[str]

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, value: str) -> str:
        normalised = " ".join(value.strip().split())
        if normalised not in SUPPORTED_UNITS:
            raise ValueError(f"Unsupported product unit: {value}")
        return normalised

    @field_validator("available_city_tiers")
    @classmethod
    def validate_city_tiers(cls, value: FrozenSet[int]) -> FrozenSet[int]:
        if not value or not value.issubset({1, 2}):
            raise ValueError("City tiers must be a non-empty subset of {1, 2}.")
        return value

    @field_validator("target_segments")
    @classmethod
    def validate_target_segments(cls, value: FrozenSet[str]) -> FrozenSet[str]:
        supported = {"micro", "prof", "multi", "mfg"}
        if not value or not value.issubset(supported):
            raise ValueError("Product contains an unsupported target segment.")
        return value
