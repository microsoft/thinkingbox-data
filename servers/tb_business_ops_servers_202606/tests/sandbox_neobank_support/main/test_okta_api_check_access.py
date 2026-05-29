# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.okta_api_check_access import (
    OktaCheckAccessInput,
    OktaCheckAccessTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.mark.anyio
async def test_check_access_with_existing_active_access(db):
    """Test checking existing active access"""
    tool = OktaCheckAccessTool()
    input_data = OktaCheckAccessInput(
        email="marcus.thompson@vdb.com", app_name="Salesforce"
    )

    result = await tool.run(db, input_data)

    assert result.has_access is True
    assert result.access_level is not None
    assert result.access_level == "read_only"
    assert result.granted_at is not None


@pytest.mark.anyio
async def test_check_access_with_revoked_access(db):
    """Test checking revoked access"""
    tool = OktaCheckAccessTool()
    input_data = OktaCheckAccessInput(email="david.kim@vdb.com", app_name="Jira")

    result = await tool.run(db, input_data)

    assert result.has_access is False
    assert result.access_level is None
    assert result.granted_at is None


@pytest.mark.anyio
async def test_check_access_no_access_record(db):
    """Test checking non-existent access"""
    tool = OktaCheckAccessTool()
    input_data = OktaCheckAccessInput(
        email="marcus.thompson@vdb.com", app_name="Zendesk"
    )

    result = await tool.run(db, input_data)

    assert result.has_access is False
    assert result.access_level is None
    assert result.granted_at is None


@pytest.mark.anyio
async def test_check_access_employee_not_found(db):
    """Test checking access for non-existent employee"""
    tool = OktaCheckAccessTool()
    input_data = OktaCheckAccessInput(
        email="nonexistent@vdb.com", app_name="Salesforce"
    )

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, input_data)

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_check_access_multiple_records_returns_latest(db):
    """Test that only active access is returned"""
    tool = OktaCheckAccessTool()
    input_data = OktaCheckAccessInput(email="maria.garcia@vdb.com", app_name="Zendesk")

    result = await tool.run(db, input_data)

    assert result.has_access is True
    assert result.access_level is not None
    assert result.granted_at is not None
