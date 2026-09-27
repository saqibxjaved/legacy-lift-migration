"""
Tests for OrderProcessor, Order, OrderItem, and OrderStatus.

Business rules verified:
  - TAX_RATE = 0.08
  - BULK_DISCOUNT_THRESHOLD = 500.00
  - BULK_DISCOUNT_RATE = 0.10
  - Bulk discount applied when subtotal > 500.00 (strictly greater than)
  - No discount when subtotal <= 500.00
  - process_batch never raises; invalid items are skipped silently
  - Negative price raises ValueError
  - Zero quantity raises ValueError
  - Empty items list raises ValueError
  - None order raises ValueError
"""

import pytest
from decimal import Decimal
from demo.expected_output.order_processor import (
    Order,
    OrderItem,
    OrderProcessor,
    OrderStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_item(name: str = "Widget", price: float = 10.00, quantity: int = 1) -> OrderItem:
    """Convenience factory for OrderItem instances."""
    return OrderItem(name=name, price=Decimal(str(price)), quantity=quantity)


def make_processor() -> OrderProcessor:
    return OrderProcessor()


# ---------------------------------------------------------------------------
# TestConstants — pin financial constants so refactors cannot silently break math
# ---------------------------------------------------------------------------

class TestConstants:
    def test_tax_rate_value(self):
        """TAX_RATE must be exactly 0.08."""
        processor = make_processor()
        assert processor.TAX_RATE == Decimal("0.08")

    def test_bulk_discount_threshold_value(self):
        """BULK_DISCOUNT_THRESHOLD must be exactly 500.00."""
        processor = make_processor()
        assert processor.BULK_DISCOUNT_THRESHOLD == Decimal("500.00")

    def test_bulk_discount_rate_value(self):
        """BULK_DISCOUNT_RATE must be exactly 0.10."""
        processor = make_processor()
        assert processor.BULK_DISCOUNT_RATE == Decimal("0.10")


# ---------------------------------------------------------------------------
# TestOrderStatus — enum members exist and are distinct
# ---------------------------------------------------------------------------

class TestOrderStatus:
    def test_pending_member_exists(self):
        assert OrderStatus.PENDING is not None

    def test_processed_member_exists(self):
        assert OrderStatus.PROCESSED is not None

    def test_cancelled_member_exists(self):
        assert OrderStatus.CANCELLED is not None

    def test_members_are_distinct(self):
        assert OrderStatus.PENDING != OrderStatus.PROCESSED
        assert OrderStatus.PROCESSED != OrderStatus.CANCELLED


# ---------------------------------------------------------------------------
# TestSubtotalCalculation — _calculate_subtotal
# ---------------------------------------------------------------------------

class TestSubtotalCalculation:
    def test_single_item_subtotal(self):
        """subtotal = price * quantity for one item."""
        processor = make_processor()
        items = [make_item(price=25.00, quantity=3)]
        result = processor._calculate_subtotal(items)
        assert result == Decimal("75.00")

    def test_multiple_items_subtotal(self):
        """subtotal is the sum across all items."""
        processor = make_processor()
        items = [
            make_item(name="A", price=10.00, quantity=2),   # 20.00
            make_item(name="B", price=15.00, quantity=4),   # 60.00
        ]
        result = processor._calculate_subtotal(items)
        assert result == Decimal("80.00")


# ---------------------------------------------------------------------------
# TestDiscountCalculation — _calculate_discount + boundary conditions
# ---------------------------------------------------------------------------

class TestDiscountCalculation:
    def test_no_discount_when_subtotal_below_threshold(self):
        """subtotal of 499.99 is below threshold -> discount = 0."""
        processor = make_processor()
        discount = processor._calculate_discount(Decimal("499.99"))
        assert discount == Decimal("0")

    def test_no_discount_when_subtotal_equals_threshold(self):
        """subtotal of exactly 500.00 is NOT strictly greater -> discount = 0."""
        processor = make_processor()
        discount = processor._calculate_discount(Decimal("500.00"))
        assert discount == Decimal("0")

    def test_bulk_discount_applied_when_subtotal_above_threshold(self):
        """subtotal of 600.00 > 500.00 -> discount = 600.00 * 0.10 = 60.00."""
        processor = make_processor()
        discount = processor._calculate_discount(Decimal("600.00"))
        assert discount == Decimal("60.00")

    def test_bulk_discount_boundary_just_above_threshold(self):
        """subtotal of 500.01 is strictly greater than 500 -> discount applied."""
        processor = make_processor()
        discount = processor._calculate_discount(Decimal("500.01"))
        assert discount == Decimal("50.001")


# ---------------------------------------------------------------------------
# TestProcessOrderHappyPath — successful end-to-end order processing
# ---------------------------------------------------------------------------

class TestProcessOrderHappyPath:
    def test_process_order_returns_processed_status(self):
        """A valid order ends with PROCESSED status."""
        processor = make_processor()
        order = Order(items=[make_item(price=10.00, quantity=1)])
        result = processor.process_order(order)
        assert result.status == OrderStatus.PROCESSED

    def test_process_order_no_discount_path(self):
        """
        Subtotal = 100.00 (<= 500) -> discount = 0, tax = 8.00, total = 108.00.
        """
        processor = make_processor()
        order = Order(items=[make_item(price=50.00, quantity=2)])
        result = processor.process_order(order)
        assert result.subtotal == Decimal("100.00")
        assert result.discount == Decimal("0")
        assert result.tax == Decimal("8.00")
        assert result.total == Decimal("108.00")

    def test_process_order_bulk_discount_path(self):
        """
        Subtotal = 600.00 (> 500) -> discount = 60.00, taxable = 540.00,
        tax = 43.20, total = 583.20.
        """
        processor = make_processor()
        order = Order(items=[make_item(price=200.00, quantity=3)])
        result = processor.process_order(order)
        assert result.subtotal == Decimal("600.00")
        assert result.discount == Decimal("60.00")
        # tax = (600.00 - 60.00) * 0.08 = 540.00 * 0.08 = 43.20
        assert result.tax == Decimal("43.20")
        assert result.total == Decimal("583.20")

    def test_process_order_tax_accuracy(self):
        """
        Verify tax is calculated on the post-discount subtotal, not the gross.
        """
        processor = make_processor()
        # subtotal = 1000.00, discount = 100.00, taxable = 900.00
        # tax = 900.00 * 0.08 = 72.00, total = 972.00
        order = Order(items=[make_item(price=100.00, quantity=10)])
        result = processor.process_order(order)
        assert result.tax == Decimal("72.00")
        assert result.total == Decimal("972.00")


# ---------------------------------------------------------------------------
# TestProcessOrderValidation — invalid inputs raise ValueError
# ---------------------------------------------------------------------------

class TestProcessOrderValidation:
    def test_none_order_raises_value_error(self):
        """Passing None as the order must raise ValueError."""
        processor = make_processor()
        with pytest.raises(ValueError):
            processor.process_order(None)

    def test_empty_items_raises_value_error(self):
        """An order with an empty items list must raise ValueError."""
        processor = make_processor()
        order = Order(items=[])
        with pytest.raises(ValueError):
            processor.process_order(order)

    def test_negative_price_raises_value_error(self):
        """An item with a negative price must cause ValueError."""
        processor = make_processor()
        order = Order(items=[make_item(price=-5.00, quantity=1)])
        with pytest.raises(ValueError):
            processor.process_order(order)

    def test_zero_quantity_raises_value_error(self):
        """An item with zero quantity must cause ValueError."""
        processor = make_processor()
        order = Order(items=[make_item(price=10.00, quantity=0)])
        with pytest.raises(ValueError):
            processor.process_order(order)


# ---------------------------------------------------------------------------
# TestProcessBatch — batch processing contract (ADR-004: never raises)
# ---------------------------------------------------------------------------

class TestProcessBatch:
    def test_process_batch_all_valid_returns_all_results(self):
        """All valid orders in a batch are processed and returned."""
        processor = make_processor()
        orders = [
            Order(items=[make_item(price=10.00, quantity=1)]),
            Order(items=[make_item(price=20.00, quantity=2)]),
        ]
        results = processor.process_batch(orders)
        assert len(results) == 2
        assert all(r.status == OrderStatus.PROCESSED for r in results)

    def test_process_batch_skips_invalid_never_raises(self):
        """
        ADR-004 mandate: process_batch must never propagate exceptions.
        An invalid order (empty items) is skipped; valid orders still complete.
        """
        processor = make_processor()
        valid_order = Order(items=[make_item(price=10.00, quantity=1)])
        invalid_order = Order(items=[])            # will raise internally
        orders = [valid_order, invalid_order]
        # Must not raise
        results = processor.process_batch(orders)
        # Only the valid order should appear in results
        assert len(results) == 1
        assert results[0].status == OrderStatus.PROCESSED

    def test_process_batch_all_invalid_returns_empty_list(self):
        """If every order in a batch is invalid, the result is an empty list."""
        processor = make_processor()
        orders = [
            Order(items=[]),
            Order(items=[make_item(price=-1.00, quantity=1)]),
        ]
        results = processor.process_batch(orders)
        assert results == []

    def test_process_batch_empty_input_returns_empty_list(self):
        """An empty batch input returns an empty list without raising."""
        processor = make_processor()
        results = processor.process_batch([])
        assert results == []
