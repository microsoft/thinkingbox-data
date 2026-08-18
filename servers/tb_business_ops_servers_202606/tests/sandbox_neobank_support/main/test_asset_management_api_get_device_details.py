# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for asset_management_api_get_device_details tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.asset_management_api_get_device_details import (
    GetDeviceDetailsInput,
    GetDeviceDetailsTool,
)


@pytest.mark.anyio
async def test_get_device_details_assigned_device(db):
    """Test getting details for an assigned device."""
    tool = GetDeviceDetailsTool()
    request = GetDeviceDetailsInput(asset_id="VDB-HW-29417")

    result = await tool.run(db, request)

    assert result.asset_id == "VDB-HW-29417"
    assert result.device_type == "laptop_premium"
    assert result.device_model == "MacBook Pro 16-inch M2"
    assert result.warehouse_location == "sf"
    assert result.condition == "good"
    assert result.purchase_date == "2023-01-15T00:00:00Z"
    assert 33 <= result.age_months <= 36
    assert result.is_assigned is True
    assert result.assigned_to == "WD-847291"


@pytest.mark.anyio
async def test_get_device_details_unassigned_device(db):
    """Test getting details for an unassigned device."""
    tool = GetDeviceDetailsTool()
    request = GetDeviceDetailsInput(asset_id="VDB-HW-57382")

    result = await tool.run(db, request)

    assert result.asset_id == "VDB-HW-57382"
    assert result.device_type == "laptop_standard"
    assert result.condition == "new"
    assert result.is_assigned is False
    assert result.assigned_to is None


@pytest.mark.anyio
async def test_get_device_details_retired_device(db):
    """Test getting details for a retired device."""
    tool = GetDeviceDetailsTool()
    request = GetDeviceDetailsInput(asset_id="VDB-HW-14725")

    result = await tool.run(db, request)

    assert result.asset_id == "VDB-HW-14725"
    assert result.condition == "retired"
    assert result.is_assigned is False


@pytest.mark.anyio
async def test_get_device_details_monitor(db):
    """Test getting details for a monitor device."""
    tool = GetDeviceDetailsTool()
    request = GetDeviceDetailsInput(asset_id="VDB-HW-68149")

    result = await tool.run(db, request)

    assert result.asset_id == "VDB-HW-68149"
    assert result.device_type == "monitor"
    assert result.device_model == "Dell UltraSharp 27 U2723DE"
    assert result.is_assigned is True
    assert result.assigned_to == "WD-847291"


@pytest.mark.anyio
async def test_get_device_details_not_found(db):
    """Test error when device not found."""
    tool = GetDeviceDetailsTool()
    request = GetDeviceDetailsInput(asset_id="VDB-HW-99999")

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "Asset not found" in str(exc_info.value)
