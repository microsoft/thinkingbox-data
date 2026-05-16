# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool for checking available hardware inventory at warehouse locations."""

from typing import List

from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import DeviceType, HardwareAsset, WarehouseLocation


class CheckInventoryInput(BaseModel):
    """Input for asset_management_api_check_inventory."""

    model_config = ConfigDict(extra="forbid")

    device_type: str = Field(
        ...,
        description="Type of device to check",
        examples=["laptop_standard", "monitor", "headset"],
    )
    warehouse_location: str = Field(
        ..., description="Warehouse location", examples=["sf", "nyc", "austin"]
    )


class AssetInfo(BaseModel):
    """Asset information."""

    device_model: str = Field(..., description="Device model name")
    asset_id: str = Field(..., description="Asset ID (format: VDB-HW-#####)")


class CheckInventoryOutput(BaseModel):
    """Output for asset_management_api_check_inventory."""

    device_type: str = Field(..., description="Device type")
    warehouse_location: str = Field(..., description="Warehouse location")
    available_count: int = Field(..., description="Number of available devices")
    total_count: int = Field(..., description="Total number of devices at location")
    asset_ids: List[AssetInfo] = Field(
        ..., description="List of available asset details (device_model and asset_id)"
    )


class CheckInventoryTool(Tool):
    """Tool for checking available hardware inventory at a warehouse location."""

    @property
    def name(self) -> str:
        return "asset_management_api_check_inventory"

    @property
    def description(self) -> str:
        return "Check the number of available (unassigned) devices of a specific type at a warehouse location."

    @property
    def request_model(self):
        return CheckInventoryInput

    @property
    def output_model(self):
        return CheckInventoryOutput

    async def run(
        self, db: InMemoryDatabase, request: CheckInventoryInput
    ) -> CheckInventoryOutput:
        """Check inventory at warehouse."""
        # Validate device type
        try:
            device_type_enum = DeviceType(request.device_type)
        except ValueError:
            raise Tool.ExecutionError(f"Invalid device type: {request.device_type}")

        # Validate warehouse location
        try:
            warehouse_enum = WarehouseLocation(request.warehouse_location)
        except ValueError:
            raise Tool.ExecutionError(
                f"Invalid warehouse location: {request.warehouse_location}"
            )

        # Get all assets matching device type and location
        all_assets = db.get_all(HardwareAsset)
        matching_assets = [
            a
            for a in all_assets
            if a.device_type == device_type_enum
            and a.warehouse_location == warehouse_enum
            and a.condition.value != "retired"  # Don't count retired devices
        ]

        total_count = len(matching_assets)

        # WHERE clause: device_type = ? AND warehouse_location = ? AND is_assigned = false AND condition IN ('new', 'good')
        available_assets = [
            a
            for a in matching_assets
            if not a.is_assigned and a.condition.value in ("new", "good")
        ]
        available_count = len(available_assets)

        # Build asset_ids list with device model and asset id
        asset_ids = [
            AssetInfo(device_model=a.device_model, asset_id=a.id)
            for a in available_assets
        ]

        return CheckInventoryOutput(
            device_type=request.device_type,
            warehouse_location=request.warehouse_location,
            available_count=available_count,
            total_count=total_count,
            asset_ids=asset_ids,
        )
