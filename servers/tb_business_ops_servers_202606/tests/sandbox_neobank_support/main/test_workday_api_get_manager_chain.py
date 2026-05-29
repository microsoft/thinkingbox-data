# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for the workday_api.get_manager_chain tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.workday_api_get_manager_chain import (
    WorkdayGetManagerChainTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestWorkdayGetManagerChain:
    @pytest.fixture
    def workday_get_manager_chain_tool(self):
        """Create an instance of WorkdayGetManagerChainTool."""
        return WorkdayGetManagerChainTool()

    @pytest.mark.anyio
    async def test_get_manager_chain_success(self, workday_get_manager_chain_tool, db):
        """Test retrieving complete manager chain."""
        # Arrange
        request_data = {"email": "marcus.thompson@vdb.com"}

        # Act
        result = await workday_get_manager_chain_tool.run_with_validation(
            db, request_data
        )

        # Assert
        assert len(result["manager_chain"]) == 3

        # Direct manager
        assert result["manager_chain"][0]["employee_id"] == "WD-681453"
        assert result["manager_chain"][0]["email"] == "sarah.jones@vdb.com"
        assert result["manager_chain"][0]["full_name"] == "Sarah Jones"
        assert result["manager_chain"][0]["level"] == 7
        assert result["manager_chain"][0]["role"] == "Engineering Manager"

        # Skip-level manager (VP)
        assert result["manager_chain"][1]["employee_id"] == "WD-573926"
        assert result["manager_chain"][1]["email"] == "michael.rodriguez@vdb.com"
        assert result["manager_chain"][1]["level"] == 8

        # CEO
        assert result["manager_chain"][2]["employee_id"] == "WD-294817"
        assert result["manager_chain"][2]["email"] == "lisa.chen@vdb.com"
        assert result["manager_chain"][2]["level"] == 9

    @pytest.mark.anyio
    async def test_get_manager_chain_ceo_has_no_chain(
        self, workday_get_manager_chain_tool, db
    ):
        """Test that CEO with no manager returns empty chain."""
        # Arrange
        request_data = {"email": "lisa.chen@vdb.com"}

        # Act
        result = await workday_get_manager_chain_tool.run_with_validation(
            db, request_data
        )

        # Assert
        assert len(result["manager_chain"]) == 0

    @pytest.mark.anyio
    async def test_get_manager_chain_one_level(
        self, workday_get_manager_chain_tool, db
    ):
        """Test manager chain with only one level."""
        # Arrange
        request_data = {"email": "michael.rodriguez@vdb.com"}

        # Act
        result = await workday_get_manager_chain_tool.run_with_validation(
            db, request_data
        )

        # Assert
        assert len(result["manager_chain"]) == 1
        assert result["manager_chain"][0]["employee_id"] == "WD-294817"

    @pytest.mark.anyio
    async def test_get_manager_chain_not_found(
        self, workday_get_manager_chain_tool, db
    ):
        """Test retrieving manager chain for non-existing employee raises an error."""
        # Arrange
        request_data = {"email": "nonexistent@vdb.com"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Employee not found"):
            await workday_get_manager_chain_tool.run_with_validation(db, request_data)
