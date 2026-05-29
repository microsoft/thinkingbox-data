# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for the workday_api.get_employee tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.workday_api_get_employee import (
    WorkdayGetEmployeeTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestWorkdayGetEmployee:
    @pytest.fixture
    def workday_get_employee_tool(self):
        """Create an instance of WorkdayGetEmployeeTool."""
        return WorkdayGetEmployeeTool()

    @pytest.mark.anyio
    async def test_get_employee_success(self, workday_get_employee_tool, db):
        """Test retrieving a complete employee profile."""
        # Arrange
        request_data = {"email": "marcus.thompson@vdb.com"}

        # Act
        result = await workday_get_employee_tool.run_with_validation(db, request_data)

        # Assert
        assert result["employee_id"] == "WD-847291"
        assert result["email"] == "marcus.thompson@vdb.com"
        assert result["full_name"] == "Marcus Thompson"
        assert result["level"] == 4
        assert result["department"] == "product_engineering"
        assert result["role"] == "Senior Software Engineer"
        assert result["office_location"] == "sf"
        assert result["start_date"] == "2021-09-15T00:00:00Z"
        assert result["manager_id"] == "WD-681453"
        assert result["employment_status"] == "active"
        assert result["is_contractor"] is False

    @pytest.mark.anyio
    async def test_get_employee_on_leave(self, workday_get_employee_tool, db):
        """Test profile for employee on leave."""
        # Arrange
        request_data = {"email": "kevin.miller@vdb.com"}

        # Act
        result = await workday_get_employee_tool.run_with_validation(db, request_data)

        # Assert
        assert result["employment_status"] == "on_leave"
        assert result["office_location"] == "remote"

    @pytest.mark.anyio
    async def test_get_employee_not_found(self, workday_get_employee_tool, db):
        """Test retrieving a non-existing employee raises an error."""
        # Arrange
        request_data = {"email": "nonexistent@vdb.com"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="No employee found"):
            await workday_get_employee_tool.run_with_validation(db, request_data)

    @pytest.mark.anyio
    async def test_get_employee_contractor(self, workday_get_employee_tool, db):
        """Test profile for contractor."""
        # Arrange
        request_data = {"email": "olivia.moore@vdb.com"}

        # Act
        result = await workday_get_employee_tool.run_with_validation(db, request_data)

        # Assert
        assert result["is_contractor"] is True
        assert result["department"] == "customer_support"
