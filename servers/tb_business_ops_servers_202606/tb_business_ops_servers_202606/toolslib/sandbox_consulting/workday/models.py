# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Workday HCM toolset."""

from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field


class EmployeeLevel(str, Enum):
    """Employee level enumeration."""

    ANALYST = "Analyst"
    CONSULTANT = "Consultant"
    SENIOR_CONSULTANT = "Senior Consultant"
    MANAGER = "Manager"
    SENIOR_MANAGER = "Senior Manager"
    PARTNER = "Partner"
    ADMINISTRATIVE = "Administrative"


class OfficeLocation(str, Enum):
    """Office location enumeration."""

    NEW_YORK = "New York"
    SAN_FRANCISCO = "San Francisco"
    CHICAGO = "Chicago"
    AUSTIN = "Austin"


class OnboardingPhase(str, Enum):
    """Onboarding phase enumeration."""

    DAY_0_1_IMMEDIATE = "day_0_1_immediate"
    DAY_1_3_INITIAL = "day_1_3_initial"
    DAY_3_7_PROVISIONING = "day_3_7_provisioning"
    DAY_7_30_ENGAGEMENT_RAMP = "day_7_30_engagement_ramp"
    COMPLETED = "completed"


class ApproverAvailability(str, Enum):
    """Approver availability status enumeration."""

    AVAILABLE = "available"
    ON_LEAVE = "on_leave"


class Employee(BaseModel):
    """Employee model from Workday HCM."""

    table_name: ClassVar[str] = "employees"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    email: str = Field(..., description="Employee email address (primary key)")
    name: str = Field(..., description="Employee full name")
    level: EmployeeLevel = Field(..., description="Employee level")
    office_location: OfficeLocation = Field(..., description="Office location")
    start_date: datetime = Field(..., description="Employment start date")
    manager_email: Optional[str] = Field(None, description="Manager email address")
    partner_email: Optional[str] = Field(None, description="Partner email address")
    onboarding_phase: Optional[OnboardingPhase] = Field(
        None, description="Onboarding phase"
    )
    availability_status: ApproverAvailability = Field(
        ApproverAvailability.AVAILABLE, description="Availability status for approvals"
    )
    backup_approver_email: Optional[str] = Field(
        None, description="Backup approver email address"
    )

    def get_id(self) -> str:
        """Return the email as ID."""
        return self.email
