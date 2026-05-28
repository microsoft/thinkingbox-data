# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool for retrieving all hardware devices assigned to an employee."""

from datetime import datetime, timezone
from typing import List

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import AssetAssignment, Employee, HardwareAsset


def _parse_purchase_date_utc(purchase_date: str, asset_id: str) -> datetime:
    """Parse purchase_date and assume UTC if timezone info is missing."""
    if not purchase_date:
        raise Tool.ExecutionError(
            f"Invalid purchase_date for asset {asset_id}: {purchase_date!r}"
        )

    try:
        parsed = datetime.fromisoformat(purchase_date.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Tool.ExecutionError(
            f"Invalid purchase_date for asset {asset_id}: {purchase_date!r}"
        ) from exc

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


class GetEmployeeDevicesInput(BaseModel):
    """Input for asset_management_api_get_employee_devices."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(
        ..., description="Employee email address", examples=["john.smith@vdb.com"]
    )


class DeviceInfo(BaseModel):
    """Device information."""

    asset_id: str = Field(..., description="Asset ID")
    device_type: str = Field(..., description="Device type")
    device_model: str = Field(..., description="Device model")
    assigned_at: str = Field(..., description="Assignment timestamp")
    condition: str = Field(..., description="Device condition")
    age_months: int = Field(..., description="Device age in months")


class GetEmployeeDevicesOutput(BaseModel):
    """Output for asset_management_api_get_employee_devices."""

    employee_id: str = Field(..., description="Employee ID")
    devices: List[DeviceInfo] = Field(..., description="List of assigned devices")


class GetEmployeeDevicesTool(Tool):
    """Tool for getting all hardware devices assigned to an employee."""

    @property
    def name(self) -> str:
        return "asset_management_api_get_employee_devices"

    @property
    def description(self) -> str:
        return "Retrieve all hardware devices currently assigned to an employee. Returns device details including type, model, age, and condition."

    @property
    def request_model(self):
        return GetEmployeeDevicesInput

    @property
    def output_model(self):
        return GetEmployeeDevicesOutput

    async def run(
        self, db: InMemoryDatabase, request: GetEmployeeDevicesInput
    ) -> GetEmployeeDevicesOutput:
        """Get all devices assigned to an employee."""
        # Get employee by email
        all_employees = db.get_all(Employee)
        employees = [e for e in all_employees if e.email == request.email]

        if not employees:
            raise Tool.ExecutionError(f"Employee not found: {request.email}")

        employee = employees[0]

        # Get all active assignments for this employee
        all_assignments = db.get_all(AssetAssignment)
        active_assignments = [
            a for a in all_assignments if a.employee_id == employee.id and a.is_active
        ]

        # Get device details for each assignment
        all_assets = db.get_all(HardwareAsset)
        devices = []

        FIXED_CURRENT_TIME = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)

        for assignment in active_assignments:
            # Find the asset
            matching_assets = [a for a in all_assets if a.id == assignment.asset_id]
            if not matching_assets:
                continue

            asset = matching_assets[0]

            # Calculate age in months
            purchase_date = _parse_purchase_date_utc(asset.purchase_date, asset.id)
            age_months = int((FIXED_CURRENT_TIME - purchase_date).days / 30)

            devices.append(
                DeviceInfo(
                    asset_id=asset.id,
                    device_type=asset.device_type.value,
                    device_model=asset.device_model,
                    assigned_at=assignment.assigned_at,
                    condition=asset.condition.value,
                    age_months=age_months,
                )
            )

        return GetEmployeeDevicesOutput(employee_id=employee.id, devices=devices)
