"""Migrated from OrderProcessor.java — com.example.monolith.service"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional
import sys


# ─────────────────────────────────────────────────────────────────────────────
# Stub models
# ─────────────────────────────────────────────────────────────────────────────

class OrderStatus(Enum):
    """Possible states of an order."""

    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    CANCELLED = "CANCELLED"


@dataclass
class OrderItem:
    """A single line-item within an order."""

    name: str
    price: Decimal
    quantity: int


@dataclass
class Order:
    """Represents a customer order."""

    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING
    subtotal: Decimal = Decimal("0")
    discount: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")
    total: Decimal = Decimal("0")


# ─────────────────────────────────────────────────────────────────────────────
# OrderProcessor
# ─────────────────────────────────────────────────────────────────────────────

class OrderProcessor:
    """Processes incoming orders, applying validation and discount logic."""

    TAX_RATE: Decimal = Decimal("0.08")
    BULK_DISCOUNT_THRESHOLD: Decimal = Decimal("500.00")
    BULK_DISCOUNT_RATE: Decimal = Decimal("0.10")

    def process_order(self, order: Order) -> Order:
        """Process a single order: validate, apply discounts, calculate tax.

        Raises:
            ValueError: for invalid orders or items.
        """
        self._validate_order(order)

        subtotal = self._calculate_subtotal(order.items)
        discount = self._calculate_discount(subtotal)
        taxable_amount = subtotal - discount
        tax = taxable_amount * self.TAX_RATE
        total = taxable_amount + tax

        order.subtotal = subtotal
        order.discount = discount
        order.tax = tax
        order.total = total
        order.status = OrderStatus.PROCESSED

        return order

    def _validate_order(self, order: Optional[Order]) -> None:
        """Validate that order and its items are non-null and non-empty.

        Raises:
            ValueError: for null, empty, or malformed orders.
        """
        if order is None:
            raise ValueError("Order must not be null")
        if not order.items:
            raise ValueError("Order must contain at least one item")
        for item in order.items:
            if item.price is None or item.price < Decimal("0"):
                raise ValueError(f"Item price must be non-negative: {item.name}")
            if item.quantity <= 0:
                raise ValueError(f"Item quantity must be positive: {item.name}")

    def _calculate_subtotal(self, items: list[OrderItem]) -> Decimal:
        """Sum price * quantity for all items."""
        return sum((item.price * item.quantity for item in items), Decimal("0"))

    def _calculate_discount(self, subtotal: Decimal) -> Decimal:
        """Apply a 10% bulk discount when subtotal exceeds $500."""
        if subtotal > self.BULK_DISCOUNT_THRESHOLD:
            return subtotal * self.BULK_DISCOUNT_RATE
        return Decimal("0")

    def process_batch(self, orders: list[Order]) -> list[Order]:
        """Process a batch of orders. Skips invalid orders, logs to stderr."""
        processed: list[Order] = []
        for order in orders:
            try:
                processed.append(self.process_order(order))
            except ValueError as exc:
                print(f"Skipping invalid order: {exc}", file=sys.stderr)
        return processed
