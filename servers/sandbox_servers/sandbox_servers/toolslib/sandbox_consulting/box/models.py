# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Box Document Management toolset."""

from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field


class ConfidentialityLevel(str, Enum):
    """Confidentiality level enumeration."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    CLIENT_CONFIDENTIAL = "client_confidential"


class PermissionLevel(str, Enum):
    """Permission level enumeration."""

    VIEWER = "viewer"
    EDITOR = "editor"
    CO_OWNER = "co_owner"


class Folder(BaseModel):
    """Folder model."""

    table_name: ClassVar[str] = "folders"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique folder identifier")
    folder_name: str = Field(..., description="Folder name")
    confidentiality_level: ConfidentialityLevel = Field(
        ..., description="Confidentiality level of the folder"
    )
    owner_email: str = Field(..., description="Folder owner email address")
    client_id: Optional[str] = Field(None, description="Client ID if client folder")
    engagement_code: Optional[str] = Field(
        None, description="Engagement code if engagement-specific"
    )

    def get_id(self) -> str:
        """Return unique identifier for this folder."""
        return self.id


class FolderAccessLog(BaseModel):
    """Folder access log model."""

    table_name: ClassVar[str] = "folder_access_logs"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique access log identifier")
    folder_id: str = Field(..., description="Folder ID")
    employee_email: str = Field(..., description="Employee email address")
    permission_level: PermissionLevel = Field(
        ..., description="Permission level granted"
    )

    def get_id(self) -> str:
        """Return unique identifier for this access log."""
        return self.id
