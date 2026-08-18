# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for asset_management_api_get_employee_devices tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.asset_management_api_get_employee_devices import (
    GetEmployeeDevicesInput,
    GetEmployeeDevicesTool,
)


@pytest.mark.anyio
async def test_get_employee_devices_with_multiple_devices(db):
    """Test getting devices for employee with multiple assignments."""
    tool = GetEmployeeDevicesTool()
    request = GetEmployeeDevicesInput(email="marcus.thompson@vdb.com")

    result = await tool.run(db, request)

    assert result.employee_id == "WD-847291"
    assert len(result.devices) == 2  # laptop and monitor

    # Check first device
    device_ids = [d.asset_id for d in result.devices]
    assert "VDB-HW-29417" in device_ids
    assert "VDB-HW-68149" in device_ids


@pytest.mark.anyio
async def test_get_employee_devices_single_device(db):
    """Test getting devices for employee with single assignment."""
    tool = GetEmployeeDevicesTool()
    request = GetEmployeeDevicesInput(email="emma.wilson@vdb.com")

    result = await tool.run(db, request)

    assert result.employee_id == "WD-192638"
    assert len(result.devices) == 1
    assert result.devices[0].asset_id == "VDB-HW-84726"
    assert result.devices[0].device_type == "laptop_standard"


@pytest.mark.anyio
async def test_get_employee_devices_no_devices(db):
    """Test getting devices for employee with no assignments."""
    tool = GetEmployeeDevicesTool()
    request = GetEmployeeDevicesInput(email="david.kim@vdb.com")

    result = await tool.run(db, request)

    assert result.employee_id == "WD-465782"
    assert len(result.devices) == 0


@pytest.mark.anyio
async def test_get_employee_devices_check_age_calculation(db):
    """Test that device age is calculated correctly."""
    tool = GetEmployeeDevicesTool()
    request = GetEmployeeDevicesInput(email="marcus.thompson@vdb.com")

    result = await tool.run(db, request)

    # Find the laptop (VDB-HW-29417, purchased 2023-01-15)
    laptop = next(d for d in result.devices if d.asset_id == "VDB-HW-29417")
    # From 2023-01-15 to 2025-12-17 is about 34-35 months
    assert 33 <= laptop.age_months <= 36


@pytest.mark.anyio
async def test_get_employee_devices_employee_not_found(db):
    """Test error when employee not found."""
    tool = GetEmployeeDevicesTool()
    request = GetEmployeeDevicesInput(email="nonexistent@vdb.com")

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "Employee not found" in str(exc_info.value)
