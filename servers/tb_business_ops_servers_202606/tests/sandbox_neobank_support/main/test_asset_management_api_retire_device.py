# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for asset_management_api_retire_device tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.asset_management_api_retire_device import (
    RetireDeviceInput,
    RetireDeviceTool,
)


@pytest.mark.anyio
async def test_retire_device_success_unassigned(db):
    """Test successfully retiring an unassigned device."""
    tool = RetireDeviceTool()
    request = RetireDeviceInput(asset_id="VDB-HW-19263")

    result = await tool.run(db, request)

    assert result.asset_id == "VDB-HW-19263"
    assert result.previous_condition == "new"
    assert result.retired_at == "2025-12-17T10:00:00Z"
    assert result.was_assigned is False

    # Verify asset is now retired
    from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
        HardwareAsset,
    )

    assets = db.get_all(HardwareAsset)
    retired_asset = next(a for a in assets if a.id == "VDB-HW-19263")
    assert retired_asset.condition == "retired"
    assert retired_asset.is_assigned is False


@pytest.mark.anyio
async def test_retire_device_success_with_assignment(db):
    """Test successfully retiring an assigned device and deactivating assignment."""
    tool = RetireDeviceTool()
    request = RetireDeviceInput(asset_id="VDB-HW-29417")

    result = await tool.run(db, request)

    assert result.asset_id == "VDB-HW-29417"
    assert result.previous_condition == "good"
    assert result.was_assigned is True

    # Verify assignment is now inactive
    from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
        AssetAssignment,
    )

    assignments = db.get_all(AssetAssignment)
    asset_assignments = [a for a in assignments if a.asset_id == "VDB-HW-29417"]

    for assignment in asset_assignments:
        assert assignment.is_active is False
        assert assignment.returned_at == "2025-12-17T10:00:00Z"


@pytest.mark.anyio
async def test_retire_device_already_retired(db):
    """Test error when trying to retire an already retired device."""
    tool = RetireDeviceTool()
    request = RetireDeviceInput(asset_id="VDB-HW-14725")

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "already retired" in str(exc_info.value)


@pytest.mark.anyio
async def test_retire_device_not_found(db):
    """Test error when device not found."""
    tool = RetireDeviceTool()
    request = RetireDeviceInput(asset_id="VDB-HW-99999")

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_retire_device_with_multiple_assignments(db):
    """Test retiring device that had multiple assignments over time."""
    tool = RetireDeviceTool()
    request = RetireDeviceInput(asset_id="VDB-HW-68149")

    result = await tool.run(db, request)

    assert result.asset_id == "VDB-HW-68149"
    assert result.was_assigned is True

    # Verify all assignments for this asset are now inactive
    from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
        AssetAssignment,
    )

    assignments = db.get_all(AssetAssignment)
    asset_assignments = [a for a in assignments if a.asset_id == "VDB-HW-68149"]

    for assignment in asset_assignments:
        assert assignment.is_active is False
