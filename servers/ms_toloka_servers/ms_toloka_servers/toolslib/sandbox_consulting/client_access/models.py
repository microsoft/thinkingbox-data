# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Client Access Management toolset."""

from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field


class AccessType(str, Enum):
    """Access type enumeration."""

    FULL_ACCESS = "full_access"
    READ_ONLY = "read_only"
    CONTRIBUTOR = "contributor"
    ADMIN = "admin"


class ClearanceLevel(str, Enum):
    """Clearance level enumeration."""

    STANDARD = "standard"
    HIGH_SECURITY = "high_security"


class ClearanceStatus(str, Enum):
    """Clearance status enumeration."""

    NOT_INITIATED = "not_initiated"
    IN_PROGRESS = "in_progress"
    CLEARED = "cleared"
    FAILED = "failed"
    EXPIRED = "expired"


class NdaStatus(str, Enum):
    """NDA status enumeration."""

    NOT_SIGNED = "not_signed"
    SENT_FOR_SIGNATURE = "sent_for_signature"
    SIGNED = "signed"
    EXPIRED = "expired"


class VpnAccess(BaseModel):
    """VPN access record model."""

    table_name: ClassVar[str] = "vpn_access"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique VPN access identifier")
    employee_email: str = Field(..., description="Employee email address")
    client_id: Optional[str] = Field(
        None, description="Client ID for client-specific VPN"
    )
    revoked_at: Optional[datetime] = Field(
        None, description="Date when VPN access was revoked"
    )

    def get_id(self) -> str:
        """Return the VPN access ID."""
        return self.id


class ClientSystemAccess(BaseModel):
    """Client system access record model."""

    table_name: ClassVar[str] = "client_system_access"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique access identifier")
    employee_email: str = Field(..., description="Employee email address")
    client_id: str = Field(..., description="Client ID")
    system_name: str = Field(..., description="System or application name")
    access_type: AccessType = Field(..., description="Type of access granted")
    revoked_at: Optional[datetime] = Field(
        None, description="Date when access was revoked"
    )

    def get_id(self) -> str:
        """Return the access ID."""
        return self.id


class ClearanceRecord(BaseModel):
    """Clearance record from background check system."""

    table_name: ClassVar[str] = "clearance_record"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    employee_email: str = Field(..., description="Employee email address (primary key)")
    clearance_level: ClearanceLevel = Field(
        ..., description="Clearance level (standard or high_security)"
    )
    status: ClearanceStatus = Field(..., description="Clearance status")

    def get_id(self) -> str:
        """Return the employee email as ID."""
        return self.employee_email


class NdaRecord(BaseModel):
    """NDA record from NDA management system."""

    table_name: ClassVar[str] = "nda_record"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    employee_email: str = Field(
        ..., description="Employee email address (part of composite key)"
    )
    client_id: str = Field(..., description="Client ID (part of composite key)")
    status: NdaStatus = Field(..., description="NDA status")

    def get_id(self) -> str:
        """Return composite key as ID."""
        return f"{self.employee_email}:{self.client_id}"
