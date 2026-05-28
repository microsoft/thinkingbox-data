# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for cancelling an order."""

from typing import Any, Dict, Type

from sandbox_servers import InMemoryDatabase, Tool, get_schema_without_refs
from sandbox_servers.toolslib.external_retail_toolset.oms.models import (
    Order,
    OrderCancellationReason,
    OrderStatus,
)
from pydantic import BaseModel, ConfigDict, Field


class CancelOrderInput(BaseModel):
    """Input for cancel_order tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    order_id: str = Field(
        ..., description="Order identifier to cancel", examples=["ORD-00012345"]
    )
    cancellation_reason: OrderCancellationReason = Field(
        ...,
        description="Reason for cancellation: customer_request, payment_failed, address_undeliverable, or out_of_stock",
        examples=["customer_request"],
    )


class CancelOrderOutput(BaseModel):
    """Output for cancel_order tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    order_id: str = Field(
        ..., description="Order identifier", examples=["ORD-00012345"]
    )
    status: str = Field(..., description="Updated order status", examples=["cancelled"])
    refund_initiated: bool = Field(
        ...,
        description="Whether refund was automatically initiated",
        examples=[True],
    )


class CancelOrderTool(Tool):
    """Tool implementation for cancelling an order."""

    @property
    def name(self) -> str:
        return "cancel_order"

    @property
    def description(self) -> str:
        return "Cancels an order and updates status to cancelled."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CancelOrderInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CancelOrderOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return CancelOrderInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CancelOrderOutput

    async def run(
        self, db: InMemoryDatabase, request: CancelOrderInput
    ) -> CancelOrderOutput:
        """Cancel an order if it hasn't been shipped yet."""
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

            # Determine if refund should be initiated
            # Refund initiated if order was already in processing (payment authorized)
            refund_initiated = matching_order.status == OrderStatus.PROCESSING

            # Update order status to cancelled
            matching_order.status = OrderStatus.CANCELLED
            db.update(matching_order)

            # Return cancellation confirmation
            return CancelOrderOutput(
                order_id=matching_order.id,
                status=OrderStatus.CANCELLED.value,
                refund_initiated=refund_initiated,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to cancel order: {str(e)}"
            raise Tool.ExecutionError(error_message)
