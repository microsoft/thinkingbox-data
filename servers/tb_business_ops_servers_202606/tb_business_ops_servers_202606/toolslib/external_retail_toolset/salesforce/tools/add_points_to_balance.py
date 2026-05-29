# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for adding reward points to customer balance."""

from typing import Any, Dict, Type

from tb_business_ops_servers_202606 import InMemoryDatabase, Tool, get_schema_without_refs
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.salesforce.models import (
    MembershipRecord,
    MembershipStatus,
    PointsAdjustmentReason,
)
from pydantic import BaseModel, ConfigDict, Field


class AddPointsToBalanceInput(BaseModel):
    """Input for add_points_to_balance tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    customer_id: str = Field(
        ..., description="Customer identifier", examples=["CUS-00012345"]
    )
    points_to_add: int = Field(
        ..., description="Number of points to credit", examples=[500]
    )
    points_reason: PointsAdjustmentReason = Field(
        ...,
        description="Reason for points adjustment: refund_return, service_recovery, manual_adjustment",
        examples=["refund_return"],
    )


class AddPointsToBalanceOutput(BaseModel):
    """Output for add_points_to_balance tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    customer_id: str = Field(
        ..., description="Customer identifier", examples=["CUS-00012345"]
    )
    old_balance: int = Field(
        ..., description="Previous points balance", examples=[2500]
    )
    points_added: int = Field(..., description="Number of points added", examples=[500])
    new_balance: int = Field(..., description="New points balance", examples=[3000])


class AddPointsToBalanceTool(Tool):
    """Tool implementation for adding reward points to customer balance."""

    @property
    def name(self) -> str:
        return "add_points_to_balance"

    @property
    def description(self) -> str:
        return "Add reward points to customer's Plus membership balance."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(AddPointsToBalanceInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(AddPointsToBalanceOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return AddPointsToBalanceInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return AddPointsToBalanceOutput

    async def run(
        self, db: InMemoryDatabase, request: AddPointsToBalanceInput
    ) -> AddPointsToBalanceOutput:
        """Add points to customer's membership balance."""
        try:
            # Find any membership for this customer (active or not)
            all_memberships = db.get_all(MembershipRecord)
            customer_membership = None
            for membership in all_memberships:
                if membership.customer_id == request.customer_id:
                    customer_membership = membership
                    break

            # If no membership found, raise error (customer needs a membership record)
            if not customer_membership:
                raise Tool.ExecutionError(
                    f"No membership record found for customer {request.customer_id}. "
                    "Customer must have a membership record to receive points."
                )

            # Store old balance
            old_balance = customer_membership.points_balance

            # Add points to balance
            new_balance = old_balance + request.points_to_add

            # Update membership record
            customer_membership.points_balance = new_balance
            db.update(customer_membership)

            # Return result
            return AddPointsToBalanceOutput(
                customer_id=request.customer_id,
                old_balance=old_balance,
                points_added=request.points_to_add,
                new_balance=new_balance,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to add points to balance: {str(e)}"
            raise Tool.ExecutionError(error_message)
