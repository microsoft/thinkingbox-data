# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Salesforce CRM toolset."""

from datetime import datetime
from enum import Enum
from typing import ClassVar, List, Optional

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.client_access.models import (
    ClearanceLevel,
)
from pydantic import BaseModel, ConfigDict, Field


class EngagementStatus(str, Enum):
    """Engagement status enumeration."""

    PIPELINE = "pipeline"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AssignmentStatus(str, Enum):
    """Assignment status enumeration."""

    ACTIVE = "active"
    BOOKED = "booked"


class SfEngagement(BaseModel):
    """Salesforce engagement model."""

    table_name: ClassVar[str] = "sf_engagements"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    engagement_code: str = Field(
        ..., description="Unique engagement identifier (e.g., ENG-0012345)"
    )
    client_id: str = Field(..., description="Client identifier (e.g., CLT-0012345)")
    engagement_manager_email: str = Field(
        ..., description="Engagement manager email address"
    )
    status: EngagementStatus = Field(..., description="Engagement status")
    start_date: datetime = Field(..., description="Engagement start date")
    end_date: Optional[datetime] = Field(None, description="Engagement end date")

    def get_id(self) -> str:
        """Return the engagement code as ID."""
        return self.engagement_code


class Client(BaseModel):
    """Client model from Salesforce."""

    table_name: ClassVar[str] = "clients"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique client identifier (e.g., CLT-0012345)")
    name: str = Field(..., description="Client name")
    requires_nda: bool = Field(True, description="Whether NDA is required")
    clearance_level: ClearanceLevel = Field(
        ClearanceLevel.STANDARD, description="Required clearance level"
    )
    required_training_courses: List[str] = Field(
        default_factory=list, description="Array of required training course IDs"
    )

    def get_id(self) -> str:
        """Return the client ID."""
        return self.id
