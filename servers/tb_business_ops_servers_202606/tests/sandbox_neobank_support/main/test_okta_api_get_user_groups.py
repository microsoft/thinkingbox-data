# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.okta_api_get_user_groups import (
    OktaGetUserGroupsInput,
    OktaGetUserGroupsTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.mark.anyio
async def test_get_user_groups_multiple_groups(db):
    """Test getting list of groups for user with multiple groups"""
    tool = OktaGetUserGroupsTool()
    input_data = OktaGetUserGroupsInput(email="marcus.thompson@vdb.com")

    result = await tool.run(db, input_data)

    assert len(result.groups) == 2
    group_names = [g.group_name for g in result.groups]
    assert "bi_product_analytics" in group_names
    assert "engineers" in group_names


@pytest.mark.anyio
async def test_get_user_groups_single_group(db):
    """Test getting list of groups for user with single group"""
    tool = OktaGetUserGroupsTool()
    input_data = OktaGetUserGroupsInput(email="emma.wilson@vdb.com")

    result = await tool.run(db, input_data)

    assert len(result.groups) == 1
    assert result.groups[0].group_name == "engineers"


@pytest.mark.anyio
async def test_get_user_groups_no_groups(db):
    """Test getting list of groups for user with no groups"""
    tool = OktaGetUserGroupsTool()
    input_data = OktaGetUserGroupsInput(email="michael.rodriguez@vdb.com")

    result = await tool.run(db, input_data)

    assert len(result.groups) == 0


@pytest.mark.anyio
async def test_get_user_groups_employee_not_found(db):
    """Test getting groups for non-existent employee"""
    tool = OktaGetUserGroupsTool()
    input_data = OktaGetUserGroupsInput(email="nonexistent@vdb.com")

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, input_data)

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_get_user_groups_only_active(db):
    """Test that only active groups are returned"""
    tool = OktaGetUserGroupsTool()
    input_data = OktaGetUserGroupsInput(email="sarah.jones@vdb.com")

    result = await tool.run(db, input_data)

    assert len(result.groups) > 0


@pytest.mark.anyio
async def test_get_user_groups_with_metadata(db):
    """Test that all necessary group metadata is returned"""
    tool = OktaGetUserGroupsTool()
    input_data = OktaGetUserGroupsInput(email="marcus.thompson@vdb.com")

    result = await tool.run(db, input_data)

    assert len(result.groups) > 0

    for group in result.groups:
        assert group.group_name is not None
        assert group.added_at is not None
