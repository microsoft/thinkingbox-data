# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.okta_api_add_to_group import (
    OktaAddToGroupInput,
    OktaAddToGroupTool,
)


@pytest.mark.anyio
async def test_add_to_group_success(db):
    """Test successful addition of user to group"""
    tool = OktaAddToGroupTool()
    input_data = OktaAddToGroupInput(
        email="michael.rodriguez@vdb.com", group_name="managers"
    )

    result = await tool.run(db, input_data)

    assert result.membership_id.startswith("OGM-")


@pytest.mark.anyio
async def test_add_to_group_already_member(db):
    """Test adding user to group where they are already a member"""
    tool = OktaAddToGroupTool()
    input_data = OktaAddToGroupInput(
        email="marcus.thompson@vdb.com", group_name="engineers"
    )

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, input_data)

    assert "already" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_add_to_group_employee_not_found(db):
    """Test adding non-existent employee to group"""
    tool = OktaAddToGroupTool()
    input_data = OktaAddToGroupInput(
        email="nonexistent@vdb.com", group_name="engineers"
    )

    with pytest.raises(Exception) as exc_info:
        await tool.run(db, input_data)

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_add_to_group_contractor(db):
    """Test adding contractor to group"""
    tool = OktaAddToGroupTool()
    input_data = OktaAddToGroupInput(
        email="olivia.moore@vdb.com",  # Olivia Moore - contractor
        group_name="engineers",
    )

    # Contractors can be added to groups
    result = await tool.run(db, input_data)

    assert result.membership_id.startswith("OGM-")


@pytest.mark.anyio
async def test_add_to_group_creates_valid_membership(db):
    """Test that valid group membership record is created"""
    tool = OktaAddToGroupTool()
    input_data = OktaAddToGroupInput(
        email="david.kim@vdb.com", group_name="support_team"
    )

    result = await tool.run(db, input_data)

    assert result.membership_id.startswith("OGM-")
    # Verify that user can now get their groups
    from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.okta_api_get_user_groups import (
        OktaGetUserGroupsInput,
        OktaGetUserGroupsTool,
    )

    get_groups_tool = OktaGetUserGroupsTool()
    get_groups_input = OktaGetUserGroupsInput(email="david.kim@vdb.com")
    groups_result = await get_groups_tool.run(db, get_groups_input)

    group_names = [g.group_name for g in groups_result.groups]
    assert "support_team" in group_names
