# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for approval_get_status."""

from typing import Any, Dict, List, Optional, Type

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.approval.models import (
    ApprovalRequest,
    RequestType,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    get_schema_without_refs,
)
from pydantic import BaseModel, ConfigDict, Field


class ApprovalGetStatusInput(BaseModel):
    """Input for approval_get_status tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    request_type: RequestType = Field(
        ...,
        description="Type of request to filter by",
        examples=["software_access"],
    )
    requester_email: str = Field(
        ...,
        description="Requester email address to filter by",
        examples=["user@msg.com"],
    )
    engagement_code: Optional[str] = Field(
        None,
        description="Engagement code to filter by (optional)",
        examples=["ENG-0012345"],
    )
    approver_email: Optional[str] = Field(
        None,
        description="Approver email address to filter by (optional)",
        examples=["manager@msg.com"],
    )


class ApprovalStatusResult(BaseModel):
    """Individual approval status result."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    approval_id: str = Field(..., description="Unique approval request ID")
    status: str = Field(
        ...,
        description="Current status of the approval request (pending/approved/rejected)",
    )
    request_type: str = Field(..., description="Type of the request")
    approver_email: str = Field(..., description="Approver email address")
    engagement_code: Optional[str] = Field(
        None, description="Engagement code if applicable"
    )


class ApprovalGetStatusOutput(BaseModel):
    """Output for approval_get_status tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    results: List[ApprovalStatusResult] = Field(
        default_factory=list,
        description="List of matching approval requests with their statuses",
    )


class ApprovalGetStatusTool(Tool):
    """Tool implementation for retrieving approval request status."""

    @property
    def name(self) -> str:
        return "get_status"

    @property
    def description(self) -> str:
        return (
            "Retrieve approval request status. Use this tool to check approval status before "
            "proceeding with provisioning steps (license allocation, access provisioning, etc.). "
            "Searches for approval requests matching the specified criteria and returns their "
            "current status (pending, approved, or rejected). Required parameters are request_type "
            "and requester_email. Optionally filter by engagement_code and/or approver_email."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(ApprovalGetStatusInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(ApprovalGetStatusOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return ApprovalGetStatusInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ApprovalGetStatusOutput

    async def run(
        self, db: InMemoryDatabase, request: ApprovalGetStatusInput
    ) -> ApprovalGetStatusOutput:
        """Retrieve approval request status based on filter criteria."""
        try:
            # Get all approval requests
            all_approvals = db.get_all(ApprovalRequest)

            # Filter by required fields
            filtered_approvals = [
                approval
                for approval in all_approvals
                if approval.request_type.value == request.request_type
                and approval.requester_email == request.requester_email
            ]

            # Apply optional filters
            if request.engagement_code is not None:
                filtered_approvals = [
                    approval
                    for approval in filtered_approvals
                    if approval.engagement_code == request.engagement_code
                ]

            if request.approver_email is not None:
                filtered_approvals = [
                    approval
                    for approval in filtered_approvals
                    if approval.approver_email == request.approver_email
                ]

            # Build results
            if filtered_approvals:
                results = [
                    ApprovalStatusResult(
                        approval_id=approval.id,
                        status=approval.status.value,
                        request_type=approval.request_type.value,
                        approver_email=approval.approver_email,
                        engagement_code=approval.engagement_code,
                    )
                    for approval in filtered_approvals
                ]
            else:
                # Return dummy result when no approvals found
                results = [
                    ApprovalStatusResult(
                        approval_id="NOT_FOUND",
                        status="not_found",
                        request_type=request.request_type,
                        approver_email=request.approver_email or "",
                        engagement_code=request.engagement_code,
                    )
                ]

            return ApprovalGetStatusOutput(results=results)

        except Tool.ExecutionError:
            raise
        except Exception as e:
            error_message = f"Failed to retrieve approval status: {str(e)}"
            raise Tool.ExecutionError(error_message)
