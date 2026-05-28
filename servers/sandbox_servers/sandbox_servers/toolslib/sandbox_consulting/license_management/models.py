# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for License Management Platform toolset."""

from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field


class LicensePool(str, Enum):
    """License pool type enumeration."""

    STANDARD = "standard"
    ENTERPRISE = "enterprise"


class LicensePoolRecord(BaseModel):
    """License pool record model."""

    table_name: ClassVar[str] = "license_pool_record"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    catalog_id: str = Field(..., description="Software catalog ID")
    pool_type: LicensePool = Field(
        ..., description="License pool type (standard or enterprise)"
    )
    total_licenses: Optional[int] = Field(
        None,
        description="Total licenses available (null means unlimited capacity for enterprise pools)",
    )

    def get_id(self) -> str:
        """Return composite key of catalog_id and pool_type."""
        return f"{self.catalog_id}_{self.pool_type.value}"


class LicenseAllocation(BaseModel):
    """License allocation model."""

    table_name: ClassVar[str] = "license_allocation"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique allocation identifier")
    catalog_id: str = Field(..., description="Software catalog ID")
    employee_email: str = Field(..., description="Employee email address")
    engagement_code: Optional[str] = Field(
        None, description="Engagement code (optional)"
    )
    pool_type: LicensePool = Field(..., description="License pool type")
    deallocated_at: Optional[datetime] = Field(
        None, description="Deallocation timestamp (null means active allocation)"
    )

    def get_id(self) -> str:
        """Return the allocation ID."""
        return self.id
