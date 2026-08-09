"""Authoritative monetary calculations for the Finance module.

Every quotation, invoice and payment total in the system is produced here.
The module is deliberately pure (no database, no HTTP, no settings) so the
rules can be unit-tested in isolation and so there is exactly one place where
the calculation order is defined.

Calculation rule
----------------
::

    line_total   = round(quantity x unit_price)
    subtotal     = sum(line_totals)
    discount     = percentage of subtotal, or a fixed amount (capped at subtotal)
    taxable_base = subtotal - discount
    tax          = round(taxable_base x tax_rate%)
    grand_total  = taxable_base + tax

Tax is charged on the **discounted** amount, which is the common convention
and keeps ``grand_total`` consistent with what the customer actually pays.

All money is :class:`decimal.Decimal` quantized to 2 decimal places using
ROUND_HALF_UP. Floating point is never used for money — ``float`` cannot
represent values like ``0.1`` exactly and the error compounds across line
items.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable

# Discount strategies. Kept as plain strings to match the repository's
# convention of storing enum *values* in String columns.
DISCOUNT_PERCENTAGE = "percentage"
DISCOUNT_FIXED = "fixed"
DISCOUNT_TYPES = (DISCOUNT_PERCENTAGE, DISCOUNT_FIXED)

MONEY_PLACES = Decimal("0.01")
QUANTITY_PLACES = Decimal("0.001")

# Upper bounds chosen to stay well inside the NUMERIC(14, 2) columns used by
# the finance tables, so a valid document can never overflow on write.
MAX_QUANTITY = Decimal("1000000")
MAX_UNIT_PRICE = Decimal("100000000")
MAX_TOTAL = Decimal("999999999999")


class CalculationError(ValueError):
    """Raised when inputs cannot produce a valid monetary result."""


def to_decimal(value: Any, *, field_name: str = "value") -> Decimal:
    """Coerce user input to Decimal without ever going through float.

    ``float`` inputs are routed through ``str`` first: ``Decimal(0.1)`` yields
    ``0.1000000000000000055511151231257827...`` whereas ``Decimal("0.1")``
    is exact.
    """
    if isinstance(value, Decimal):
        candidate = value
    elif isinstance(value, bool):
        # bool is a subclass of int; accepting it silently would hide bugs.
        raise CalculationError(f"{field_name} must be a number.")
    elif isinstance(value, (int, float, str)):
        try:
            candidate = Decimal(str(value).strip())
        except (InvalidOperation, ArithmeticError):
            raise CalculationError(f"{field_name} must be a valid number.") from None
    else:
        raise CalculationError(f"{field_name} must be a number.")

    if not candidate.is_finite():
        raise CalculationError(f"{field_name} must be a finite number.")
    return candidate


def money(value: Any, *, field_name: str = "amount") -> Decimal:
    """Quantize a value to 2 decimal places (ROUND_HALF_UP)."""
    return to_decimal(value, field_name=field_name).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def quantity(value: Any, *, field_name: str = "quantity") -> Decimal:
    """Quantize a quantity to 3 decimal places, allowing fractional units."""
    return to_decimal(value, field_name=field_name).quantize(QUANTITY_PLACES, rounding=ROUND_HALF_UP)


def validate_quantity(value: Any) -> Decimal:
    result = quantity(value)
    if result <= 0:
        raise CalculationError("Quantity must be greater than zero.")
    if result > MAX_QUANTITY:
        raise CalculationError(f"Quantity must not exceed {MAX_QUANTITY:,.0f}.")
    return result


def validate_unit_price(value: Any) -> Decimal:
    result = money(value, field_name="unit_price")
    if result < 0:
        raise CalculationError("Unit price cannot be negative.")
    if result > MAX_UNIT_PRICE:
        raise CalculationError(f"Unit price must not exceed {MAX_UNIT_PRICE:,.2f}.")
    return result


def validate_tax_rate(value: Any) -> Decimal:
    """Tax rate as a percentage, e.g. ``Decimal('17.5')`` for 17.5%."""
    result = to_decimal(value, field_name="tax_rate").quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    if result < 0:
        raise CalculationError("Tax rate cannot be negative.")
    if result > 100:
        raise CalculationError("Tax rate cannot exceed 100%.")
    return result


def compute_line_total(qty: Any, unit_price: Any) -> Decimal:
    """Total for a single line, rounded once at the end."""
    return money(validate_quantity(qty) * validate_unit_price(unit_price), field_name="line_total")


@dataclass(frozen=True)
class LineTotal:
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


@dataclass(frozen=True)
class DocumentTotals:
    """The complete, authoritative set of monetary values for a document."""

    lines: list[LineTotal] = field(default_factory=list)
    subtotal: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    grand_total: Decimal = Decimal("0.00")

    def as_dict(self) -> dict[str, Decimal]:
        return {
            "subtotal": self.subtotal,
            "discount_amount": self.discount_amount,
            "tax_amount": self.tax_amount,
            "grand_total": self.grand_total,
        }


def compute_discount(subtotal: Decimal, discount_type: str | None, discount_value: Any) -> Decimal:
    """Resolve a discount to a concrete amount, capped at the subtotal.

    Capping matters: an uncapped fixed discount larger than the subtotal would
    produce a negative taxable base and therefore a negative tax.
    """
    if discount_value in (None, ""):
        return Decimal("0.00")

    value = to_decimal(discount_value, field_name="discount_value")
    if value < 0:
        raise CalculationError("Discount cannot be negative.")
    if value == 0:
        return Decimal("0.00")

    resolved_type = (discount_type or DISCOUNT_PERCENTAGE).strip().lower()
    if resolved_type not in DISCOUNT_TYPES:
        raise CalculationError(f"Discount type must be one of: {', '.join(DISCOUNT_TYPES)}.")

    if resolved_type == DISCOUNT_PERCENTAGE:
        if value > 100:
            raise CalculationError("Percentage discount cannot exceed 100%.")
        amount = money(subtotal * value / Decimal("100"), field_name="discount_amount")
    else:
        amount = money(value, field_name="discount_amount")
        if amount > subtotal:
            raise CalculationError("Fixed discount cannot exceed the subtotal.")

    return min(amount, subtotal)


def compute_totals(
    items: Iterable[Any],
    *,
    discount_type: str | None = DISCOUNT_PERCENTAGE,
    discount_value: Any = 0,
    tax_rate: Any = 0,
) -> DocumentTotals:
    """Compute every monetary value for a document from its line items.

    ``items`` may be dicts or objects exposing ``quantity`` and ``unit_price``,
    which lets the same function serve both inbound request payloads and
    already-persisted ORM rows.
    """
    lines: list[LineTotal] = []

    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            raw_qty, raw_price = item.get("quantity"), item.get("unit_price")
        else:
            raw_qty, raw_price = getattr(item, "quantity", None), getattr(item, "unit_price", None)

        try:
            qty = validate_quantity(raw_qty)
            price = validate_unit_price(raw_price)
        except CalculationError as exc:
            raise CalculationError(f"Item {index}: {exc}") from None

        lines.append(LineTotal(quantity=qty, unit_price=price, line_total=money(qty * price)))

    if not lines:
        raise CalculationError("A document must contain at least one line item.")

    subtotal = money(sum((line.line_total for line in lines), Decimal("0")), field_name="subtotal")
    if subtotal > MAX_TOTAL:
        raise CalculationError("Document subtotal exceeds the maximum supported amount.")

    discount_amount = compute_discount(subtotal, discount_type, discount_value)
    taxable_base = subtotal - discount_amount
    tax_amount = money(taxable_base * validate_tax_rate(tax_rate) / Decimal("100"), field_name="tax_amount")
    grand_total = money(taxable_base + tax_amount, field_name="grand_total")

    return DocumentTotals(
        lines=lines,
        subtotal=subtotal,
        discount_amount=discount_amount,
        tax_amount=tax_amount,
        grand_total=grand_total,
    )


def format_money(value: Any, symbol: str = "") -> str:
    """Render an amount for display/PDF output with thousands separators."""
    return f"{symbol}{money(value):,.2f}"
