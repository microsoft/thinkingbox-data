# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for updating order shipping address."""

from typing import Any, Dict, Type

from tb_business_ops_servers_202606 import InMemoryDatabase, Tool, get_schema_without_refs
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.oms.models import (
    Order,
)
from pydantic import BaseModel, ConfigDict, Field


class UpdateOrderAddressInput(BaseModel):
    """Input for update_order_address tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    order_id: str = Field(
        ..., description="Order identifier", examples=["ORD-00012345"]
    )
    new_address_line1: str = Field(
        ..., description="New shipping address line 1", examples=["456 New Street"]
    )
    new_address_city: str = Field(
        ..., description="New shipping address city", examples=["Nashville"]
    )
    new_address_state: str = Field(
        ..., description="New shipping address state", examples=["TN"]
    )
    new_address_zip: str = Field(
        ..., description="New shipping address ZIP code", examples=["37201"]
    )


class UpdateOrderAddressOutput(BaseModel):
    """Output for update_order_address tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    order_id: str = Field(
        ..., description="Order identifier", examples=["ORD-00012345"]
    )
    address_updated: bool = Field(
        ..., description="Whether address was updated", examples=[True]
    )
    new_shipping_address_line1: str = Field(
        ..., description="Updated address line 1", examples=["456 New Street"]
    )
    new_shipping_address_city: str = Field(
        ..., description="Updated address city", examples=["Nashville"]
    )
    new_shipping_address_state: str = Field(
        ..., description="Updated address state", examples=["TN"]
    )
    new_shipping_address_zip: str = Field(
        ..., description="Updated address ZIP", examples=["37201"]
    )


class UpdateOrderAddressTool(Tool):
    """Tool implementation for updating order shipping address."""

    @property
    def name(self) -> str:
        return "update_order_address"

    @property
    def description(self) -> str:
        return "Update shipping address for an order."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(UpdateOrderAddressInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(UpdateOrderAddressOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return UpdateOrderAddressInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return UpdateOrderAddressOutput

    async def run(
        self, db: InMemoryDatabase, request: UpdateOrderAddressInput
    ) -> UpdateOrderAddressOutput:
        """Update shipping address for an order."""
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

            # Update shipping address fields
            matching_order.shipping_address_line1 = request.new_address_line1
            matching_order.shipping_address_city = request.new_address_city
            matching_order.shipping_address_state = request.new_address_state
            matching_order.shipping_address_zip = request.new_address_zip

            # Save changes to database
            db.update(matching_order)

            # Return confirmation with new address
            return UpdateOrderAddressOutput(
                order_id=matching_order.id,
                address_updated=True,
                new_shipping_address_line1=matching_order.shipping_address_line1,
                new_shipping_address_city=matching_order.shipping_address_city,
                new_shipping_address_state=matching_order.shipping_address_state,
                new_shipping_address_zip=matching_order.shipping_address_zip,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to update order address: {str(e)}"
            raise Tool.ExecutionError(error_message)
