# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for creating RMA."""

from datetime import datetime, timezone
from typing import Any, Dict, Type

from ms_toloka_servers import InMemoryDatabase, Tool, get_schema_without_refs
from ms_toloka_servers.toolslib.external_retail_toolset.loop_returns.models import (
    RMARecord,
    RMAReturnReason,
    RMAStatus,
)
from pydantic import BaseModel, ConfigDict, Field

# Fixed time for testing purposes
FIXED_DATETIME = datetime(2025, 10, 1, 13, 0, 5, tzinfo=timezone.utc)


class CreateRMAInput(BaseModel):
    """Input for create_rma tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    order_id: str = Field(
        ..., description="Order identifier", examples=["ORD-00012345"]
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
    is_defective: bool = Field(
        default=False, description="Whether return is for defect", examples=[True]
    )
    refund_amount: float = Field(
        ..., description="Calculated refund amount after all fees", examples=[500.00]
    )
    restocking_fee: float = Field(
        ...,
        description="Restocking fee amount in dollars",
        examples=[0.00],
    )
    return_shipping_cost: float = Field(
        ...,
        description="Return shipping cost amount in dollars",
        examples=[0.00],
    )
    removal_fee: float = Field(
        ...,
        description="Removal fee amount in dollars",
        examples=[0.00],
    )


class CreateRMAOutput(BaseModel):
    """Output for create_rma tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    rma_id: str = Field(
        ..., description="Generated RMA identifier", examples=["RMA-00012345"]
    )
    status: RMAStatus = Field(
        ...,
        description=(
            "Current RMA status. One of: pending, approved, shipped_to_warehouse, "
            "received, refunded, cancelled"
        ),
        examples=["approved"],
    )
    created_date: str = Field(
        ..., description="Date RMA was created", examples=["2024-10-22T10:30:00Z"]
    )


class CreateRMATool(Tool):
    """Tool implementation for creating a new RMA."""

    @property
    def name(self) -> str:
        return "create_rma"

    @property
    def description(self) -> str:
        return (
            "Create a return merchandise authorization for a product return. Generates a "
            "new RMA for returning one line item from an order. This is operation initiates the return process."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CreateRMAInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CreateRMAOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return CreateRMAInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CreateRMAOutput

    async def run(
        self, db: InMemoryDatabase, request: CreateRMAInput
    ) -> CreateRMAOutput:
        """Create a new RMA record."""
        try:
            # Generate deterministic RMA ID
            existing_rmas = db.get_all(RMARecord)
            rma_count = len(existing_rmas)

            # Generate new RMA ID with prefix RMA-2 for newly created RMAs
            prefix = "RMA-20"
            new_rma_id = f"{prefix}{rma_count:06d}"

            # Ensure uniqueness
            existing_ids = {rma.id for rma in existing_rmas}
            while new_rma_id in existing_ids:
                rma_count += 1
                new_rma_id = f"{prefix}{rma_count:06d}"

            # Create current timestamp
            created_date = FIXED_DATETIME

            # Create new RMA record with status='approved'
            new_rma = RMARecord(
                id=new_rma_id,
                order_id=request.order_id,
                line_item_id=request.line_item_id,
                customer_id=request.customer_id,
                return_reason=request.return_reason,
                is_defective=request.is_defective,
                status=RMAStatus.APPROVED,
                created_date=created_date,
                refund_amount=request.refund_amount,
                restocking_fee=request.restocking_fee,
                return_shipping_cost=request.return_shipping_cost,
                removal_fee=request.removal_fee,
            )

            # Store the new RMA in database
            db.create(new_rma)

            # Return RMA creation result
            return CreateRMAOutput(
                rma_id=new_rma.id,
                status=new_rma.status,
                created_date=new_rma.created_date.isoformat(),
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to create RMA: {str(e)}"
            raise Tool.ExecutionError(error_message)
