# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for the workday_api.get_org_structure tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.workday_api_get_org_structure import (
    WorkdayGetOrgStructureTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    Tool,
)


class TestWorkdayGetOrgStructure:
    @pytest.fixture
    def workday_get_org_structure_tool(self):
        """Create an instance of WorkdayGetOrgStructureTool."""
        return WorkdayGetOrgStructureTool()

    @pytest.mark.anyio
    async def test_get_org_structure_success(self, workday_get_org_structure_tool, db):
        """Test retrieving direct reports for a manager."""
        # Arrange
        request_data = {"manager_email": "sarah.jones@vdb.com"}

        # Act
        result = await workday_get_org_structure_tool.run_with_validation(
            db, request_data
        )

        # Assert - Sarah has 4 direct reports
        assert len(result["direct_reports"]) == 6

        # Check that expected employees are in the results
        emails = [report["email"] for report in result["direct_reports"]]
        assert "marcus.thompson@vdb.com" in emails
        assert "emma.wilson@vdb.com" in emails
        assert "david.kim@vdb.com" in emails
        assert "kevin.miller@vdb.com" in emails

    @pytest.mark.anyio
    async def test_get_org_structure_ceo_multiple_reports(
        self, workday_get_org_structure_tool, db
    ):
        """Test CEO has multiple direct reports across departments."""
        # Arrange
        request_data = {"manager_email": "lisa.chen@vdb.com"}

        # Act
        result = await workday_get_org_structure_tool.run_with_validation(
            db, request_data
        )

        # Assert - CEO has 6 direct reports
        assert len(result["direct_reports"]) == 6

        # Check we have key managers reporting to CEO
        emails = [report["email"] for report in result["direct_reports"]]
        assert "michael.rodriguez@vdb.com" in emails  # VP of Engineering
        assert "maria.garcia@vdb.com" in emails  # Customer Support Manager
        assert "jennifer.brown@vdb.com" in emails  # Compliance Director

    @pytest.mark.anyio
    async def test_get_org_structure_no_reports(
        self, workday_get_org_structure_tool, db
    ):
        """Test employee with no direct reports returns empty list."""
        # Arrange
        request_data = {"manager_email": "marcus.thompson@vdb.com"}

        # Act
        result = await workday_get_org_structure_tool.run_with_validation(
            db, request_data
        )

        # Assert
        assert len(result["direct_reports"]) == 0

    @pytest.mark.anyio
    async def test_get_org_structure_contractor_no_reports(
        self, workday_get_org_structure_tool, db
    ):
        """Test contractor with no direct reports returns empty list."""
        # Arrange
        request_data = {"manager_email": "olivia.moore@vdb.com"}

        # Act
        result = await workday_get_org_structure_tool.run_with_validation(
            db, request_data
        )

        # Assert
        assert len(result["direct_reports"]) == 0

    @pytest.mark.anyio
    async def test_get_org_structure_not_found(
        self, workday_get_org_structure_tool, db
    ):
        """Test retrieving org structure for non-existing employee raises an error."""
        # Arrange
        request_data = {"manager_email": "nonexistent@vdb.com"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Manager not found"):
            await workday_get_org_structure_tool.run_with_validation(db, request_data)
