# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for IT Asset Management toolset."""

from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field


class DeviceType(str, Enum):
    """Device type enumeration."""

    LAPTOP = "laptop"
    PHONE = "phone"
    MONITOR = "monitor"
    DOCKING_STATION = "docking_station"
    HEADSET = "headset"
    PERIPHERAL = "peripheral"


class InventoryStatus(str, Enum):
    """Inventory status enumeration."""

    AVAILABLE = "available"
    RESERVED = "reserved"
    ASSIGNED = "assigned"
    RETIRED = "retired"
    IN_REPAIR = "in_repair"


class OfficeLocation(str, Enum):
    """Office location enumeration."""

    NEW_YORK = "New York"
    SAN_FRANCISCO = "San Francisco"
    CHICAGO = "Chicago"
    AUSTIN = "Austin"


class Device(BaseModel):
    """Device model."""

    table_name: ClassVar[str] = "devices"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique asset identifier (e.g., MSG00012345)")
    device_type: DeviceType = Field(..., description="Device type")
    model: str = Field(..., description="Device model")
    age_months: int = Field(..., description="Device age in months")
    inventory_status: InventoryStatus = Field(..., description="Inventory status")
    location: OfficeLocation = Field(..., description="Office location")

    def get_id(self) -> str:
        """Return the device asset ID."""
        return self.id


class DeviceAssignment(BaseModel):
    """Device assignment model."""

    table_name: ClassVar[str] = "device_assignments"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique assignment identifier")
    asset_id: str = Field(..., description="Device asset ID")
    employee_email: str = Field(..., description="Employee email address")
    returned_at: Optional[datetime] = Field(
        None, description="Date when device was returned"
    )

    def get_id(self) -> str:
        """Return the assignment ID."""
        return self.id
