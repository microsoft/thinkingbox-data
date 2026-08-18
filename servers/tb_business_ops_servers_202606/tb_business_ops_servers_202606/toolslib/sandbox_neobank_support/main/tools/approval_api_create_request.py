# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for creating approval requests."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type

from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
    ApprovalRequest,
    ApprovalRequestStatus,
    ApprovalRequestType,
    ApprovalUrgency,
    Employee,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    get_schema_without_refs,
)
from pydantic import BaseModel, ConfigDict, Field

# Fixed timestamp for deterministic behavior
FIXED_CURRENT_TIME = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)


class CreateRequestInput(BaseModel):
    """Input for create_request tool."""

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, validate_assignment=True
    )

    request_type: ApprovalRequestType = Field(
        ...,
        description="Type of approval request",
        examples=["access_request"],
    )
    requester_email: str = Field(
        ...,
        description="Email of the employee requesting approval",
        examples=["john.smith@vdb.com"],
    )
    approver_email: str = Field(
        ...,
        description="Email of the designated approver",
        examples=["sarah.jones@vdb.com"],
    )
    details: str = Field(
        ...,
        description="Details of what is being requested",
        examples=["Requesting Snowflake read-only access for Q4 reporting project"],
    )
    urgency: Optional[ApprovalUrgency] = Field(
        None,
        description="Urgency level of the request",
        examples=["standard"],
    )
    ticket_id: Optional[str] = Field(
        None,
        description="Associated ticket ID for tracking",
        examples=["TCK-00012345"],
    )


class CreateRequestOutput(BaseModel):
    """Output for create_request tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    approval_request_id: str = Field(
        ...,
        description="Unique identifier for the approval request",
        examples=["APR-00000001"],
    )
    status: str = Field(
        ..., description="Initial status of the request", examples=["pending"]
    )


class CreateRequestTool(Tool):
    """Tool implementation for creating approval requests."""

    @property
    def name(self) -> str:
        return "approval_api_create_request"

    @property
    def description(self) -> str:
        return (
            "Create a multi-level approval request in the workflow system and notify the designated approver. "
            "Used for access requests, hardware purchases, data exports, and policy exceptions. "
            "The system will automatically notify the approver and track the request status. "
            "Use approver_lookup_api tools to determine the correct approver before creating the request."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CreateRequestInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CreateRequestOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return CreateRequestInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CreateRequestOutput

    async def run(
        self, db: InMemoryDatabase, request: CreateRequestInput
    ) -> CreateRequestOutput:
        """Create an approval request."""
        try:
            # Look up requester by email
            all_employees = db.get_all(Employee)
            requester = None
            for emp in all_employees:
                if emp.email == request.requester_email:
                    requester = emp
                    break

            if not requester:
                raise Tool.ExecutionError(
                    f"Requester not found: {request.requester_email}"
                )

            # Look up approver by email
            approver = None
            for emp in all_employees:
                if emp.email == request.approver_email:
                    approver = emp
                    break

            if not approver:
                raise Tool.ExecutionError(
                    f"Approver not found: {request.approver_email}"
                )

            # Get all existing approval requests to generate new ID
            all_requests = db.get_all(ApprovalRequest)
            next_id = len(all_requests) + 1
            new_id = f"APR-{next_id:08d}"

            # Set default urgency if not provided
            urgency = request.urgency if request.urgency else ApprovalUrgency.STANDARD

            # Create new approval request (created_at is now optional)
            new_request = ApprovalRequest(
                id=new_id,
                request_type=request.request_type,
                requester_id=requester.id,
                approver_id=approver.id,
                status=ApprovalRequestStatus.PENDING,
                urgency=urgency,
                details=request.details,
                ticket_id=request.ticket_id,
                created_at=None,
                decided_at=None,
                approver_feedback=None,
            )

            # Save to database
            db.create(new_request)

            # Return response
            return CreateRequestOutput(
                approval_request_id=new_request.id,
                status=new_request.status.value,
            )

        except Tool.ExecutionError:
            raise
        except Exception as e:
            error_message = f"Failed to create approval request: {str(e)}"
            raise Tool.ExecutionError(error_message)
