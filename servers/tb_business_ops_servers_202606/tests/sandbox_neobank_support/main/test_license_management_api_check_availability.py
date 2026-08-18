# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for license_management_api_check_availability tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import LicenseType
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.license_management_api_check_availability import (
    LicenseCheckAvailabilityInput,
    LicenseCheckAvailabilityTool,
)


@pytest.mark.anyio
async def test_check_availability_standard_pool(db):
    """Test checking availability for standard license pool with allocations."""
    tool = LicenseCheckAvailabilityTool()
    request = LicenseCheckAvailabilityInput(software_name="Tableau")

    result = await tool.run(db, request)

    # Tableau has 25 total, 2 active allocations (LAL-24719583, LAL-53826947)
    assert result.license_type == LicenseType.STANDARD
    assert result.total_licenses == 25
    assert result.available_licenses == 23


@pytest.mark.anyio
async def test_check_availability_unlimited_pool(db):
    """Test checking availability for unlimited license pool."""
    tool = LicenseCheckAvailabilityTool()
    request = LicenseCheckAvailabilityInput(software_name="Salesforce")

    result = await tool.run(db, request)

    assert result.license_type == LicenseType.UNLIMITED
    assert result.total_licenses is None
    assert result.available_licenses is None


@pytest.mark.anyio
async def test_check_availability_individual_pool(db):
    """Test checking availability for individual license pool."""
    tool = LicenseCheckAvailabilityTool()
    request = LicenseCheckAvailabilityInput(software_name="Adobe Creative Cloud")

    result = await tool.run(db, request)

    # Adobe CC has 10 total, 1 active allocation (LAL-67194238)
    assert result.license_type == LicenseType.INDIVIDUAL
    assert result.total_licenses == 10
    assert result.available_licenses == 9


@pytest.mark.anyio
async def test_check_availability_jira(db):
    """Test checking availability for Jira license pool."""
    tool = LicenseCheckAvailabilityTool()
    request = LicenseCheckAvailabilityInput(software_name="Jira")

    result = await tool.run(db, request)

    # Jira has 50 total, 2 active allocations (LAL-81473956, LAL-19582637)
    assert result.license_type == LicenseType.STANDARD
    assert result.total_licenses == 50
    assert result.available_licenses == 48


@pytest.mark.anyio
async def test_check_availability_not_found(db):
    """Test error when software not found."""
    tool = LicenseCheckAvailabilityTool()
    request = LicenseCheckAvailabilityInput(software_name="NonExistentSoftware")

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "Software not found in license inventory" in str(exc_info.value)
