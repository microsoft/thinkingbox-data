# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for updating order shipping speed."""

from typing import Any, Dict, Type

from tb_business_ops_servers_202606 import InMemoryDatabase, Tool, get_schema_without_refs
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.oms.models import (
    Order,
    OrderStatus,
    ShippingSpeed,
)
from pydantic import BaseModel, ConfigDict, Field

# Shipping cost mapping
SHIPPING_COSTS = {
    ShippingSpeed.STANDARD: 0.00,
    ShippingSpeed.EXPEDITED: 15.00,
    ShippingSpeed.NEXT_DAY: 29.99,
}


class UpdateShippingSpeedInput(BaseModel):
    """Input for update_shipping_speed tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    order_id: str = Field(
        ..., description="Order identifier", examples=["ORD-00012345"]
    )
    new_shipping_speed: ShippingSpeed = Field(
        ...,
        description="New shipping speed: standard, expedited, or next_day",
        examples=["expedited"],
    )


class UpdateShippingSpeedOutput(BaseModel):
    """Output for update_shipping_speed tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    order_id: str = Field(
        ..., description="Order identifier", examples=["ORD-00012345"]
    )
    old_shipping_speed: str = Field(
        ..., description="Previous shipping speed", examples=["standard"]
    )
    new_shipping_speed: str = Field(
        ..., description="Updated shipping speed", examples=["expedited"]
    )
    cost_difference: float = Field(
        ...,
        description="Cost difference (positive if customer owes more, negative if refund due). Standard=$0, Expedited=$15, Next-day=$29.99",
        examples=[15.00],
    )
    updated: bool = Field(
        ..., description="Whether shipping speed was updated", examples=[True]
    )


class UpdateShippingSpeedTool(Tool):
    """Tool implementation for updating order shipping speed."""

    @property
    def name(self) -> str:
        return "update_shipping_speed"

    @property
    def description(self) -> str:
        return (
            "Upgrade or downgrade shipping speed for an order. The agent should check the order "
            "status, timing, and company policy to determine if shipping speed changes are "
            "appropriate. For example, the policy may restrict changes to orders placed within "
            "2 hours or in specific statuses, but the agent must verify this from the policy "
            "document. Returns the cost difference that must be charged or refunded using "
            "separate charge_customer or create_refund tool."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(UpdateShippingSpeedInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(UpdateShippingSpeedOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return UpdateShippingSpeedInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return UpdateShippingSpeedOutput

    async def run(
        self, db: InMemoryDatabase, request: UpdateShippingSpeedInput
    ) -> UpdateShippingSpeedOutput:
        """Update shipping speed for an order."""
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

            # Store old shipping speed
            old_shipping_speed = matching_order.shipping_speed

            # Calculate cost difference
            old_cost = SHIPPING_COSTS[old_shipping_speed]
            new_cost = SHIPPING_COSTS[request.new_shipping_speed]
            cost_difference = new_cost - old_cost

            # Update shipping speed and cost
            matching_order.shipping_speed = request.new_shipping_speed
            matching_order.shipping_cost = new_cost

            # Recalculate total amount
            matching_order.total_amount = (
                matching_order.subtotal_amount
                - matching_order.discount_amount
                - matching_order.points_value
                + new_cost
            )

            # Save changes to database
            db.update(matching_order)

            # Return confirmation with cost difference
            return UpdateShippingSpeedOutput(
                order_id=matching_order.id,
                old_shipping_speed=old_shipping_speed.value,
                new_shipping_speed=request.new_shipping_speed.value,
                cost_difference=cost_difference,
                updated=True,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to update shipping speed: {str(e)}"
            raise Tool.ExecutionError(error_message)
