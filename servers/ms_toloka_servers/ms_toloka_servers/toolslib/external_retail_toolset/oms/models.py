# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for OMS (Order Management System) toolset."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OrderStatus(str, Enum):
    """Order status enumeration."""

    PENDING_PAYMENT = "pending_payment"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    INSTALLATION_SCHEDULED = "installation_scheduled"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class ShippingSpeed(str, Enum):
    """Shipping speed enumeration."""

    STANDARD = "standard"
    EXPEDITED = "expedited"
    NEXT_DAY = "next_day"


class FulfillmentType(str, Enum):
    """Fulfillment type enumeration."""

    WAREHOUSE = "warehouse"
    DROP_SHIP = "drop_ship"


class OrderCancellationReason(str, Enum):
    """Order cancellation reason enumeration."""

    CUSTOMER_REQUEST = "customer_request"
    PAYMENT_FAILED = "payment_failed"
    ADDRESS_UNDELIVERABLE = "address_undeliverable"
    OUT_OF_STOCK = "out_of_stock"


class TrackingStatus(str, Enum):
    """Tracking status enumeration."""

    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELAYED = "delayed"
    DELIVERED = "delivered"
    EXCEPTION = "exception"
    RETURNED_TO_SENDER = "returned_to_sender"


class Order(BaseModel):
    """Order model from OMS."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique order identifier")
    customer_id: str = Field(..., description="Customer identifier")
    order_date: datetime = Field(..., description="Order placement date and time")
    status: OrderStatus = Field(
        default=OrderStatus.PENDING_PAYMENT, description="Current order status"
    )
    subtotal_amount: float = Field(
        ..., description="Subtotal before discounts and shipping"
    )
    discount_amount: float = Field(default=0.0, description="Total discount applied")
    points_used: int = Field(default=0, description="Reward points used")
    points_value: float = Field(default=0.0, description="Dollar value of points used")
    shipping_cost: float = Field(default=0.0, description="Shipping cost")
    total_amount: float = Field(
        ..., description="Total order amount after all adjustments"
    )
    shipping_address_line1: str = Field(..., description="Shipping address line 1")
    shipping_address_city: str = Field(..., description="Shipping address city")
    shipping_address_state: str = Field(..., description="Shipping address state")
    shipping_address_zip: str = Field(..., description="Shipping address ZIP code")
    shipping_speed: ShippingSpeed = Field(
        default=ShippingSpeed.STANDARD, description="Shipping speed selected"
    )
    fulfillment_type: FulfillmentType = Field(
        default=FulfillmentType.WAREHOUSE, description="Order fulfillment type"
    )
    installation_service_id: Optional[str] = Field(
        None, description="Installation service job ID if applicable"
    )

    def get_id(self) -> str:
        """Return the ID of this order."""
        return self.id


class OrderLineItem(BaseModel):
    """Order line item model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique line item identifier")
    order_id: str = Field(..., description="Associated order identifier")
    sku: str = Field(..., description="Product SKU")
    product_name: str = Field(..., description="Product name")
    quantity: int = Field(..., description="Quantity ordered")
    base_price: float = Field(..., description="Base price per unit")
    discount_amount: float = Field(
        default=0.0, description="Discount amount applied to this line"
    )
    final_price: float = Field(..., description="Final price after discount")

    def get_id(self) -> str:
        """Return the ID of this line item."""
        return self.id


class Shipment(BaseModel):
    """Shipment model from OMS."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique shipment identifier")
    order_id: str = Field(..., description="Associated order identifier")
    carrier: str = Field(..., description="Shipping carrier name")
    tracking_number: str = Field(..., description="Tracking number")
    ship_date: datetime = Field(..., description="Date when shipment was created")
    estimated_delivery_date: datetime = Field(
        ..., description="Estimated delivery date"
    )
    actual_delivery_date: Optional[datetime] = Field(
        None, description="Actual delivery date"
    )

    def get_id(self) -> str:
        """Return the ID of this shipment."""
        return self.id


class CarrierTracking(BaseModel):
    """Carrier tracking model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    tracking_number: str = Field(..., description="Tracking number (primary key)")
    shipment_id: str = Field(..., description="Associated shipment identifier")
    carrier: str = Field(..., description="Shipping carrier name")
    status: TrackingStatus = Field(
        default=TrackingStatus.PENDING, description="Current tracking status"
    )
    current_location: Optional[str] = Field(
        None, description="Current package location"
    )
    estimated_delivery: datetime = Field(..., description="Estimated delivery date")
    last_update: datetime = Field(..., description="Last tracking update timestamp")

    def get_id(self) -> str:
        """Return the tracking number as ID."""
        return self.tracking_number
