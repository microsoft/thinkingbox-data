# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Software Catalog toolset."""

from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class PoolType(str, Enum):
    """Pool type enumeration."""

    STANDARD = "standard"
    ENTERPRISE = "enterprise"


class SoftwareCatalog(BaseModel):
    """Software catalog model."""

    table_name: ClassVar[str] = "software_catalog"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique catalog identifier (e.g., CAT-0012345)")
    name: str = Field(..., description="Software name")
    annual_cost: int = Field(..., description="Annual cost in dollars")
    pool_type: PoolType = Field(
        ..., description="License pool type (standard or enterprise)"
    )

    def get_id(self) -> str:
        """Return the ID of this catalog entry."""
        return self.id
