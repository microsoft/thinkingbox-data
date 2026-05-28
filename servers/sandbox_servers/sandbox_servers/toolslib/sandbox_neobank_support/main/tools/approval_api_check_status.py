# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for checking approval request status."""

from typing import Any, Dict, Optional, Type

from sandbox_servers.toolslib.sandbox_neobank_support.main.models import (
    ApprovalRequest,
)
from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field


class CheckStatusInput(BaseModel):
    """Input for check_status tool."""

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, validate_assignment=True
    )

    approval_request_id: str = Field(
        ...,
        description="Unique identifier of the approval request",
        examples=["APR-00000001"],
    )


class CheckStatusOutput(BaseModel):
    """Output for check_status tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    status: str = Field(
        ..., description="Current status of the approval request", examples=["pending"]
    )
    decided_at: Optional[str] = Field(
        None,
        description="Timestamp of decision if completed",
        examples=["2025-12-17T11:30:00Z"],
    )
    approver_feedback: Optional[str] = Field(
        None,
        description="Feedback or notes from approver",
        examples=["Approved for 30-day access period"],
    )


class CheckStatusTool(Tool):
    """Tool implementation for checking approval request status."""

    @property
    def name(self) -> str:
        return "approval_api_check_status"

    @property
    def description(self) -> str:
        return (
            "Check the status of an approval request including approval/rejection decision and "
            "any feedback from the approver. Returns the current status (pending, approved, rejected, cancelled) "
            "along with decision timestamp and approver feedback if available. "
            "Use this to check if pending approval has been completed before proceeding with provisioning."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CheckStatusInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CheckStatusOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return CheckStatusInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CheckStatusOutput

    async def run(
        self, db: InMemoryDatabase, request: CheckStatusInput
    ) -> CheckStatusOutput:
        """Check the status of an approval request."""
        try:
            # Get all approval requests
            all_requests = db.get_all(ApprovalRequest)

            # Find matching request by ID
            matching_request = None
            for req in all_requests:
                if req.id == request.approval_request_id:
                    matching_request = req
                    break

            # If no request found, raise 404 error
            if not matching_request:
                raise Tool.ExecutionError(
                    f"Approval request not found: {request.approval_request_id}"
                )

            # Prepare decided_at timestamp if available
            decided_at = None
            if matching_request.decided_at:
                decided_at = matching_request.decided_at.strftime("%Y-%m-%dT%H:%M:%SZ")

            # Return status information
            return CheckStatusOutput(
                status=matching_request.status.value,
                decided_at=decided_at,
                approver_feedback=matching_request.approver_feedback,
            )

        except Tool.ExecutionError:
            raise
        except Exception as e:
            error_message = f"Failed to check approval status: {str(e)}"
            raise Tool.ExecutionError(error_message)
