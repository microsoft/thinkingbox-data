# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for updating membership status in CDP."""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional, Type

from tb_business_ops_servers_202606 import InMemoryDatabase, Tool, get_schema_without_refs
from tb_business_ops_servers_202606.toolslib.external_retail_toolset.salesforce.models import (
    CustomerProfile,
    CustomerTier,
    MembershipRecord,
    MembershipStatus,
)
from pydantic import BaseModel, ConfigDict, Field

# Fixed time for testing purposes
FIXED_DATETIME = datetime(2025, 10, 1, 13, 0, 5, tzinfo=timezone.utc)


class MembershipAction(str, Enum):
    """Membership action enumeration."""

    UPGRADE = "upgrade"
    CANCEL = "cancel"


class UpdateMembershipStatusInput(BaseModel):
    """Input for update_membership_status tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    customer_id: str = Field(
        ..., description="Customer identifier", examples=["CUS-00012345"]
    )
    action: MembershipAction = Field(
        ...,
        description="Action to perform: upgrade or cancel",
        examples=["upgrade"],
    )
    membership_type: Optional[str] = Field(
        None,
        description="Required if action is upgrade. Currently only plus is supported",
        examples=["plus"],
    )


class UpdateMembershipStatusOutput(BaseModel):
    """Output for update_membership_status tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    customer_id: str = Field(
        ..., description="Customer identifier", examples=["CUS-00012345"]
    )
    membership_id: Optional[str] = Field(
        None,
        description="Membership identifier (for upgrade)",
        examples=["MEM-00012345"],
    )
    new_tier: CustomerTier = Field(
        ..., description="Updated customer tier", examples=["plus_member"]
    )
    action_completed: str = Field(
        ..., description="Action that was completed", examples=["upgraded"]
    )
    start_date: Optional[str] = Field(
        None,
        description="Membership start date (for upgrade)",
        examples=["2024-10-22T00:00:00Z"],
    )
    end_date: Optional[str] = Field(
        None,
        description="Membership end date (for upgrade)",
        examples=["2025-10-22T23:59:59Z"],
    )


class UpdateMembershipStatusTool(Tool):
    """Tool implementation for updating membership status."""

    @property
    def name(self) -> str:
        return "update_membership_status"

    @property
    def description(self) -> str:
        return (
            "Upgrade customer to Plus membership or cancel membership. The agent should check "
            "the customer's current membership status and company policy to determine if the "
            "action is appropriate. Updates customer membership status - either creates new Plus "
            "membership (upgrade) or cancels existing membership. When upgrading, automatically "
            "updates customer_tier in both CDP and Zendesk. When cancelling, reverts customer_tier "
            "to standard."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(UpdateMembershipStatusInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(UpdateMembershipStatusOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return UpdateMembershipStatusInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return UpdateMembershipStatusOutput

    async def run(
        self, db: InMemoryDatabase, request: UpdateMembershipStatusInput
    ) -> UpdateMembershipStatusOutput:
        """Update membership status for a customer."""
        try:
            # Get customer profile
            all_profiles = db.get_all(CustomerProfile)
            customer_profile = None
            for profile in all_profiles:
                if profile.id == request.customer_id:
                    customer_profile = profile
                    break

            if not customer_profile:
                raise Tool.ExecutionError(f"Customer not found: {request.customer_id}")

            # Handle upgrade action
            if request.action == MembershipAction.UPGRADE:
                if not request.membership_type:
                    raise Tool.ExecutionError(
                        "membership_type is required when action is upgrade"
                    )

                # Get all memberships for generating new ID
                all_memberships = db.get_all(MembershipRecord)

                # Generate new membership ID
                existing_ids = [m.id for m in all_memberships]
                counter = 1
                while True:
                    new_membership_id = f"MEM-2{counter:07d}"
                    if new_membership_id not in existing_ids:
                        break
                    counter += 1

                # Create new membership record
                now = FIXED_DATETIME
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = (start_date + timedelta(days=365)).replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )

                new_membership = MembershipRecord(
                    id=new_membership_id,
                    customer_id=request.customer_id,
                    membership_type=request.membership_type,
                    start_date=start_date,
                    end_date=end_date,
                    status=MembershipStatus.ACTIVE,
                    points_balance=0,
                )

                # Add membership to database
                db.create(new_membership)

                # Update customer tier to plus_member
                customer_profile.customer_tier = CustomerTier.PLUS_MEMBER
                db.update(customer_profile)

                return UpdateMembershipStatusOutput(
                    customer_id=request.customer_id,
                    membership_id=new_membership_id,
                    new_tier=CustomerTier.PLUS_MEMBER,
                    action_completed="upgraded",
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                )

            # Handle cancel action
            elif request.action == MembershipAction.CANCEL:
                # Find any membership (not just active) for this customer
                all_memberships = db.get_all(MembershipRecord)
                customer_membership = None
                for membership in all_memberships:
                    if membership.customer_id == request.customer_id:
                        customer_membership = membership
                        break

                if not customer_membership:
                    raise Tool.ExecutionError(
                        f"No membership record found for customer: {request.customer_id}"
                    )

                # Update membership status to cancelled
                customer_membership.status = MembershipStatus.CANCELLED
                db.update(customer_membership)

                # Revert customer tier to standard
                customer_profile.customer_tier = CustomerTier.STANDARD
                db.update(customer_profile)

                return UpdateMembershipStatusOutput(
                    customer_id=request.customer_id,
                    membership_id=None,
                    new_tier=CustomerTier.STANDARD,
                    action_completed="cancelled",
                    start_date=None,
                    end_date=None,
                )

            else:
                raise Tool.ExecutionError(f"Invalid action: {request.action}")

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to update membership status: {str(e)}"
            raise Tool.ExecutionError(error_message)
