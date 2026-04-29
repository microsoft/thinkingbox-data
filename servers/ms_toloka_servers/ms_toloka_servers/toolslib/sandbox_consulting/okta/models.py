# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Okta Identity Management toolset."""

from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field


class AccessType(str, Enum):
    """Access type enumeration."""

    FULL_ACCESS = "full_access"
    READ_ONLY = "read_only"
    CONTRIBUTOR = "contributor"
    ADMIN = "admin"


class ApplicationAccessLog(BaseModel):
    """Application access log model."""

    table_name: ClassVar[str] = "application_access_logs"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique access log identifier")
    employee_email: str = Field(..., description="Employee email address")
    app_name: str = Field(..., description="Application name")
    access_type: Optional[AccessType] = Field(
        None, description="Access type (full_access, read_only, contributor, admin)"
    )

    def get_id(self) -> str:
        """Return the ID of this access log entry."""
        return self.id
