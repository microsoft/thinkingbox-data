# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for workday_api master tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.workday.models import (
    ApproverAvailability,
    Employee,
    EmployeeLevel,
    OfficeLocation,
    OnboardingPhase,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.workday.tools.api import (
    WorkdayApiTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestWorkdayApi:
    @pytest.fixture
    def test_db(self):
        """Create a test database with employees."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "employee": Employee,
        }
        db._model_cls_to_stem = {
            Employee: "employee",
        }

        # Create test employees
        employee1 = Employee(
            email="john.smith@msg.com",
            name="John Smith",
            level=EmployeeLevel.SENIOR_CONSULTANT,
            office_location=OfficeLocation.NEW_YORK,
            start_date="2022-03-15T00:00:00Z",
            manager_email="sarah.johnson@msg.com",
            partner_email="richard.williams@msg.com",
            onboarding_phase=OnboardingPhase.COMPLETED,
            availability_status=ApproverAvailability.AVAILABLE,
            backup_approver_email="michael.chen@msg.com",
        )

        employee2 = Employee(
            email="jane.doe@msg.com",
            name="Jane Doe",
            level=EmployeeLevel.CONSULTANT,
            office_location=OfficeLocation.SAN_FRANCISCO,
            start_date="2023-06-01T00:00:00Z",
            manager_email="michael.chen@msg.com",
            partner_email="richard.williams@msg.com",
            onboarding_phase=OnboardingPhase.COMPLETED,
            availability_status=ApproverAvailability.AVAILABLE,
            backup_approver_email=None,
        )

        employee3 = Employee(
            email="alice.wilson@msg.com",
            name="Alice Wilson",
            level=EmployeeLevel.ANALYST,
            office_location=OfficeLocation.CHICAGO,
            start_date="2024-01-08T00:00:00Z",
            manager_email="sarah.johnson@msg.com",
            partner_email=None,
            onboarding_phase=OnboardingPhase.DAY_7_30_ENGAGEMENT_RAMP,
            availability_status=ApproverAvailability.AVAILABLE,
            backup_approver_email="emily.rodriguez@msg.com",
        )

        employee4 = Employee(
            email="michael.chen@msg.com",
            name="Michael Chen",
            level=EmployeeLevel.MANAGER,
            office_location=OfficeLocation.SAN_FRANCISCO,
            start_date="2019-09-01T00:00:00Z",
            manager_email="richard.williams@msg.com",
            partner_email="richard.williams@msg.com",
            onboarding_phase=OnboardingPhase.COMPLETED,
            availability_status=ApproverAvailability.ON_LEAVE,
            backup_approver_email="sarah.johnson@msg.com",
        )

        db._store = {
            Employee: [employee1, employee2, employee3, employee4],
        }
        return db

    @pytest.fixture
    def workday_tool(self):
        """Create an instance of the workday_api tool."""
        return WorkdayApiTool()

    @pytest.mark.anyio
    async def test_get_employee_success(self, workday_tool, test_db):
        """Test successful retrieval of employee data."""
        # Arrange
        request_data = {"action": "get_employee", "email": "john.smith@msg.com"}

        # Act
        result = await workday_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "employee_data" in result
        emp = result["employee_data"]
        assert emp["email"] == "john.smith@msg.com"
        assert emp["name"] == "John Smith"
        assert emp["level"] == "Senior Consultant"
        assert emp["office_location"] == "New York"
        assert emp["start_date"] == "2022-03-15T00:00:00+00:00"
        assert emp["manager_email"] == "sarah.johnson@msg.com"
        assert emp["partner_email"] == "richard.williams@msg.com"
        assert emp["onboarding_phase"] == "completed"
        assert emp["availability_status"] == "available"
        assert emp["backup_approver_email"] == "michael.chen@msg.com"

    @pytest.mark.anyio
    async def test_get_employee_with_nulls(self, workday_tool, test_db):
        """Test retrieval of employee with optional fields as null."""
        # Arrange
        request_data = {"action": "get_employee", "email": "jane.doe@msg.com"}

        # Act
        result = await workday_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "employee_data" in result
        emp = result["employee_data"]
        assert emp["email"] == "jane.doe@msg.com"
        assert emp["name"] == "Jane Doe"
        assert emp.get("backup_approver_email") is None

    @pytest.mark.anyio
    async def test_get_employee_onboarding_phase(self, workday_tool, test_db):
        """Test retrieval of employee with specific onboarding phase."""
        # Arrange
        request_data = {"action": "get_employee", "email": "alice.wilson@msg.com"}

        # Act
        result = await workday_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "employee_data" in result
        emp = result["employee_data"]
        assert emp["onboarding_phase"] == "day_7_30_engagement_ramp"
        assert emp.get("partner_email") is None

    @pytest.mark.anyio
    async def test_get_employee_on_leave(self, workday_tool, test_db):
        """Test retrieval of employee with on_leave status."""
        # Arrange
        request_data = {"action": "get_employee", "email": "michael.chen@msg.com"}

        # Act
        result = await workday_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "employee_data" in result
        emp = result["employee_data"]
        assert emp["availability_status"] == "on_leave"
        assert emp["backup_approver_email"] == "sarah.johnson@msg.com"

    @pytest.mark.anyio
    async def test_get_employee_not_found(self, workday_tool, test_db):
        """Test error when employee not found."""
        # Arrange
        request_data = {"action": "get_employee", "email": "nonexistent@msg.com"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Employee not found"):
            await workday_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_employee_missing_email(self, workday_tool, test_db):
        """Test error when email is missing."""
        # Arrange
        request_data = {"action": "get_employee"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await workday_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_invalid_action(self, workday_tool, test_db):
        """Test error when invalid action is provided."""
        # Arrange
        request_data = {"action": "invalid_action", "email": "john.smith@msg.com"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await workday_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_employee_empty_database(self, workday_tool):
        """Test get_employee with empty database."""
        # Arrange
        empty_db = InMemoryDatabase.__new__(InMemoryDatabase)
        empty_db._stem_to_model_cls = {"employee": Employee}
        empty_db._model_cls_to_stem = {Employee: "employee"}
        empty_db._store = {Employee: []}
        request_data = {"action": "get_employee", "email": "john.smith@msg.com"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Employee not found"):
            await workday_tool.run_with_validation(empty_db, request_data)

    @pytest.mark.anyio
    async def test_get_employee_all_fields_present(self, workday_tool, test_db):
        """Test that all expected fields are present in the output."""
        # Arrange
        request_data = {"action": "get_employee", "email": "john.smith@msg.com"}

        # Act
        result = await workday_tool.run_with_validation(test_db, request_data)

        # Assert - verify all expected fields are present
        assert "employee_data" in result
        emp = result["employee_data"]
        assert "email" in emp
        assert "name" in emp
        assert "level" in emp
        assert "office_location" in emp
        assert "start_date" in emp
        assert "manager_email" in emp
        assert "partner_email" in emp
        assert "onboarding_phase" in emp
        assert "availability_status" in emp
        assert "backup_approver_email" in emp
