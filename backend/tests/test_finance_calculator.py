"""Unit tests for the money engine.

These run without a database or HTTP layer, so a failure here points at the
calculation rules themselves rather than at plumbing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.finance_calculator import (
    CalculationError,
    compute_discount,
    compute_line_total,
    compute_totals,
    money,
)


def D(value: str) -> Decimal:
    return Decimal(value)


class TestLineTotals:
    def test_simple_line_total(self):
        assert compute_line_total(3, "19.99") == D("59.97")

    def test_fractional_quantity(self):
        assert compute_line_total("2.5", "40.00") == D("100.00")

    def test_zero_unit_price_is_allowed(self):
        """Free line items are legitimate (bundled or promotional goods)."""
        assert compute_line_total(5, 0) == D("0.00")

    def test_float_input_does_not_leak_binary_error(self):
        # 0.1 + 0.2 != 0.3 in binary floating point; 3 x 0.1 must be exactly 0.30.
        assert compute_line_total(3, 0.1) == D("0.30")

    def test_rounds_half_up(self):
        # 1 x 0.005 -> 0.01, not 0.00 (banker's rounding would give 0.00).
        assert compute_line_total(1, "0.005") == D("0.01")

    @pytest.mark.parametrize("bad_quantity", [0, -1, "-0.001"])
    def test_rejects_non_positive_quantity(self, bad_quantity):
        with pytest.raises(CalculationError, match="greater than zero"):
            compute_line_total(bad_quantity, 10)

    def test_rejects_negative_price(self):
        with pytest.raises(CalculationError, match="cannot be negative"):
            compute_line_total(1, -5)

    @pytest.mark.parametrize("bad", ["abc", None, True, [1]])
    def test_rejects_non_numeric(self, bad):
        with pytest.raises(CalculationError):
            compute_line_total(1, bad)

    def test_rejects_nan_and_infinity(self):
        with pytest.raises(CalculationError, match="finite"):
            compute_line_total(1, float("inf"))


class TestDiscount:
    def test_percentage_discount(self):
        assert compute_discount(D("200.00"), "percentage", 10) == D("20.00")

    def test_fixed_discount(self):
        assert compute_discount(D("200.00"), "fixed", "35.50") == D("35.50")

    def test_zero_discount(self):
        assert compute_discount(D("200.00"), "percentage", 0) == D("0.00")

    def test_none_discount(self):
        assert compute_discount(D("200.00"), "percentage", None) == D("0.00")

    def test_full_percentage_discount_allowed(self):
        assert compute_discount(D("200.00"), "percentage", 100) == D("200.00")

    def test_percentage_over_100_rejected(self):
        with pytest.raises(CalculationError, match="cannot exceed 100"):
            compute_discount(D("200.00"), "percentage", 101)

    def test_fixed_discount_above_subtotal_rejected(self):
        """Otherwise the taxable base — and therefore the tax — goes negative."""
        with pytest.raises(CalculationError, match="cannot exceed the subtotal"):
            compute_discount(D("200.00"), "fixed", "200.01")

    def test_negative_discount_rejected(self):
        with pytest.raises(CalculationError, match="cannot be negative"):
            compute_discount(D("200.00"), "percentage", -5)

    def test_unknown_discount_type_rejected(self):
        with pytest.raises(CalculationError, match="Discount type"):
            compute_discount(D("200.00"), "buy_one_get_one", 10)


class TestDocumentTotals:
    def test_full_calculation_chain(self):
        # 3 x 19.99 = 59.97, 2 x 0.10 = 0.20  -> subtotal 60.17
        # 10% discount = 6.02 (6.017 rounded half-up)
        # taxable base = 54.15, 20% tax = 10.83
        # grand total = 64.98
        totals = compute_totals(
            [
                {"description": "a", "quantity": 3, "unit_price": "19.99"},
                {"description": "b", "quantity": 2, "unit_price": "0.10"},
            ],
            discount_type="percentage",
            discount_value=10,
            tax_rate=20,
        )
        assert totals.subtotal == D("60.17")
        assert totals.discount_amount == D("6.02")
        assert totals.tax_amount == D("10.83")
        assert totals.grand_total == D("64.98")

    def test_tax_is_charged_on_the_discounted_amount(self):
        totals = compute_totals(
            [{"description": "a", "quantity": 1, "unit_price": "100.00"}],
            discount_type="fixed",
            discount_value="50.00",
            tax_rate=10,
        )
        assert totals.discount_amount == D("50.00")
        assert totals.tax_amount == D("5.00")  # 10% of 50, not of 100
        assert totals.grand_total == D("55.00")

    def test_grand_total_identity_holds(self):
        totals = compute_totals(
            [{"description": "a", "quantity": 7, "unit_price": "13.37"}],
            discount_value="3.5",
            tax_rate="17.5",
        )
        assert totals.grand_total == totals.subtotal - totals.discount_amount + totals.tax_amount

    def test_zero_tax_and_zero_discount(self):
        totals = compute_totals([{"description": "a", "quantity": 4, "unit_price": "25.00"}])
        assert totals.subtotal == totals.grand_total == D("100.00")

    def test_hundred_percent_discount_yields_zero_total(self):
        totals = compute_totals(
            [{"description": "a", "quantity": 1, "unit_price": "500.00"}],
            discount_value=100,
            tax_rate=20,
        )
        assert totals.grand_total == D("0.00")
        assert totals.tax_amount == D("0.00")

    def test_large_values_stay_exact(self):
        totals = compute_totals(
            [{"description": "a", "quantity": 1000, "unit_price": "99999.99"}]
        )
        assert totals.subtotal == D("99999990.00")

    def test_many_small_items_do_not_drift(self):
        """100 x 0.07 must be exactly 7.00 — a float sum drifts here."""
        totals = compute_totals(
            [{"description": f"item {i}", "quantity": 1, "unit_price": "0.07"} for i in range(100)]
        )
        assert totals.subtotal == D("7.00")

    def test_empty_document_rejected(self):
        with pytest.raises(CalculationError, match="at least one line item"):
            compute_totals([])

    def test_invalid_item_reports_its_position(self):
        with pytest.raises(CalculationError, match="Item 2"):
            compute_totals(
                [
                    {"description": "ok", "quantity": 1, "unit_price": 10},
                    {"description": "bad", "quantity": -1, "unit_price": 10},
                ]
            )

    @pytest.mark.parametrize("bad_rate", [-1, 101, "abc"])
    def test_invalid_tax_rate_rejected(self, bad_rate):
        with pytest.raises(CalculationError):
            compute_totals(
                [{"description": "a", "quantity": 1, "unit_price": 10}], tax_rate=bad_rate
            )

    def test_accepts_objects_as_well_as_dicts(self):
        class Row:
            quantity = Decimal("2")
            unit_price = Decimal("15.00")

        totals = compute_totals([Row()])
        assert totals.subtotal == D("30.00")


class TestMoneyHelper:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("1.005", "1.01"), ("1.004", "1.00"), (0.1, "0.10"), (2, "2.00"), ("-3.456", "-3.46")],
    )
    def test_quantization(self, raw, expected):
        assert money(raw) == Decimal(expected)
