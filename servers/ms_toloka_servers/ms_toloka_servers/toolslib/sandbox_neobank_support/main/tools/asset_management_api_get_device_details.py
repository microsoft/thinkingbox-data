# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool for retrieving detailed information about a hardware device."""

from datetime import datetime, timezone
from typing import Optional

from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import AssetAssignment, HardwareAsset


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


class GetDeviceDetailsInput(BaseModel):
    """Input for asset_management_api_get_device_details."""

    model_config = ConfigDict(extra="forbid")

    asset_id: str = Field(
        ..., description="Hardware asset ID", examples=["VDB-HW-00001"]
    )


class GetDeviceDetailsOutput(BaseModel):
    """Output for asset_management_api_get_device_details."""

    asset_id: str = Field(..., description="Asset ID")
    device_type: str = Field(..., description="Device type")
    device_model: str = Field(..., description="Device model")
    purchase_date: str = Field(..., description="Purchase date")
    age_months: int = Field(..., description="Device age in months")
    condition: str = Field(..., description="Device condition")
    warehouse_location: str = Field(..., description="Warehouse location")
    is_assigned: bool = Field(..., description="Whether device is currently assigned")
    assigned_to: Optional[str] = Field(None, description="Employee ID if assigned")


class GetDeviceDetailsTool(Tool):
    """Tool for getting detailed information about a hardware device."""

    @property
    def name(self) -> str:
        return "asset_management_api_get_device_details"

    @property
    def description(self) -> str:
        return "Retrieve detailed information about a specific hardware device including age, condition, and assignment status."

    @property
    def request_model(self):
        return GetDeviceDetailsInput

    @property
    def output_model(self):
        return GetDeviceDetailsOutput

    async def run(
        self, db: InMemoryDatabase, request: GetDeviceDetailsInput
    ) -> GetDeviceDetailsOutput:
        """Get device details."""
        # Get asset by ID
        all_assets = db.get_all(HardwareAsset)
        matching_assets = [a for a in all_assets if a.id == request.asset_id]

        if not matching_assets:
            raise Tool.ExecutionError(f"Asset not found: {request.asset_id}")

        asset = matching_assets[0]

        # Calculate age in months
        FIXED_CURRENT_TIME = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)
        purchase_date = _parse_purchase_date_utc(asset.purchase_date, asset.id)
        age_months = int((FIXED_CURRENT_TIME - purchase_date).days / 30)

        # Check if assigned
        assigned_to = None
        if asset.is_assigned:
            all_assignments = db.get_all(AssetAssignment)
            active_assignments = [
                a for a in all_assignments if a.asset_id == asset.id and a.is_active
            ]
            if active_assignments:
                assigned_to = active_assignments[0].employee_id

        return GetDeviceDetailsOutput(
            asset_id=asset.id,
            device_type=asset.device_type.value,
            device_model=asset.device_model,
            purchase_date=asset.purchase_date,
            age_months=age_months,
            condition=asset.condition.value,
            warehouse_location=asset.warehouse_location.value,
            is_assigned=asset.is_assigned,
            assigned_to=assigned_to,
        )
