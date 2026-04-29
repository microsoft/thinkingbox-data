# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Jobber (Field Service Management) toolset."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InstallationServiceType(str, Enum):
    """Installation service type enumeration."""

    APPLIANCE_BASIC = "appliance_basic"
    APPLIANCE_ADVANCED = "appliance_advanced"
    TV_MOUNTING = "tv_mounting"


class InstallationJobStatus(str, Enum):
    """Installation job status enumeration."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ISSUE_REPORTED = "issue_reported"


class InstallationRescheduleReason(str, Enum):
    """Installation reschedule reason enumeration."""

    CUSTOMER_REQUEST = "customer_request"
    WORKMANSHIP_ISSUE = "workmanship_issue"
    TECHNICIAN_UNAVAILABLE = "technician_unavailable"
    WEATHER_DELAY = "weather_delay"


class InstallationCancellationReason(str, Enum):
    """Installation cancellation reason enumeration."""

    CUSTOMER_WANTS_SHIP_ONLY = "customer_wants_ship_only"
    CUSTOMER_CANCELLED_ORDER = "customer_cancelled_order"
    PRODUCT_INCOMPATIBLE = "product_incompatible"
    ADDRESS_INACCESSIBLE = "address_inaccessible"


class InstallationJob(BaseModel):
    """Installation job model from Jobber."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique installation job identifier")
    order_id: str = Field(..., description="Associated order identifier")
    customer_id: str = Field(..., description="Customer identifier")
    service_type: InstallationServiceType = Field(
        ..., description="Type of installation service"
    )
    scheduled_date: datetime = Field(
        ..., description="Scheduled appointment date and time"
    )
    technician_id: Optional[str] = Field(
        None, description="Assigned technician identifier"
    )
    status: InstallationJobStatus = Field(
        default=InstallationJobStatus.SCHEDULED, description="Current job status"
    )
    completion_date: Optional[datetime] = Field(
        None, description="Date when job was completed"
    )
    workmanship_warranty_end: Optional[datetime] = Field(
        None, description="End date of 90-day workmanship warranty"
    )
    service_cost: float = Field(..., description="Cost of installation service")

    def get_id(self) -> str:
        """Return the ID of this installation job."""
        return self.id
