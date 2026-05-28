# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from sandbox_servers.toolslib.sandbox_neobank_support.main.models import (
    GenericAccessLevel,
)
from sandbox_servers.toolslib.sandbox_neobank_support.main.tools.okta_api_provision_access import (
    OktaProvisionAccessInput,
    OktaProvisionAccessTool,
)
from sandbox_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.mark.anyio
async def test_provision_access_success(db):
    """Test successful access provisioning"""
    tool = OktaProvisionAccessTool()
    input_data = OktaProvisionAccessInput(
        email="robert.anderson@vdb.com",
        app_name="Slack",
        access_level=GenericAccessLevel.READ_WRITE,
    )

    result = await tool.run(db, input_data)

    assert result.app_access_id.startswith("OAA-")


@pytest.mark.anyio
async def test_provision_access_already_exists(db):
    """Test provisioning access when access already exists"""
    tool = OktaProvisionAccessTool()
    input_data = OktaProvisionAccessInput(
        email="marcus.thompson@vdb.com",
        app_name="Salesforce",
        access_level=GenericAccessLevel.ADMIN,
    )

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, input_data)

    assert "already has access" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_provision_access_employee_not_found(db):
    """Test provisioning access for non-existent employee"""
    tool = OktaProvisionAccessTool()
    input_data = OktaProvisionAccessInput(
        email="nonexistent@vdb.com",
        app_name="Slack",
        access_level=GenericAccessLevel.READ_ONLY,
    )

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, input_data)

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_provision_access_with_read_only(db):
    """Test provisioning access with read_only level"""
    tool = OktaProvisionAccessTool()
    input_data = OktaProvisionAccessInput(
        email="maria.garcia@vdb.com",
        app_name="Jira",
        access_level=GenericAccessLevel.READ_ONLY,
    )

    result = await tool.run(db, input_data)

    assert result.app_access_id.startswith("OAA-")


@pytest.mark.anyio
async def test_provision_access_creates_valid_record(db):
    """Test that provision_access creates a valid DB record"""
    tool = OktaProvisionAccessTool()
    input_data = OktaProvisionAccessInput(
        email="amanda.lee@vdb.com",
        app_name="Confluence",
        access_level=GenericAccessLevel.READ_WRITE,
    )

    result = await tool.run(db, input_data)

    # Verify the record was created
    from sandbox_servers.toolslib.sandbox_neobank_support.main.models import (
        OktaAppAccess,
    )

    all_accesses = db.get_all(OktaAppAccess)
    new_access = [a for a in all_accesses if a.id == result.app_access_id]

    assert len(new_access) == 1
    assert new_access[0].is_active is True
    assert new_access[0].app_name == "Confluence"


@pytest.mark.anyio
async def test_provision_access_with_temporary_access(db):
    """Test provisioning temporary access with expiry date."""
    tool = OktaProvisionAccessTool()
    expiry_date = "2025-12-31T23:59:59Z"
    input_data = OktaProvisionAccessInput(
        email="sophia.davis@vdb.com",
        app_name="Snowflake",
        access_level=GenericAccessLevel.READ_ONLY,
        is_temporary=True,
        access_expiry_date=expiry_date,
    )

    result = await tool.run(db, input_data)

    # Verify the record was created with temporary access settings
    from sandbox_servers.toolslib.sandbox_neobank_support.main.models import (
        OktaAppAccess,
    )

    access_record = db.get_by_id(OktaAppAccess, result.app_access_id)

    assert access_record is not None
    assert access_record.is_temporary is True
    assert access_record.expires_at == expiry_date
    assert access_record.is_active is True


@pytest.mark.anyio
async def test_provision_access_permanent_access(db):
    """Test provisioning permanent access (is_temporary=False, no expiry)."""
    tool = OktaProvisionAccessTool()
    input_data = OktaProvisionAccessInput(
        email="emma.wilson@vdb.com",
        app_name="GitHub",
        access_level=GenericAccessLevel.WRITE,
        is_temporary=False,
    )

    result = await tool.run(db, input_data)

    # Verify the record was created as permanent access
    from sandbox_servers.toolslib.sandbox_neobank_support.main.models import (
        OktaAppAccess,
    )

    access_record = db.get_by_id(OktaAppAccess, result.app_access_id)

    assert access_record is not None
    assert access_record.is_temporary is False
    assert access_record.expires_at is None
    assert access_record.is_active is True
