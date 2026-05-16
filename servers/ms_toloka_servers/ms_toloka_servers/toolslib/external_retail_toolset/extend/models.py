# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Extend Warranty Provider toolset."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WarrantyType(str, Enum):
    """Warranty type enumeration."""

    manufacturer = "manufacturer"
    extended_warranty = "extended_warranty"
    protection_plan = "protection_plan"


class WarrantyClaimStatus(str, Enum):
    """Warranty claim status enumeration."""

    pending = "pending"
    approved = "approved"
    in_progress = "in_progress"
    completed = "completed"
    denied = "denied"


class WarrantyIssueType(str, Enum):
    """Warranty issue type enumeration."""

    product_not_functioning = "product_not_functioning"
    component_failed = "component_failed"
    performance_degradation = "performance_degradation"
    accidental_damage = "accidental_damage"


class WarrantyContract(BaseModel):
    """Warranty contract model from Extend."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Warranty contract identifier")
    order_id: str = Field(..., description="Order identifier")
    sku: str = Field(..., description="Product SKU")
    customer_id: str = Field(..., description="Customer identifier")
    warranty_type: WarrantyType = Field(..., description="Type of warranty")
    start_date: datetime = Field(..., description="Warranty start date")
    end_date: datetime = Field(..., description="Warranty end date")
    coverage_details: str = Field(..., description="Coverage details description")

    def get_id(self) -> str:
        """Return the contract ID."""
        return self.id


class WarrantyClaim(BaseModel):
    """Warranty claim model from Extend."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Warranty claim identifier")
    contract_id: str = Field(..., description="Warranty contract identifier")
    customer_id: str = Field(..., description="Customer identifier")
    claim_date: datetime = Field(..., description="Claim submission date")
    issue_description: str = Field(..., description="Issue description")
    status: WarrantyClaimStatus = Field(..., description="Claim status")
    resolution: Optional[str] = Field(None, description="Claim resolution details")

    def get_id(self) -> str:
        """Return the claim ID."""
        return self.id
