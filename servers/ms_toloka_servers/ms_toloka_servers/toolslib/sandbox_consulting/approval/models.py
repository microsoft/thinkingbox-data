# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Approval Workflow System toolset."""

from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field


class RequestType(str, Enum):
    """Request type enumeration."""

    SOFTWARE_ACCESS = "software_access"
    HARDWARE_REPLACEMENT = "hardware_replacement"
    CLIENT_ACCESS = "client_access"
    TRAINING_ENGAGEMENT_COORDINATION = "training_engagement_coordination"
    TRAINING_COST = "training_cost"
    EXPENSE_OVERRIDE = "expense_override"
    TRAVEL = "travel"
    DOCUMENT_ACCESS = "document_access"


class ApprovalRequestStatus(str, Enum):
    """Approval request status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_FOUND = "not_found"


class ApprovalRequest(BaseModel):
    """Approval request model."""

    table_name: ClassVar[str] = "approval_requests"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(
        ..., description="Unique approval request identifier (e.g., APR-0012345)"
    )
    request_type: RequestType = Field(..., description="Type of request")
    requester_email: str = Field(..., description="Requester email address")
    approver_email: str = Field(..., description="Approver email address")
    amount: Optional[int] = Field(
        None, description="Amount in USD (for cost-related requests)"
    )
    engagement_code: Optional[str] = Field(
        None, description="Engagement code (when applicable)"
    )
    status: ApprovalRequestStatus = Field(
        default=ApprovalRequestStatus.PENDING,
        description="Current status of the approval request",
    )

    def get_id(self) -> str:
        """Return the approval request ID."""
        return self.id
