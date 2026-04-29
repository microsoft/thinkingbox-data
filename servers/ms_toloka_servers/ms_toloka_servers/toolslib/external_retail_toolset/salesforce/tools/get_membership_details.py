# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for getting membership details from CDP."""

from typing import Any, Dict, Type

from ms_toloka_servers import InMemoryDatabase, Tool, get_schema_without_refs
from ms_toloka_servers.toolslib.external_retail_toolset.salesforce.models import (
    MembershipRecord,
    MembershipStatus,
)
from pydantic import BaseModel, ConfigDict, Field


class GetMembershipDetailsInput(BaseModel):
    """Input for get_membership_details tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    customer_id: str = Field(
        ...,
        description="Customer identifier to retrieve membership",
        examples=["CUS-00012345"],
    )


class GetMembershipDetailsOutput(BaseModel):
    """Output for get_membership_details tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    membership_id: str = Field(
        ..., description="Unique membership identifier", examples=["MEM-00012345"]
    )
    customer_id: str = Field(
        ..., description="Customer identifier", examples=["CUS-00012345"]
    )
    membership_type: str = Field(..., description="Membership type", examples=["plus"])
    start_date: str = Field(
        ..., description="Membership start date", examples=["2024-01-01T00:00:00Z"]
    )
    end_date: str = Field(
        ..., description="Membership end date", examples=["2024-12-31T23:59:59Z"]
    )
    status: MembershipStatus = Field(
        ..., description="Membership status", examples=["active"]
    )
    points_balance: int = Field(
        ..., description="Current reward points balance", examples=[2500]
    )


class GetMembershipDetailsTool(Tool):
    """Tool implementation for retrieving membership details from CDP."""

    @property
    def name(self) -> str:
        return "get_membership_details"

    @property
    def description(self) -> str:
        return (
            "Retrieve customer membership information and points balance. "
            "Fetches TechHome Plus membership details including status, "
            "start/end dates, and current points balance. Used to verify "
            "membership status for policy application and check points "
            "availability for disputes."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetMembershipDetailsInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetMembershipDetailsOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetMembershipDetailsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetMembershipDetailsOutput

    async def run(
        self, db: InMemoryDatabase, request: GetMembershipDetailsInput
    ) -> GetMembershipDetailsOutput:
        """Retrieve membership details by customer ID."""
        try:
            # Get all membership records
            all_memberships = db.get_all(MembershipRecord)

            # Find active membership for this customer
            matching_membership = None
            for membership in all_memberships:
                if (
                    membership.customer_id == request.customer_id
                    and membership.status == MembershipStatus.ACTIVE
                ):
                    matching_membership = membership
                    break

            # If no active membership found, raise 404 error
            if not matching_membership:
                raise Tool.ExecutionError(
                    f"No active membership found for customer: {request.customer_id}"
                )

            # Return membership details
            return GetMembershipDetailsOutput(
                membership_id=matching_membership.id,
                customer_id=matching_membership.customer_id,
                membership_type=matching_membership.membership_type,
                start_date=matching_membership.start_date.isoformat(),
                end_date=matching_membership.end_date.isoformat(),
                status=matching_membership.status,
                points_balance=matching_membership.points_balance,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to retrieve membership details: {str(e)}"
            raise Tool.ExecutionError(error_message)
