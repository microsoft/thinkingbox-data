# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for Hardware Procurement create_order."""

from typing import Any, Dict, Type

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.workday.models import OfficeLocation
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field


class HardwareProcurementCreateOrderInput(BaseModel):
    """Input for hardware_procurement_create_order tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    device_model: str = Field(
        ...,
        description="Device model to order",
        examples=["Google Pixel 7a"],
    )
    quantity: int = Field(
        ...,
        description="Quantity to order",
        examples=[1],
    )
    deliver_to: OfficeLocation = Field(
        ...,
        description="Office location for delivery",
        examples=["New York"],
    )


class HardwareProcurementCreateOrderOutput(BaseModel):
    """Output for hardware_procurement_create_order tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    order_id: str = Field(
        ..., description="Purchase order identifier in format HWO-XXXXXXX"
    )


class HardwareProcurementCreateOrderTool(Tool):
    """Tool implementation for creating hardware procurement orders."""

    @property
    def name(self) -> str:
        return "create_order"

    @property
    def description(self) -> str:
        return (
            "Place hardware order with vendor. Creates a purchase order for hardware procurement "
            "from external suppliers. Use when inventory is unavailable and procurement is approved. "
            "Lead times are: Laptops 18 days, Phones 14 days, Other devices 21 days. "
            "Inform user of expected delivery timeline."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(HardwareProcurementCreateOrderInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(HardwareProcurementCreateOrderOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return HardwareProcurementCreateOrderInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return HardwareProcurementCreateOrderOutput

    async def run(
        self, db: InMemoryDatabase, request: HardwareProcurementCreateOrderInput
    ) -> HardwareProcurementCreateOrderOutput:
        """Create hardware procurement order.

        This is a vendor API call that always returns the same order ID.
        No database write is performed as this is an external system call.
        """
        try:
            # According to specification: "Always generate same order ID HWO-0056435 (always!!!)"
            # This simulates a call to an external vendor API
            return HardwareProcurementCreateOrderOutput(order_id="HWO-0056435")

        except Exception as e:
            # Catch any unexpected exceptions and convert them to ExecutionError
            error_message = f"Failed to create hardware procurement order: {str(e)}"
            raise Tool.ExecutionError(error_message)
