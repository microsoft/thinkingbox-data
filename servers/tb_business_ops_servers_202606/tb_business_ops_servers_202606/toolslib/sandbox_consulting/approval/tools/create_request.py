# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for approval_create_request."""

from typing import Any, Dict, Optional, Type

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.approval.models import (
    ApprovalRequest,
    ApprovalRequestStatus,
    RequestType,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    get_schema_without_refs,
)
from pydantic import BaseModel, ConfigDict, Field


class ApprovalCreateRequestInput(BaseModel):
    """Input for approval_create_request tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    request_type: RequestType = Field(
        ..., description="Type of request", examples=["software_access"]
    )
    requester_email: str = Field(
        ..., description="Requester email address", examples=["user@msg.com"]
    )
    approver_email: str = Field(
        ..., description="Approver email address", examples=["manager@msg.com"]
    )
    amount: Optional[int] = Field(
        None, description="Amount in USD (optional)", examples=[500]
    )
    engagement_code: Optional[str] = Field(
        None, description="Engagement code (optional)", examples=["ENG-0012345"]
    )


class ApprovalCreateRequestOutput(BaseModel):
    """Output for approval_create_request tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    approval_id: str = Field(..., description="Unique ID of created approval request")


class ApprovalCreateRequestTool(Tool):
    """Tool implementation for creating approval requests."""

    @property
    def name(self) -> str:
        return "create_request"

    @property
    def description(self) -> str:
        return (
            "Create approval request in workflow system. Creates a new approval request that "
            "routes to designated approvers for software access, hardware, training, client access, "
            "and other request types. Generates approval record in the workflow system. Create "
            "approval requests after determining required approvers based on policy rules. Always "
            "include engagement_code when applicable."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(ApprovalCreateRequestInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(ApprovalCreateRequestOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return ApprovalCreateRequestInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ApprovalCreateRequestOutput

    async def run(
        self, db: InMemoryDatabase, request: ApprovalCreateRequestInput
    ) -> ApprovalCreateRequestOutput:
        """Create an approval request."""
        try:
            # Generate sequential approval ID
            existing_approvals = db.get_all(ApprovalRequest)
            PREFIX_FOR_NEW_IDS = "APR-2"
            count = 0
            existing_ids = {approval.id for approval in existing_approvals}

            while True:
                new_id = f"{PREFIX_FOR_NEW_IDS}-{count:06d}"
                if new_id not in existing_ids:
                    break
                count += 1

            # Create approval request with status=pending
            new_approval = ApprovalRequest(
                id=new_id,
                request_type=request.request_type,
                requester_email=request.requester_email,
                approver_email=request.approver_email,
                amount=request.amount,
                engagement_code=request.engagement_code,
                status=ApprovalRequestStatus.PENDING,
            )
            db.create(new_approval)

            return ApprovalCreateRequestOutput(approval_id=new_id)

        except Tool.ExecutionError:
            raise
        except Exception as e:
            error_message = f"Failed to create approval request: {str(e)}"
            raise Tool.ExecutionError(error_message)
