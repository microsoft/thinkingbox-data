# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool for retiring a hardware device (marking for return/disposal)."""

from datetime import datetime, timezone

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
from pydantic import BaseModel, ConfigDict, Field

from ..models import AssetAssignment, DeviceCondition, HardwareAsset


class RetireDeviceInput(BaseModel):
    """Input for asset_management_api_retire_device."""

    model_config = ConfigDict(extra="forbid")

    asset_id: str = Field(
        ..., description="Hardware asset ID to retire", examples=["VDB-HW-00001"]
    )


class RetireDeviceOutput(BaseModel):
    """Output for asset_management_api_retire_device."""

    asset_id: str = Field(..., description="Asset ID")
    previous_condition: str = Field(..., description="Previous device condition")
    retired_at: str = Field(..., description="Retirement timestamp")
    was_assigned: bool = Field(
        ..., description="Whether device was assigned to employee"
    )


class RetireDeviceTool(Tool):
    """Tool for retiring a hardware device."""

    @property
    def name(self) -> str:
        return "asset_management_api_retire_device"

    @property
    def description(self) -> str:
        return "Mark a hardware device as retired. If device is assigned to an employee, the assignment will be deactivated."

    @property
    def request_model(self):
        return RetireDeviceInput

    @property
    def output_model(self):
        return RetireDeviceOutput

    async def run(
        self, db: InMemoryDatabase, request: RetireDeviceInput
    ) -> RetireDeviceOutput:
        """Retire a hardware device."""
        # Get asset by ID
        all_assets = db.get_all(HardwareAsset)
        matching_assets = [a for a in all_assets if a.id == request.asset_id]

        if not matching_assets:
            raise Tool.ExecutionError(f"Asset not found: {request.asset_id}")

        asset = matching_assets[0]

        # Check if already retired
        if asset.condition == DeviceCondition.RETIRED:
            raise Tool.ExecutionError(f"Asset {request.asset_id} is already retired")

        previous_condition = asset.condition.value
        was_assigned = asset.is_assigned

        FIXED_CURRENT_TIME = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)
        timestamp = FIXED_CURRENT_TIME.strftime("%Y-%m-%dT%H:%M:%SZ")

        # If assigned, deactivate the assignment
        if asset.is_assigned:
            all_assignments = db.get_all(AssetAssignment)
            active_assignments = [
                a for a in all_assignments if a.asset_id == asset.id and a.is_active
            ]

            for assignment in active_assignments:
                assignment.is_active = False
                assignment.returned_at = timestamp
                db.update(assignment)

        # Update asset status
        asset.condition = DeviceCondition.RETIRED
        asset.is_assigned = False
        db.update(asset)

        return RetireDeviceOutput(
            asset_id=asset.id,
            previous_condition=previous_condition,
            retired_at=timestamp,
            was_assigned=was_assigned,
        )
