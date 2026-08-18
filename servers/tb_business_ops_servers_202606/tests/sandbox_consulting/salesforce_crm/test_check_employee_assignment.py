# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for salesforce_check_employee_assignment tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.mavenlink.models import (
    AssignmentStatus,
    EmployeeAssignment,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.salesforce_crm.tools.check_employee_assignment import (
    CheckEmployeeAssignmentTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
)


class TestCheckEmployeeAssignment:
    @pytest.fixture
    def test_db(self):
        """Create a test database with employee_assignments."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "employee_assignment": EmployeeAssignment,
        }
        db._model_cls_to_stem = {
            EmployeeAssignment: "employee_assignment",
        }

        # Create test assignments
        assignment1 = EmployeeAssignment(
            id="ASN-0012345",
            employee_email="john.smith@msg.com",
            engagement_code="ENG-0012345",
            assignment_status=AssignmentStatus.ACTIVE,
            start_date="2024-01-15T00:00:00Z",
            end_date="2024-12-31T00:00:00Z",
            senior_manager_email="sarah.johnson@msg.com",
        )

        assignment2 = EmployeeAssignment(
            id="ASN-0023456",
            employee_email="jane.doe@msg.com",
            engagement_code="ENG-0012345",
            assignment_status=AssignmentStatus.ACTIVE,
            start_date="2024-02-01T00:00:00Z",
            end_date="2024-12-31T00:00:00Z",
            senior_manager_email="sarah.johnson@msg.com",
        )

        assignment3 = EmployeeAssignment(
            id="ASN-0034567",
            employee_email="bob.taylor@msg.com",
            engagement_code="ENG-0034567",
            assignment_status=AssignmentStatus.BOOKED,
            start_date="2025-01-01T00:00:00Z",
            end_date=None,
            senior_manager_email="emily.rodriguez@msg.com",
        )

        db._store = {
            EmployeeAssignment: [assignment1, assignment2, assignment3],
        }
        return db

    @pytest.fixture
    def check_assignment_tool(self):
        """Create an instance of the check_employee_assignment tool."""
        return CheckEmployeeAssignmentTool()

    @pytest.mark.anyio
    async def test_check_assignment_success_active(
        self, check_assignment_tool, test_db
    ):
        """Test successful check with active assignment."""
        # Arrange
        request_data = {"email": "john.smith@msg.com", "engagement_code": "ENG-0012345"}

        # Act
        result = await check_assignment_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["assigned"] is True
        assert result["assignment_status"] == "active"
        assert result["start_date"] == "2024-01-15T00:00:00+00:00"
        assert result["end_date"] == "2024-12-31T00:00:00+00:00"

    @pytest.mark.anyio
    async def test_check_assignment_success_booked(
        self, check_assignment_tool, test_db
    ):
        """Test successful check with booked assignment."""
        # Arrange
        request_data = {"email": "bob.taylor@msg.com", "engagement_code": "ENG-0034567"}

        # Act
        result = await check_assignment_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["assigned"] is True
        assert result["assignment_status"] == "booked"
        assert result["start_date"] == "2025-01-01T00:00:00+00:00"
        assert result.get("end_date") is None

    @pytest.mark.anyio
    async def test_check_assignment_not_assigned(self, check_assignment_tool, test_db):
        """Test when employee is not assigned to engagement."""
        # Arrange
        request_data = {"email": "unknown@msg.com", "engagement_code": "ENG-0012345"}

        # Act
        result = await check_assignment_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["assigned"] is False
        assert result.get("assignment_status") is None
        assert result.get("start_date") is None
        assert result.get("end_date") is None

    @pytest.mark.anyio
    async def test_check_assignment_wrong_engagement(
        self, check_assignment_tool, test_db
    ):
        """Test when employee is assigned but to different engagement."""
        # Arrange
        request_data = {"email": "john.smith@msg.com", "engagement_code": "ENG-9999999"}

        # Act
        result = await check_assignment_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["assigned"] is False
        assert result.get("assignment_status") is None
        assert result.get("start_date") is None
        assert result.get("end_date") is None

    @pytest.mark.anyio
    async def test_check_assignment_empty_database(self, check_assignment_tool):
        """Test check with empty database."""
        # Arrange
        empty_db = InMemoryDatabase.__new__(InMemoryDatabase)
        empty_db._stem_to_model_cls = {"employee_assignment": EmployeeAssignment}
        empty_db._model_cls_to_stem = {EmployeeAssignment: "employee_assignment"}
        empty_db._store = {EmployeeAssignment: []}
        request_data = {"email": "john.smith@msg.com", "engagement_code": "ENG-0012345"}

        # Act
        result = await check_assignment_tool.run_with_validation(empty_db, request_data)

        # Assert
        assert result["assigned"] is False

    @pytest.mark.anyio
    async def test_check_assignment_multiple_assignments_same_engagement(
        self, check_assignment_tool, test_db
    ):
        """Test that correct assignment is returned when multiple exist for same engagement."""
        # Arrange
        request_data = {"email": "jane.doe@msg.com", "engagement_code": "ENG-0012345"}

        # Act
        result = await check_assignment_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["assigned"] is True
        assert result["assignment_status"] == "active"
        assert result["start_date"] == "2024-02-01T00:00:00+00:00"

    @pytest.mark.anyio
    async def test_check_assignment_all_fields_present(
        self, check_assignment_tool, test_db
    ):
        """Test that all expected fields are present in the output."""
        # Arrange
        request_data = {"email": "john.smith@msg.com", "engagement_code": "ENG-0012345"}

        # Act
        result = await check_assignment_tool.run_with_validation(test_db, request_data)

        # Assert - verify all expected fields are present
        assert "assigned" in result
        assert "assignment_status" in result
        assert "start_date" in result
        assert "end_date" in result
