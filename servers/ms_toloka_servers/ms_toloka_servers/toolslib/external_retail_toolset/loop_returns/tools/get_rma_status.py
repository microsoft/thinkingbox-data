# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for getting RMA status."""

from typing import Any, Dict, Type

from ms_toloka_servers import InMemoryDatabase, Tool, get_schema_without_refs
from ms_toloka_servers.toolslib.external_retail_toolset.loop_returns.models import (
    RMARecord,
    RMAReturnReason,
    RMAStatus,
)
from pydantic import BaseModel, ConfigDict, Field


class GetRMAStatusInput(BaseModel):
    """Input for get_rma_status tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    rma_id: str = Field(
        ...,
        description="Return authorization identifier",
        examples=["RMA-00012345"],
    )


class GetRMAStatusOutput(BaseModel):
    """Output for get_rma_status tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    rma_id: str = Field(
        ..., description="Return authorization identifier", examples=["RMA-00012345"]
    )
    order_id: str = Field(
        ..., description="Associated order identifier", examples=["ORD-00012345"]
    )
    line_item_id: str = Field(
        ..., description="Specific line item being returned", examples=["LIN-00012345"]
    )
    customer_id: str = Field(
        ..., description="Customer identifier", examples=["CUS-00012345"]
    )
    return_reason: RMAReturnReason = Field(
        ...,
        description=(
            "Reason for return. One of: defective, wrong_item_received, "
            "changed_mind, not_as_expected, damaged_in_transit"
        ),
        examples=["defective"],
    )
    status: RMAStatus = Field(
        ...,
        description=(
            "Current RMA status. One of: pending, approved, shipped_to_warehouse, "
            "received, refunded, cancelled"
        ),
        examples=["approved"],
    )
    refund_amount: float = Field(
        ..., description="Calculated refund amount after all fees", examples=[416.01]
    )
    restocking_fee: float = Field(
        ...,
        description="15% fee for non-defective opened items (standard customers only)",
        examples=[75.00],
    )
    return_shipping_cost: float = Field(
        ...,
        description="$8.99 for non-defective small items (standard customers only)",
        examples=[8.99],
    )
    removal_fee: float = Field(
        ...,
        description="$50 for non-defective installed major appliances",
        examples=[0.00],
    )
    created_date: str = Field(
        ..., description="Date RMA was created", examples=["2024-10-20T09:15:00Z"]
    )


class GetRMAStatusTool(Tool):
    """Tool implementation for retrieving RMA status."""

    @property
    def name(self) -> str:
        return "get_rma_status"

    @property
    def description(self) -> str:
        return (
            "Check status of an existing return authorization. Retrieves RMA status "
            "including refund amount breakdown, fees, and processing status. Used when "
            "customer inquires about return status or refund timing."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetRMAStatusInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetRMAStatusOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetRMAStatusInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetRMAStatusOutput

    async def run(
        self, db: InMemoryDatabase, request: GetRMAStatusInput
    ) -> GetRMAStatusOutput:
        """Retrieve RMA status by RMA ID."""
        try:
            # Get all RMA records
            all_rmas = db.get_all(RMARecord)

            # Find matching RMA
            matching_rma = None
            for rma in all_rmas:
                if rma.id == request.rma_id:
                    matching_rma = rma
                    break

            # If no RMA found, raise 404 error
            if not matching_rma:
                raise Tool.ExecutionError(f"RMA not found: {request.rma_id}")

            # Return RMA status details
            return GetRMAStatusOutput(
                rma_id=matching_rma.id,
                order_id=matching_rma.order_id,
                line_item_id=matching_rma.line_item_id,
                customer_id=matching_rma.customer_id,
                return_reason=matching_rma.return_reason,
                status=matching_rma.status,
                refund_amount=matching_rma.refund_amount,
                restocking_fee=matching_rma.restocking_fee,
                return_shipping_cost=matching_rma.return_shipping_cost,
                removal_fee=matching_rma.removal_fee,
                created_date=matching_rma.created_date.isoformat(),
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to retrieve RMA status: {str(e)}"
            raise Tool.ExecutionError(error_message)
