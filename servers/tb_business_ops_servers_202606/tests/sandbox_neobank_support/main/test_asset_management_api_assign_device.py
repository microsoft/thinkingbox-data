# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for asset_management_api_assign_device tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import HardwareAsset
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.asset_management_api_assign_device import (
    AssignDeviceInput,
    AssignDeviceTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.mark.anyio
async def test_assign_device_success(db):
    """Test successfully assigning an unassigned device."""
    tool = AssignDeviceTool()
    request = AssignDeviceInput(asset_id="VDB-HW-57382", email="david.kim@vdb.com")

    result = await tool.run(db, request)

    assert result.assignment_id.startswith("ASN-")
    assert result.asset_id == "VDB-HW-57382"
    assert result.employee_id == "WD-465782"

    # Verify asset is now marked as assigned
    assets = db.get_all(HardwareAsset)
    assigned_asset = next(a for a in assets if a.id == "VDB-HW-57382")
    assert assigned_asset.is_assigned is True


@pytest.mark.anyio
async def test_assign_device_already_assigned(db):
    """Test error when trying to assign an already assigned device."""
    tool = AssignDeviceTool()
    request = AssignDeviceInput(
        asset_id="VDB-HW-29417",  # Already assigned to john.smith
        email="david.kim@vdb.com",
    )

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "already assigned" in str(exc_info.value)


@pytest.mark.anyio
async def test_assign_device_retired(db):
    """Test error when trying to assign a retired device."""
    tool = AssignDeviceTool()
    request = AssignDeviceInput(
        asset_id="VDB-HW-14725", email="david.kim@vdb.com"  # Retired device
    )

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "retired" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_assign_device_not_found(db):
    """Test error when device not found."""
    tool = AssignDeviceTool()
    request = AssignDeviceInput(asset_id="VDB-HW-99999", email="david.kim@vdb.com")

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_assign_device_employee_not_found(db):
    """Test error when employee not found."""
    tool = AssignDeviceTool()
    request = AssignDeviceInput(asset_id="VDB-HW-57382", email="nonexistent@vdb.com")

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "Employee not found" in str(exc_info.value)


@pytest.mark.anyio
async def test_assign_device_creates_assignment_record(db):
    """Test that assignment record is created in database."""
    tool = AssignDeviceTool()
    request = AssignDeviceInput(asset_id="VDB-HW-57382", email="david.kim@vdb.com")

    result = await tool.run(db, request)

    # Verify assignment record exists
    from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
        AssetAssignment,
    )

    assignments = db.get_all(AssetAssignment)
    new_assignment = next(a for a in assignments if a.id == result.assignment_id)

    assert new_assignment.asset_id == "VDB-HW-57382"
    assert new_assignment.employee_id == "WD-465782"
    assert new_assignment.is_active is True
    assert new_assignment.returned_at is None
