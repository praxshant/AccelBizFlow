from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from app.schemas.eligibility import QuoteItemInput
from app.schemas.products import Product


MONEY_PLACES = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class RateCard:
    version: str = "CATALOGUE-MIDPOINT-v1"

    def resolve_price(self, product: Product) -> Decimal:
        return money(
            (Decimal(product.price_min_inr_per_month) + Decimal(product.price_max_inr_per_month))
            / Decimal(2)
        )


@dataclass(frozen=True)
class QuoteLine:
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    monthly_total: Decimal
    setup_total: Decimal
    min_contract_months: int


_PHYSICAL_UNITS = {
    "per site",
    "per camera",
    "per vehicle",
    "per device",
    "per counter",
    "per channel",
    "per number",
    "per line",
}


def calculate_line_item(product: Product, quantity: int, rate_card: RateCard) -> QuoteLine:
    if quantity < 1:
        raise ValueError("Quantity must be at least one.")
    unit_price = rate_card.resolve_price(product)
    # Physical units multiply setup by quantity; user/account/pack/IP are flat one-time setup
    if product.unit in _PHYSICAL_UNITS:
        setup_total = money(Decimal(product.one_time_setup_inr) * quantity)
    else:
        setup_total = money(Decimal(product.one_time_setup_inr))
    return QuoteLine(
        product_id=product.product_id,
        product_name=product.product_name,
        quantity=quantity,
        unit_price=unit_price,
        monthly_total=money(unit_price * quantity),
        setup_total=setup_total,
        min_contract_months=product.min_contract_months,
    )


def calculate_quote(
    products: dict[str, Product],
    items: list[QuoteItemInput],
    rate_card: RateCard,
) -> tuple[list[QuoteLine], Decimal, Decimal]:
    if len({item.product_id for item in items}) != len(items):
        raise ValueError("A quote cannot contain duplicate product IDs.")
    lines = [
        calculate_line_item(products[item.product_id], item.quantity, rate_card)
        for item in items
    ]
    return (
        lines,
        money(sum((line.monthly_total for line in lines), Decimal("0"))),
        money(sum((line.setup_total for line in lines), Decimal("0"))),
    )
