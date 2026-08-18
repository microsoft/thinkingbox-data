# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for license_management_api_check_license_type tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import LicenseType
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.license_management_api_check_license_type import (
    LicenseCheckTypeInput,
    LicenseCheckTypeTool,
)


@pytest.mark.anyio
async def test_check_license_type_standard(db):
    """Test checking license type for standard license pool."""
    tool = LicenseCheckTypeTool()
    request = LicenseCheckTypeInput(software_name="Tableau")

    result = await tool.run(db, request)

    assert result.license_type == LicenseType.STANDARD
    assert result.license_id == "LIC-29471863"


@pytest.mark.anyio
async def test_check_license_type_unlimited(db):
    """Test checking license type for unlimited license pool."""
    tool = LicenseCheckTypeTool()
    request = LicenseCheckTypeInput(software_name="Salesforce")

    result = await tool.run(db, request)

    assert result.license_type == LicenseType.UNLIMITED
    assert result.license_id == "LIC-57382946"


@pytest.mark.anyio
async def test_check_license_type_individual(db):
    """Test checking license type for individual license."""
    tool = LicenseCheckTypeTool()
    request = LicenseCheckTypeInput(software_name="Adobe Creative Cloud")

    result = await tool.run(db, request)

    assert result.license_type == LicenseType.INDIVIDUAL
    assert result.license_id == "LIC-68149527"


@pytest.mark.anyio
async def test_check_license_type_case_insensitive(db):
    """Test that software name matching is case-insensitive."""
    tool = LicenseCheckTypeTool()
    request = LicenseCheckTypeInput(software_name="tableau")

    result = await tool.run(db, request)

    assert result.license_type == LicenseType.STANDARD
    assert result.license_id == "LIC-29471863"


@pytest.mark.anyio
async def test_check_license_type_not_found(db):
    """Test error when software not found."""
    tool = LicenseCheckTypeTool()
    request = LicenseCheckTypeInput(software_name="NonExistentSoftware")

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, request)

    assert "Software not found in license inventory" in str(exc_info.value)
