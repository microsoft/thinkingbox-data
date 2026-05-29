# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for retrieving order details."""

from typing import Any, Dict, List, Optional, Type

from tb_business_ops_servers_202606 import InMemoryDatabase, Tool, get_schema_without_refs
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.oms.models import (
    Order,
    OrderLineItem,
)
from pydantic import BaseModel, ConfigDict, Field


class GetOrderInput(BaseModel):
    """Input for get_order tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    order_id: str = Field(
        ...,
        description="Unique order identifier provided by customer",
        examples=["ORD-00012345"],
    )


class LineItemOutput(BaseModel):
    """Line item output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    id: str = Field(..., description="Line item identifier", examples=["LIN-00012345"])
    sku: str = Field(..., description="Product SKU", examples=["SKU-00012345"])
    product_name: str = Field(
        ...,
        description="Product name",
        examples=["Samsung 28 cu ft French Door Refrigerator"],
    )
    quantity: int = Field(..., description="Quantity ordered", examples=[1])
    base_price: float = Field(..., description="Base price per unit", examples=[899.99])
    discount_amount: float = Field(
        ..., description="Discount amount applied to this line", examples=[90.00]
    )
    final_price: float = Field(
        ..., description="Final price after discount", examples=[809.99]
    )


class GetOrderOutput(BaseModel):
    """Output for get_order tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    id: str = Field(..., description="Order identifier", examples=["ORD-00012345"])
    customer_id: str = Field(
        ..., description="Customer identifier", examples=["CUS-00012345"]
    )
    order_date: str = Field(
        ..., description="Order date", examples=["2024-10-15T14:23:00Z"]
    )
    status: str = Field(..., description="Order status", examples=["shipped"])
    subtotal_amount: float = Field(
        ..., description="Subtotal before discounts", examples=[899.99]
    )
    discount_amount: float = Field(
        ..., description="Total discount applied", examples=[90.00]
    )
    points_used: int = Field(..., description="Reward points used", examples=[500])
    points_value: float = Field(
        ..., description="Dollar value of points", examples=[25.00]
    )
    shipping_cost: float = Field(..., description="Shipping cost", examples=[0.00])
    total_amount: float = Field(
        ..., description="Total order amount", examples=[784.99]
    )
    shipping_address_line1: str = Field(
        ..., description="Shipping address line 1", examples=["123 Main St"]
    )
    shipping_address_city: str = Field(
        ..., description="Shipping address city", examples=["Memphis"]
    )
    shipping_address_state: str = Field(
        ..., description="Shipping address state", examples=["TN"]
    )
    shipping_address_zip: str = Field(
        ..., description="Shipping address ZIP", examples=["38103"]
    )
    shipping_speed: str = Field(
        ..., description="Shipping speed", examples=["standard"]
    )
    fulfillment_type: str = Field(
        ..., description="Fulfillment type", examples=["warehouse"]
    )
    installation_service_id: Optional[str] = Field(
        None, description="Installation service ID", examples=["JOB-00001234"]
    )
    line_items: List[LineItemOutput] = Field(
        ..., description="Array of order line items with details"
    )


class GetOrderTool(Tool):
    """Tool implementation for retrieving complete order details."""

    @property
    def name(self) -> str:
        return "get_order"

    @property
    def description(self) -> str:
        return (
            "Retrieve complete order details including status, items, pricing, and discounts. "
            "Fetches full order information from the Order Management System including order "
            "status, line items, pricing breakdown, applied discounts, points usage, shipping "
            "details, and installation service reference if applicable. Essential for processing "
            "returns, cancellations, modifications, and discount disputes."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetOrderInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetOrderOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetOrderInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetOrderOutput

    async def run(self, db: InMemoryDatabase, request: GetOrderInput) -> GetOrderOutput:
        """Retrieve order details by order ID."""
        try:
            # Get all orders
            all_orders = db.get_all(Order)

            # Find matching order by ID
            matching_order = None
            for order in all_orders:
                if order.id == request.order_id:
                    matching_order = order
                    break

            # If no order found, raise 404 error
            if not matching_order:
                raise Tool.ExecutionError(f"Order not found: {request.order_id}")

            # Get all line items for this order
            all_line_items = db.get_all(OrderLineItem)
            order_line_items = [
                item for item in all_line_items if item.order_id == request.order_id
            ]

            # Convert line items to output format
            line_items_output = [
                LineItemOutput(
                    id=item.id,
                    sku=item.sku,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    base_price=item.base_price,
                    discount_amount=item.discount_amount,
                    final_price=item.final_price,
                )
                for item in order_line_items
            ]

            # Return order information with line items
            return GetOrderOutput(
                id=matching_order.id,
                customer_id=matching_order.customer_id,
                order_date=matching_order.order_date.isoformat(),
                status=matching_order.status.value,
                subtotal_amount=matching_order.subtotal_amount,
                discount_amount=matching_order.discount_amount,
                points_used=matching_order.points_used,
                points_value=matching_order.points_value,
                shipping_cost=matching_order.shipping_cost,
                total_amount=matching_order.total_amount,
                shipping_address_line1=matching_order.shipping_address_line1,
                shipping_address_city=matching_order.shipping_address_city,
                shipping_address_state=matching_order.shipping_address_state,
                shipping_address_zip=matching_order.shipping_address_zip,
                shipping_speed=matching_order.shipping_speed.value,
                fulfillment_type=matching_order.fulfillment_type.value,
                installation_service_id=matching_order.installation_service_id,
                line_items=line_items_output,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to retrieve order: {str(e)}"
            raise Tool.ExecutionError(error_message)
