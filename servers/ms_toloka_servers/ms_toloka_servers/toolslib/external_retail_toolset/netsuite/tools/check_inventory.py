# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for checking inventory availability."""

from typing import Any, Dict, Optional, Type

from ms_toloka_servers import InMemoryDatabase, Tool, get_schema_without_refs
from ms_toloka_servers.toolslib.external_retail_toolset.netsuite.models import (
    InventoryRecord,
)
from pydantic import BaseModel, ConfigDict, Field


class CheckInventoryInput(BaseModel):
    """Input for check_inventory tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    sku: str = Field(
        ...,
        description="Product SKU to check availability",
        examples=["SKU-00012345"],
    )


class CheckInventoryOutput(BaseModel):
    """Output for check_inventory tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    sku: str = Field(
        ..., description="Product SKU identifier", examples=["SKU-00012345"]
    )
    available_quantity: int = Field(
        ..., description="Available quantity in stock", examples=[5]
    )
    reserved_quantity: int = Field(
        ..., description="Reserved quantity for pending orders", examples=[2]
    )
    warehouse_location: Optional[str] = Field(
        None, description="Warehouse location code", examples=["Memphis-A12"]
    )
    restock_date: Optional[str] = Field(
        None,
        description="Expected restock date if out of stock",
        examples=["2024-11-05T00:00:00Z"],
    )
    expected_restock_quantity: Optional[int] = Field(
        None, description="Expected quantity on restock", examples=[50]
    )


class CheckInventoryTool(Tool):
    """Tool implementation for checking product availability and restock information."""

    @property
    def name(self) -> str:
        return "check_inventory"

    @property
    def description(self) -> str:
        return (
            "Check product availability and restock information. Queries real-time "
            "inventory levels for a specific SKU including available quantity, reserved "
            "quantity, and restock date if out of stock. Critical for determining if "
            "replacement orders can be fulfilled immediately or if customer needs to wait."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CheckInventoryInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CheckInventoryOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return CheckInventoryInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CheckInventoryOutput

    async def run(
        self, db: InMemoryDatabase, request: CheckInventoryInput
    ) -> CheckInventoryOutput:
        """Check inventory availability by SKU."""
        try:
            # Get all inventory records
            all_inventory = db.get_all(InventoryRecord)

            # Find matching inventory record by SKU
            matching_inventory = None
            for inventory in all_inventory:
                if inventory.sku == request.sku:
                    matching_inventory = inventory
                    break

            # If no inventory found, raise 404 error
            if not matching_inventory:
                raise Tool.ExecutionError(
                    f"SKU not found in inventory system: {request.sku}"
                )

            # Return inventory information
            return CheckInventoryOutput(
                sku=matching_inventory.sku,
                available_quantity=matching_inventory.available_quantity,
                reserved_quantity=matching_inventory.reserved_quantity,
                warehouse_location=matching_inventory.warehouse_location,
                restock_date=(
                    matching_inventory.restock_date.isoformat()
                    if matching_inventory.restock_date
                    else None
                ),
                expected_restock_quantity=matching_inventory.expected_restock_quantity,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to check inventory: {str(e)}"
            raise Tool.ExecutionError(error_message)
