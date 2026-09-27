"""
Migrated from OrderProcessor.java — WITHOUT document context (no ADRs, no Javadoc).

ABLATION VARIANT: This file represents what a migration agent produces when it has
NO access to project documentation (pom.xml CVEs, ADR constraints, Javadoc intent).
It is intentionally degraded to demonstrate the impact of document understanding.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional
import sys


class OrderStatus(Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    CANCELLED = "CANCELLED"


@dataclass
class OrderItem:
    name: str
    price: Decimal
    quantity: int


@dataclass
class Order:
    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING
    subtotal: Decimal = Decimal("0")
    discount: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")
    total: Decimal = Decimal("0")


class OrderProcessor:
    """Order processing service."""

    # CONSTRAINT VIOLATION 1 (ADR-002): magic numbers instead of named constants
    # Without ADR-002 context, agent does not know these are contractual values
    # that MUST be named constants. The ADR explicitly says "Using magic numbers is FORBIDDEN."

    def process_order(self, order: Order) -> Order:
        self._validate_order(order)

        subtotal = self._calculate_subtotal(order.items)
        # CONSTRAINT VIOLATION 2 (ADR-002): magic number 500 instead of BULK_DISCOUNT_THRESHOLD
        discount = subtotal * Decimal("0.10") if subtotal > Decimal("500") else Decimal("0")
        taxable = subtotal - discount
        # CONSTRAINT VIOLATION 3 (ADR-002): magic number 0.08 instead of TAX_RATE
        tax = taxable * Decimal("0.08")
        total = taxable + tax

        order.subtotal = subtotal
        order.discount = discount
        order.tax = tax
        order.total = total
        order.status = OrderStatus.PROCESSED
        return order

    def _validate_order(self, order: Optional[Order]) -> None:
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
        return sum((item.price * item.quantity for item in items), Decimal("0"))

    def process_batch(self, orders: list[Order]) -> list[Order]:
        # CONSTRAINT VIOLATION 4 (ADR-004): agent used fail-fast instead of
        # per-item fault tolerance. Without ADR-004, agent assumed standard behaviour.
        # ADR-004 says: "Failing fast on the first error is FORBIDDEN in batch context."
        processed = []
        for order in orders:
            # WRONG: raises on first bad order, stops processing the rest
            processed.append(self.process_order(order))
        return processed
