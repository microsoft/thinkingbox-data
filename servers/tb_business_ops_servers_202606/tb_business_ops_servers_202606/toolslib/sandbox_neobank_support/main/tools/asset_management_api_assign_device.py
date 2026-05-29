# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool for assigning a hardware device to an employee."""

from datetime import datetime, timezone

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import AssetAssignment, Employee, HardwareAsset


class AssignDeviceInput(BaseModel):
    """Input for asset_management_api_assign_device."""

    model_config = ConfigDict(extra="forbid")

    asset_id: str = Field(
        ..., description="Hardware asset ID to assign", examples=["VDB-HW-00001"]
    )
    email: str = Field(
        ..., description="Employee email address", examples=["john.smith@vdb.com"]
    )


class AssignDeviceOutput(BaseModel):
    """Output for asset_management_api_assign_device."""

    assignment_id: str = Field(..., description="Assignment ID")
    asset_id: str = Field(..., description="Asset ID")
    employee_id: str = Field(..., description="Employee ID")


class AssignDeviceTool(Tool):
    """Tool for assigning a hardware device to an employee."""

    @property
    def name(self) -> str:
        return "asset_management_api_assign_device"

    @property
    def description(self) -> str:
        return "Assign a hardware device to an employee. Device must be available (unassigned) and in good condition."

    @property
    def request_model(self):
        return AssignDeviceInput

    @property
    def output_model(self):
        return AssignDeviceOutput

    async def run(
        self, db: InMemoryDatabase, request: AssignDeviceInput
    ) -> AssignDeviceOutput:
        """Assign device to employee."""
        # Get employee by email
        all_employees = db.get_all(Employee)
        employees = [e for e in all_employees if e.email == request.email]

        if not employees:
            raise Tool.ExecutionError(f"Employee not found: {request.email}")

        employee = employees[0]

        # Get asset by ID
        all_assets = db.get_all(HardwareAsset)
        matching_assets = [a for a in all_assets if a.id == request.asset_id]

        if not matching_assets:
            raise Tool.ExecutionError(f"Asset not found: {request.asset_id}")

        asset = matching_assets[0]

        # Check if asset is already assigned
        if asset.is_assigned:
            raise Tool.ExecutionError(f"Asset {request.asset_id} is already assigned")

        # Check asset condition
        if asset.condition.value == "retired":
            raise Tool.ExecutionError(
                f"Cannot assign retired asset: {request.asset_id}"
            )

        # Generate assignment ID
        all_assignments = db.get_all(AssetAssignment)
        next_id = len(all_assignments) + 1
        assignment_id = f"ASN-{next_id:08d}"

        # Create assignment (assigned_at is now optional, set by caller if needed)
        assignment = AssetAssignment(
            id=assignment_id,
            asset_id=asset.id,
            employee_id=employee.id,
            assigned_at=None,
            assigned_by="system",
            is_active=True,
        )
        db.create(assignment)

        # Update asset assignment status
        asset.is_assigned = True
        db.update(asset)

        return AssignDeviceOutput(
            assignment_id=assignment_id, asset_id=asset.id, employee_id=employee.id
        )
