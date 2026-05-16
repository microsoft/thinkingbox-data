# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for license_management_api_allocate_license tool."""

import pytest
from ms_toloka_servers.toolslib.sandbox_neobank_support.main.tools.license_management_api_allocate_license import (
    LicenseAllocateInput,
    LicenseAllocateTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.mark.anyio
async def test_allocate_license_success(db):
    """Test successful license allocation."""
    tool = LicenseAllocateTool()
    request = LicenseAllocateInput(software_name="Looker", email="david.kim@vdb.com")

    result = await tool.run(db, request)

    assert result.allocation_id == "LAL-00000009"


@pytest.mark.anyio
async def test_allocate_license_unlimited_pool(db):
    """Test allocation from unlimited pool."""
    tool = LicenseAllocateTool()
    request = LicenseAllocateInput(software_name="Slack", email="emma.wilson@vdb.com")

    result = await tool.run(db, request)

    assert result.allocation_id == "LAL-00000009"


@pytest.mark.anyio
async def test_allocate_license_already_allocated(db):
    """Test error when employee already has license."""
    # First allocate a license
    tool = LicenseAllocateTool()
    request1 = LicenseAllocateInput(
        software_name="Looker", email="thomas.white@vdb.com"
    )
    await tool.run(db, request1)

    # Try to allocate again - should fail
    request2 = LicenseAllocateInput(
        software_name="Looker", email="thomas.white@vdb.com"
    )

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request2)

    assert "Employee already has a license" in str(exc_info.value)


@pytest.mark.anyio
async def test_allocate_license_employee_not_found(db):
    """Test error when employee not found."""
    tool = LicenseAllocateTool()
    request = LicenseAllocateInput(software_name="Tableau", email="nonexistent@vdb.com")

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "Employee not found" in str(exc_info.value)


@pytest.mark.anyio
async def test_allocate_license_software_not_found(db):
    """Test error when software not found."""
    tool = LicenseAllocateTool()
    request = LicenseAllocateInput(
        software_name="NonExistentSoftware", email="marcus.thompson@vdb.com"
    )

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "Software not found" in str(exc_info.value)
