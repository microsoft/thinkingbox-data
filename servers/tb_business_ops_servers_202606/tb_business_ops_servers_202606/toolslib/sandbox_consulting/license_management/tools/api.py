# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for License Management Platform API (master tool)."""

from enum import Enum
from typing import Any, Dict, Optional, Type

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.license_management.models import (
    LicenseAllocation,
    LicensePool,
    LicensePoolRecord,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.software_catalog.models import (
    SoftwareCatalog,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    get_schema_without_refs,
)
from pydantic import BaseModel, ConfigDict, Field


class LicenseManagementAction(str, Enum):
    """License Management API action enumeration."""

    CHECK_AVAILABILITY = "check_availability"
    ALLOCATE = "allocate"
    GET_COST = "get_cost"


class LicenseManagementApiInput(BaseModel):
    """Input for license_management_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    action: LicenseManagementAction = Field(
        ...,
        description="Action to perform",
        examples=["check_availability"],
    )
    catalog_id: Optional[str] = Field(
        None,
        description="Software catalog ID (required for check_availability, allocate, get_cost)",
        examples=["CAT-0012345"],
    )
    pool_type: Optional[LicensePool] = Field(
        None,
        description="License pool type (required for check_availability, allocate)",
        examples=["standard"],
    )
    email: Optional[str] = Field(
        None,
        description="Employee email address (required for allocate)",
        examples=["user@msg.com"],
    )
    engagement_code: Optional[str] = Field(
        None,
        description="Engagement code (optional for allocate)",
        examples=["ENG-0012345"],
    )


class LicenseManagementApiOutput(BaseModel):
    """Output for license_management_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    available_count: Optional[int] = Field(
        None,
        description="Number of available licenses (for action=check_availability). Returns 99999 for enterprise pools with unlimited capacity.",
    )
    success: Optional[bool] = Field(
        None,
        description="Indicates if allocation was successful (for action=allocate)",
    )
    annual_cost: Optional[int] = Field(
        None,
        description="Annual cost of the license (for action=get_cost)",
    )


class LicenseManagementApiTool(Tool):
    """Master tool implementation for License Management Platform API."""

    @property
    def name(self) -> str:
        return "api"

    @property
    def description(self) -> str:
        return (
            "Manage software licenses and allocations. Checks license availability, allocates "
            "licenses to employees, and retrieves license costs. Use action parameter to specify "
            "the operation:\n\n"
            "- action='check_availability': Checks available license count for a specific software "
            "and pool type. REQUIRES: catalog_id, pool_type. Returns available_count integer. "
            "Enterprise pools with unlimited capacity return 99999 available licenses.\n\n"
            "- action='allocate': Allocates a license to an employee for a specific engagement. "
            "REQUIRES: catalog_id, email, pool_type. OPTIONAL: engagement_code. Returns success "
            "boolean. Creates record in license_allocations table.\n\n"
            "- action='get_cost': Retrieves annual cost of a software license for approval threshold "
            "calculations. REQUIRES: catalog_id. Returns annual_cost integer from software_catalog "
            "table.\n\n"
            "Agent must first call software_catalog_get_details to retrieve pool_type before calling "
            "check_availability or allocate. Always check availability before allocating. Use get_cost "
            "to determine approval thresholds based on software annual cost. Enterprise pools with "
            "unlimited capacity return 99999 available licenses."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(LicenseManagementApiInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(LicenseManagementApiOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return LicenseManagementApiInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return LicenseManagementApiOutput

    async def run(
        self, db: InMemoryDatabase, request: LicenseManagementApiInput
    ) -> LicenseManagementApiOutput:
        """Execute License Management API action."""
        try:
            if request.action == LicenseManagementAction.CHECK_AVAILABILITY:
                return await self._check_availability(db, request)
            elif request.action == LicenseManagementAction.ALLOCATE:
                return await self._allocate(db, request)
            elif request.action == LicenseManagementAction.GET_COST:
                return await self._get_cost(db, request)
            else:
                raise Tool.ExecutionError(f"Invalid action: {request.action}")

        except Tool.ExecutionError:
            raise
        except Exception as e:
            error_message = f"Failed to execute License Management API action: {str(e)}"
            raise Tool.ExecutionError(error_message)

    async def _check_availability(
        self, db: InMemoryDatabase, request: LicenseManagementApiInput
    ) -> LicenseManagementApiOutput:
        """Check available license count for a specific software and pool type."""
        if not request.catalog_id:
            raise Tool.ExecutionError("Missing required parameter: catalog_id")
        if not request.pool_type:
            raise Tool.ExecutionError("Missing required parameter: pool_type")

        # Get license pool
        all_pools = db.get_all(LicensePoolRecord)
        pool = None
        for p in all_pools:
            if p.catalog_id == request.catalog_id and p.pool_type == request.pool_type:
                pool = p
                break

        # If pool not found, raise error
        if not pool:
            raise Tool.ExecutionError(
                f"License pool not found for catalog_id={request.catalog_id}, pool_type={request.pool_type}"
            )

        # If total_licenses is NULL (enterprise pool), return available_count: 99999
        if pool.total_licenses is None:
            return LicenseManagementApiOutput(available_count=99999)

        # For standard pool, calculate available licenses
        # Get all active allocations for this catalog_id and pool_type
        all_allocations = db.get_all(LicenseAllocation)
        active_allocations = sum(
            1
            for allocation in all_allocations
            if allocation.catalog_id == request.catalog_id
            and allocation.pool_type == request.pool_type
            and allocation.deallocated_at is None
        )

        available_count = pool.total_licenses - active_allocations

        return LicenseManagementApiOutput(available_count=available_count)

    async def _allocate(
        self, db: InMemoryDatabase, request: LicenseManagementApiInput
    ) -> LicenseManagementApiOutput:
        """Allocate a license to an employee."""
        if not request.catalog_id:
            raise Tool.ExecutionError("Missing required parameter: catalog_id")
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")
        if not request.pool_type:
            raise Tool.ExecutionError("Missing required parameter: pool_type")

        # Generate allocation ID
        existing_allocations = db.get_all(LicenseAllocation)
        PREFIX_FOR_NEW_IDS = "LIC-2"
        count = 0
        existing_ids = {allocation.id for allocation in existing_allocations}

        while True:
            new_id = f"{PREFIX_FOR_NEW_IDS}-{count:06d}"
            if new_id not in existing_ids:
                break
            count += 1

        # Create new allocation
        new_allocation = LicenseAllocation(
            id=new_id,
            catalog_id=request.catalog_id,
            employee_email=request.email,
            engagement_code=request.engagement_code,  # Optional
            pool_type=request.pool_type,
            deallocated_at=None,
        )

        db.create(new_allocation)

        return LicenseManagementApiOutput(success=True)

    async def _get_cost(
        self, db: InMemoryDatabase, request: LicenseManagementApiInput
    ) -> LicenseManagementApiOutput:
        """Get annual cost of a software license."""
        if not request.catalog_id:
            raise Tool.ExecutionError("Missing required parameter: catalog_id")

        # Get software catalog entry
        software = db.get_by_id(SoftwareCatalog, request.catalog_id)

        # If not found, raise error
        if not software:
            raise Tool.ExecutionError(
                f"Software catalog entry not found: {request.catalog_id}"
            )

        return LicenseManagementApiOutput(annual_cost=software.annual_cost)
