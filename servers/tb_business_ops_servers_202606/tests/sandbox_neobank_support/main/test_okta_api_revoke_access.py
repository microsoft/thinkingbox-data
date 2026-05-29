# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.okta_api_revoke_access import (
    OktaRevokeAccessInput,
    OktaRevokeAccessTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.mark.anyio
async def test_revoke_access_success(db):
    """Test successful access revocation"""
    tool = OktaRevokeAccessTool()
    input_data = OktaRevokeAccessInput(
        email="marcus.thompson@vdb.com", app_name="Salesforce"
    )

    result = await tool.run(db, input_data)

    assert result.revoked is True


@pytest.mark.anyio
async def test_revoke_access_no_active_access(db):
    """Test revoking access when there is no active access"""
    tool = OktaRevokeAccessTool()
    input_data = OktaRevokeAccessInput(email="david.kim@vdb.com", app_name="Jira")

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, input_data)

    assert "active access" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_revoke_access_application_not_found(db):
    """Test revoking access for non-existent application"""
    tool = OktaRevokeAccessTool()
    input_data = OktaRevokeAccessInput(
        email="marcus.thompson@vdb.com", app_name="NonexistentApp"
    )

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, input_data)

    assert "active access" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_revoke_access_employee_not_found(db):
    """Test revoking access for non-existent employee"""
    tool = OktaRevokeAccessTool()
    input_data = OktaRevokeAccessInput(
        email="nonexistent@vdb.com", app_name="Salesforce"
    )

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, input_data)

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_revoke_access_idempotent(db):
    """Test repeated access revocation"""
    tool = OktaRevokeAccessTool()
    input_data = OktaRevokeAccessInput(
        email="marcus.thompson@vdb.com", app_name="Salesforce"
    )

    # First revocation
    result1 = await tool.run(db, input_data)
    assert result1.revoked is True

    # Repeated revocation attempt should fail
    with pytest.raises(Exception) as exc_info:
        await tool.run(db, input_data)

    assert "active access" in str(exc_info.value).lower()
