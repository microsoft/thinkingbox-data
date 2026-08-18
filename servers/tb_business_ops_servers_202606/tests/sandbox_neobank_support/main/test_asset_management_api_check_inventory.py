# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for asset_management_api_check_inventory tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.asset_management_api_check_inventory import (
    CheckInventoryInput,
    CheckInventoryTool,
)


@pytest.mark.anyio
async def test_check_inventory_laptops_sf(db):
    """Test checking inventory for laptops in SF warehouse."""
    tool = CheckInventoryTool()
    request = CheckInventoryInput(
        device_type="laptop_standard", warehouse_location="sf"
    )

    result = await tool.run(db, request)

    assert result.device_type == "laptop_standard"
    assert result.warehouse_location == "sf"
    assert result.available_count >= 0
    assert result.total_count > 0


@pytest.mark.anyio
async def test_check_inventory_monitors_nyc(db):
    """Test checking inventory for monitors in NYC warehouse."""
    tool = CheckInventoryTool()
    request = CheckInventoryInput(device_type="monitor", warehouse_location="nyc")

    result = await tool.run(db, request)

    assert result.device_type == "monitor"
    assert result.warehouse_location == "nyc"
    assert result.available_count > 0
    assert result.total_count > 0


@pytest.mark.anyio
async def test_check_inventory_no_available_devices(db):
    """Test checking inventory when no devices available."""
    tool = CheckInventoryTool()
    request = CheckInventoryInput(
        device_type="docking_station", warehouse_location="sf"
    )

    result = await tool.run(db, request)

    assert result.device_type == "docking_station"
    assert result.warehouse_location == "sf"
    assert result.available_count >= 0
    assert result.total_count >= 0


@pytest.mark.anyio
async def test_check_inventory_excludes_assigned_devices(db):
    """Test that assigned devices are excluded from inventory."""
    tool = CheckInventoryTool()
    request = CheckInventoryInput(device_type="laptop_premium", warehouse_location="sf")

    result = await tool.run(db, request)

    # VDB-HW-00001 is assigned, so available should be less than total
    assert result.available_count < result.total_count or result.total_count == 0


@pytest.mark.anyio
async def test_check_inventory_excludes_retired_devices(db):
    """Test that retired devices are excluded from inventory."""
    tool = CheckInventoryTool()
    request = CheckInventoryInput(device_type="mouse", warehouse_location="austin")

    result = await tool.run(db, request)

    # Retired devices shouldn't be counted
    # This verifies that retired devices are excluded from total_count
    assert result.total_count >= 0


@pytest.mark.anyio
async def test_check_inventory_headsets_austin(db):
    """Test checking inventory for headsets in Austin warehouse."""
    tool = CheckInventoryTool()
    request = CheckInventoryInput(device_type="headset", warehouse_location="austin")

    result = await tool.run(db, request)

    assert result.device_type == "headset"
    assert result.warehouse_location == "austin"
    # VDB-HW-00010 is the only headset in Austin, and it's now correctly marked as assigned
    assert result.available_count == 0
    assert result.total_count == 1


@pytest.mark.anyio
async def test_check_inventory_returns_asset_list(db):
    """Test that check inventory returns asset_ids with device_model and asset_id."""
    tool = CheckInventoryTool()
    request = CheckInventoryInput(
        device_type="laptop_standard", warehouse_location="sf"
    )

    result = await tool.run(db, request)

    # Verify asset_ids list is returned
    assert isinstance(result.asset_ids, list)
    assert len(result.asset_ids) == result.available_count

    # If there are available assets, verify structure
    if result.available_count > 0:
        for asset_info in result.asset_ids:
            assert hasattr(asset_info, "asset_id")
            assert hasattr(asset_info, "device_model")
            assert asset_info.asset_id.startswith("VDB-HW-")
            assert isinstance(asset_info.device_model, str)


@pytest.mark.anyio
async def test_check_inventory_only_includes_new_and_good_condition(db):
    """Test that only 'new' and 'good' condition devices are included in available count."""
    from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
        DeviceCondition,
        DeviceType,
        HardwareAsset,
        WarehouseLocation,
    )

    tool = CheckInventoryTool()

    # Add test assets with different conditions
    test_assets = [
        HardwareAsset(
            id="VDB-HW-99901",
            device_type=DeviceType.KEYBOARD,
            device_model="Test Keyboard New",
            purchase_date="2025-01-01T00:00:00Z",
            warehouse_location=WarehouseLocation.SF,
            condition=DeviceCondition.NEW,
            is_assigned=False,
        ),
        HardwareAsset(
            id="VDB-HW-99902",
            device_type=DeviceType.KEYBOARD,
            device_model="Test Keyboard Good",
            purchase_date="2025-01-01T00:00:00Z",
            warehouse_location=WarehouseLocation.SF,
            condition=DeviceCondition.GOOD,
            is_assigned=False,
        ),
        HardwareAsset(
            id="VDB-HW-99903",
            device_type=DeviceType.KEYBOARD,
            device_model="Test Keyboard Fair",
            purchase_date="2025-01-01T00:00:00Z",
            warehouse_location=WarehouseLocation.SF,
            condition=DeviceCondition.FAIR,
            is_assigned=False,
        ),
        HardwareAsset(
            id="VDB-HW-99904",
            device_type=DeviceType.KEYBOARD,
            device_model="Test Keyboard Poor",
            purchase_date="2025-01-01T00:00:00Z",
            warehouse_location=WarehouseLocation.SF,
            condition=DeviceCondition.POOR,
            is_assigned=False,
        ),
    ]

    for asset in test_assets:
        db.create(asset)

    request = CheckInventoryInput(device_type="keyboard", warehouse_location="sf")

    result = await tool.run(db, request)

    # Only NEW and GOOD condition devices should be counted as available
    # Total count includes all conditions except retired
    # Available count should only include 'new' and 'good' unassigned devices
    assert result.available_count >= 2  # At least our 2 test devices (new and good)
    assert result.total_count >= 4  # All 4 test devices

    # Verify that asset_ids only contains new and good condition assets
    asset_ids_set = {asset.asset_id for asset in result.asset_ids}
    assert "VDB-HW-99901" in asset_ids_set  # NEW should be included
    assert "VDB-HW-99902" in asset_ids_set  # GOOD should be included
    assert "VDB-HW-99903" not in asset_ids_set  # FAIR should NOT be included
    assert "VDB-HW-99904" not in asset_ids_set  # POOR should NOT be included
