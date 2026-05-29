# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Allocate software license tool."""

from datetime import datetime, timezone
from typing import Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Employee, LicenseAllocation, LicenseType, SoftwareLicense

# Fixed current time for deterministic behavior
FIXED_CURRENT_TIME = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)


class LicenseAllocateInput(BaseModel):
    """Input model for license_management_api_allocate_license tool."""

    software_name: str = Field(
        ..., description="Software product name", examples=["Tableau"]
    )
    email: str = Field(
        ..., description="Corporate email address", examples=["john.smith@vdb.com"]
    )


class LicenseAllocateOutput(BaseModel):
    """Output model for license_management_api_allocate_license tool."""

    model_config = ConfigDict(extra="forbid")

    allocation_id: str = Field(
        ..., description="Unique identifier for the allocation (format: LAL-########)"
    )


class LicenseAllocateTool(Tool):
    """Tool for allocating a software license to an employee."""

    @property
    def name(self) -> str:
        return "license_management_api_allocate_license"

    @property
    def description(self) -> str:
        return (
            "Allocates a license from the pool to a specific employee. For limited pools, decrements available count. "
            "Creates allocation record for tracking."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return LicenseAllocateInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return LicenseAllocateOutput

    async def run(
        self, db: InMemoryDatabase, request: LicenseAllocateInput
    ) -> LicenseAllocateOutput:
        """Allocate a license to an employee."""
        # Get employee by email
        all_employees = db.get_all(Employee)
        employees = [e for e in all_employees if e.email == request.email]

        if not employees:
            raise Tool.ExecutionError(f"Employee not found: {request.email}")

        employee = employees[0]

        # Get all software licenses
        all_licenses = db.get_all(SoftwareLicense)

        # Find license by software name (case-insensitive match)
        matching_licenses = [
            lic
            for lic in all_licenses
            if lic.software_name.lower() == request.software_name.lower()
        ]

        if not matching_licenses:
            raise Tool.ExecutionError(f"Software not found: {request.software_name}")

        license_pool = matching_licenses[0]

        # Check if employee already has an active allocation
        all_allocations = db.get_all(LicenseAllocation)
        existing_allocations = [
            alloc
            for alloc in all_allocations
            if alloc.license_id == license_pool.id
            and alloc.employee_id == employee.id
            and alloc.is_active
        ]

        if existing_allocations:
            raise Tool.ExecutionError(
                f"Employee already has a license for this software: {request.software_name}"
            )

        # For limited pools, check availability
        if license_pool.license_type != LicenseType.UNLIMITED:
            active_allocations = [
                alloc
                for alloc in all_allocations
                if alloc.license_id == license_pool.id and alloc.is_active
            ]

            allocated_count = len(active_allocations)
            total_licenses = license_pool.total_licenses or 0

            if allocated_count >= total_licenses:
                raise Tool.ExecutionError("No licenses available in pool")

        # Generate new allocation ID
        allocation_count = len(all_allocations)
        new_allocation_id = f"LAL-{allocation_count + 1:08d}"

        # Create new allocation record (allocated_at is now optional, set by caller if needed)
        new_allocation = LicenseAllocation(
            id=new_allocation_id,
            license_id=license_pool.id,
            employee_id=employee.id,
            allocated_at=None,
            allocated_by="system",
            is_active=True,
        )

        # Save to database
        db.create(new_allocation)

        return LicenseAllocateOutput(allocation_id=new_allocation_id)
