# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Check license availability tool."""

from typing import Optional, Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import LicenseAllocation, LicenseType, SoftwareLicense


class LicenseCheckAvailabilityInput(BaseModel):
    """Input model for license_management_api_check_availability tool."""

    software_name: str = Field(
        ..., description="Software product name", examples=["Tableau"]
    )


class LicenseCheckAvailabilityOutput(BaseModel):
    """Output model for license_management_api_check_availability tool."""

    model_config = ConfigDict(extra="forbid")

    available_licenses: Optional[int] = Field(
        None, description="Number of available licenses. Null for unlimited pools"
    )
    total_licenses: Optional[int] = Field(
        None, description="Total licenses in pool. Null for unlimited pools"
    )
    license_type: LicenseType = Field(..., description="Type of license pool")


class LicenseCheckAvailabilityTool(Tool):
    """Tool for checking available license count for a software product."""

    @property
    def name(self) -> str:
        return "license_management_api_check_availability"

    @property
    def description(self) -> str:
        return (
            "Returns the number of available licenses for a software product. For unlimited pools, returns null. "
            "For limited pools, calculates available count from total minus allocated."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return LicenseCheckAvailabilityInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return LicenseCheckAvailabilityOutput

    async def run(
        self, db: InMemoryDatabase, request: LicenseCheckAvailabilityInput
    ) -> LicenseCheckAvailabilityOutput:
        """Check license availability for a software product."""
        # Get all software licenses
        all_licenses = db.get_all(SoftwareLicense)

        # Find license by software name (case-insensitive match)
        matching_licenses = [
            lic
            for lic in all_licenses
            if lic.software_name.lower() == request.software_name.lower()
        ]

        if not matching_licenses:
            raise Tool.ExecutionError(
                f"Software not found in license inventory: {request.software_name}"
            )

        license_pool = matching_licenses[0]

        # For unlimited pools, return null for counts
        if license_pool.license_type == LicenseType.UNLIMITED:
            return LicenseCheckAvailabilityOutput(
                available_licenses=None,
                total_licenses=None,
                license_type=license_pool.license_type,
            )

        # For limited pools, count active allocations
        all_allocations = db.get_all(LicenseAllocation)
        active_allocations = [
            alloc
            for alloc in all_allocations
            if alloc.license_id == license_pool.id and alloc.is_active
        ]

        allocated_count = len(active_allocations)
        total_licenses = license_pool.total_licenses or 0
        available_licenses = max(0, total_licenses - allocated_count)

        return LicenseCheckAvailabilityOutput(
            available_licenses=available_licenses,
            total_licenses=total_licenses,
            license_type=license_pool.license_type,
        )
