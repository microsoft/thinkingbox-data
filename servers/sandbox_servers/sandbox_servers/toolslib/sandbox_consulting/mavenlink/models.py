# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Mavenlink Resource Management toolset."""

from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional

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


class MvEngagement(BaseModel):
    """Mavenlink engagement model."""

    table_name: ClassVar[str] = "mv_engagements"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    engagement_code: str = Field(
        ..., description="Unique engagement identifier (e.g., ENG-0012345)"
    )
    status: EngagementStatus = Field(..., description="Engagement status")
    start_date: datetime = Field(..., description="Engagement start date")
    end_date: Optional[datetime] = Field(None, description="Engagement end date")
    senior_manager_email: str = Field(..., description="Senior manager email address")

    def get_id(self) -> str:
        """Return the engagement code as ID."""
        return self.engagement_code


class EmployeeAssignment(BaseModel):
    """Employee assignment model from Mavenlink."""

    table_name: ClassVar[str] = "employee_assignments"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique assignment identifier")
    employee_email: str = Field(..., description="Employee email address")
    engagement_code: str = Field(..., description="Engagement code")
    assignment_status: AssignmentStatus = Field(..., description="Assignment status")
    start_date: datetime = Field(..., description="Assignment start date")
    end_date: Optional[datetime] = Field(None, description="Assignment end date")
    senior_manager_email: str = Field(..., description="Senior manager email address")

    def get_id(self) -> str:
        """Return the assignment ID."""
        return self.id
