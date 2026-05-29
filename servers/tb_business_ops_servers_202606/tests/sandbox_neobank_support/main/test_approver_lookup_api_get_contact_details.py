# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for approver_lookup_api_get_contact_details tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.approver_lookup_api_get_contact_details import (
    GetContactDetailsTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestApproverLookupGetContactDetails:
    @pytest.fixture
    def get_contact_details_tool(self):
        """Create an instance of the Get Contact Details tool."""
        return GetContactDetailsTool()

    @pytest.mark.anyio
    async def test_get_contact_details_available(self, get_contact_details_tool, db):
        """Test contact details for available approver."""
        # Arrange
        request_data = {
            "email": "sarah.jones@vdb.com",
        }

        # Act
        result = await get_contact_details_tool.run_with_validation(db, request_data)

        # Assert
        assert result["name"] == "Sarah Jones"
        assert result["availability_status"] == "available"
        assert result.get("backup_approver_email") is None

    @pytest.mark.anyio
    async def test_get_contact_details_on_leave(self, get_contact_details_tool, db):
        """Test contact details for approver on leave."""
        # Arrange
        request_data = {
            "email": "kevin.miller@vdb.com",
        }

        # Act
        result = await get_contact_details_tool.run_with_validation(db, request_data)

        # Assert
        assert result["name"] == "Kevin Miller"
        assert result["availability_status"] == "on_leave"
        # Should have backup approver (their manager)
        assert result["backup_approver_email"] == "sarah.jones@vdb.com"

    @pytest.mark.anyio
    async def test_get_contact_details_departing(self, get_contact_details_tool, db):
        """Test contact details for departing employee - should be available."""
        # Arrange - Find an employee with departing status or test with existing data
        # According to the mapping: departing → available
        from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
            Department,
            Employee,
            EmploymentStatus,
            OfficeLocation,
        )

        # Add a departing employee to the database for testing
        departing_emp = Employee(
            id="WD-999999",
            email="departing.employee@vdb.com",
            full_name="Departing Employee",
            level=5,
            department=Department.IT_SECURITY,
            role="Senior Engineer",
            office_location=OfficeLocation.SF,
            start_date="2020-01-01T00:00:00Z",
            manager_id="WD-753918",
            employment_status=EmploymentStatus.DEPARTING,
            is_contractor=False,
        )
        db.create(departing_emp)

        request_data = {
            "email": "departing.employee@vdb.com",
        }

        # Act
        result = await get_contact_details_tool.run_with_validation(db, request_data)

        # Assert
        assert result["name"] == "Departing Employee"
        assert result["availability_status"] == "available"
        assert result.get("backup_approver_email") is None

    @pytest.mark.anyio
    async def test_get_contact_details_employee_not_found(
        self, get_contact_details_tool, db
    ):
        """Test that nonexistent approver raises error."""
        # Arrange
        request_data = {
            "email": "nonexistent@vdb.com",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Approver not found"):
            await get_contact_details_tool.run_with_validation(db, request_data)

    @pytest.mark.anyio
    async def test_get_contact_details_missing_email(
        self, get_contact_details_tool, db
    ):
        """Test that missing email raises validation error."""
        # Arrange
        request_data = {}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await get_contact_details_tool.run_with_validation(db, request_data)
