# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for mavenlink_api master tool."""

from datetime import datetime

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.mavenlink.models import (
    AssignmentStatus,
    EmployeeAssignment,
    EngagementStatus,
    MvEngagement,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.mavenlink.tools.api import (
    MavenlinkApiTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)


class TestMavenlinkApi:
    @pytest.fixture
    def test_db(self):
        """Create a test database with engagements and assignments."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "mv_engagements": MvEngagement,
            "employee_assignments": EmployeeAssignment,
        }
        db._model_cls_to_stem = {
            MvEngagement: "mv_engagements",
            EmployeeAssignment: "employee_assignments",
        }

        # Create test engagements
        engagement1 = MvEngagement(
            engagement_code="ENG-0012345",
            status=EngagementStatus.ACTIVE,
            start_date=datetime(2024, 1, 15),
            end_date=datetime(2024, 12, 31),
            senior_manager_email="sarah.johnson@msg.com",
        )

        engagement2 = MvEngagement(
            engagement_code="ENG-0023456",
            status=EngagementStatus.ACTIVE,
            start_date=datetime(2024, 3, 1),
            end_date=datetime(2024, 8, 31),
            senior_manager_email="michael.chen@msg.com",
        )

        engagement3 = MvEngagement(
            engagement_code="ENG-0034567",
            status=EngagementStatus.PIPELINE,
            start_date=datetime(2025, 1, 1),
            end_date=None,
            senior_manager_email="emily.rodriguez@msg.com",
        )

        # Create test assignments
        assignment1 = EmployeeAssignment(
            id="ASN-0012345",
            employee_email="john.smith@msg.com",
            engagement_code="ENG-0012345",
            assignment_status=AssignmentStatus.ACTIVE,
            start_date=datetime(2024, 1, 15),
            end_date=datetime(2024, 12, 31),
            senior_manager_email="sarah.johnson@msg.com",
        )

        assignment2 = EmployeeAssignment(
            id="ASN-0023456",
            employee_email="john.smith@msg.com",
            engagement_code="ENG-0023456",
            assignment_status=AssignmentStatus.BOOKED,
            start_date=datetime(2024, 3, 1),
            end_date=datetime(2024, 8, 31),
            senior_manager_email="michael.chen@msg.com",
        )

        assignment3 = EmployeeAssignment(
            id="ASN-0034567",
            employee_email="alice.wilson@msg.com",
            engagement_code="ENG-0012345",
            assignment_status=AssignmentStatus.ACTIVE,
            start_date=datetime(2024, 1, 15),
            end_date=None,
            senior_manager_email="sarah.johnson@msg.com",
        )

        db._store = {
            MvEngagement: [engagement1, engagement2, engagement3],
            EmployeeAssignment: [assignment1, assignment2, assignment3],
        }
        return db

    @pytest.fixture
    def mavenlink_tool(self):
        """Create an instance of the Mavenlink API tool."""
        return MavenlinkApiTool()

    # Tests for get_engagement action
    @pytest.mark.anyio
    async def test_get_engagement_success(self, mavenlink_tool, test_db):
        """Test successful engagement retrieval."""
        # Arrange
        request_data = {"action": "get_engagement", "engagement_code": "ENG-0012345"}

        # Act
        result = await mavenlink_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("engagement_data") is not None
        engagement = result["engagement_data"]
        assert engagement["engagement_code"] == "ENG-0012345"
        assert engagement["status"] == "active"
        assert engagement["start_date"] == "2024-01-15T00:00:00"
        assert engagement["end_date"] == "2024-12-31T00:00:00"
        assert engagement["senior_manager_email"] == "sarah.johnson@msg.com"

    @pytest.mark.anyio
    async def test_get_engagement_with_null_end_date(self, mavenlink_tool, test_db):
        """Test engagement retrieval with null end date."""
        # Arrange
        request_data = {"action": "get_engagement", "engagement_code": "ENG-0034567"}

        # Act
        result = await mavenlink_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("engagement_data") is not None
        engagement = result["engagement_data"]
        assert engagement["engagement_code"] == "ENG-0034567"
        assert engagement["status"] == "pipeline"
        assert engagement.get("end_date") is None

    @pytest.mark.anyio
    async def test_get_engagement_not_found(self, mavenlink_tool, test_db):
        """Test error when engagement not found."""
        # Arrange
        request_data = {"action": "get_engagement", "engagement_code": "ENG-9999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Engagement not found"):
            await mavenlink_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_engagement_missing_code(self, mavenlink_tool, test_db):
        """Test error when engagement_code is missing."""
        # Arrange
        request_data = {"action": "get_engagement"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: engagement_code"
        ):
            await mavenlink_tool.run_with_validation(test_db, request_data)

    # Tests for get_employee_assignments action
    @pytest.mark.anyio
    async def test_get_employee_assignments_success(self, mavenlink_tool, test_db):
        """Test successful retrieval of employee assignments."""
        # Arrange
        request_data = {
            "action": "get_employee_assignments",
            "email": "john.smith@msg.com",
        }

        # Act
        result = await mavenlink_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("assignments") is not None
        assignments = result["assignments"]
        assert len(assignments) == 2
        # Check first assignment
        assert assignments[0]["engagement_code"] == "ENG-0012345"
        assert assignments[0]["assignment_status"] == "active"
        assert assignments[0]["senior_manager_email"] == "sarah.johnson@msg.com"
        # Check second assignment
        assert assignments[1]["engagement_code"] == "ENG-0023456"
        assert assignments[1]["assignment_status"] == "booked"

    @pytest.mark.anyio
    async def test_get_employee_assignments_empty_result(self, mavenlink_tool, test_db):
        """Test retrieval when employee has no assignments."""
        # Arrange
        request_data = {
            "action": "get_employee_assignments",
            "email": "noassignments@msg.com",
        }

        # Act
        result = await mavenlink_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("assignments") is not None
        assert len(result["assignments"]) == 0

    @pytest.mark.anyio
    async def test_get_employee_assignments_missing_email(
        self, mavenlink_tool, test_db
    ):
        """Test error when email is missing."""
        # Arrange
        request_data = {"action": "get_employee_assignments"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await mavenlink_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_employee_assignments_all_fields_present(
        self, mavenlink_tool, test_db
    ):
        """Test that all fields are present in assignment output."""
        # Arrange
        request_data = {
            "action": "get_employee_assignments",
            "email": "alice.wilson@msg.com",
        }

        # Act
        result = await mavenlink_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("assignments") is not None
        assignments = result["assignments"]
        assert len(assignments) == 1
        assignment = assignments[0]
        assert "engagement_code" in assignment
        assert "assignment_status" in assignment
        assert "start_date" in assignment
        # Note: end_date may not be present if it's None (Pydantic default behavior)
        assert "senior_manager_email" in assignment

    # Tests for validate_engagement_code action
    @pytest.mark.anyio
    async def test_validate_engagement_code_valid(self, mavenlink_tool, test_db):
        """Test validation of existing engagement code."""
        # Arrange
        request_data = {
            "action": "validate_engagement_code",
            "engagement_code": "ENG-0012345",
        }

        # Act
        result = await mavenlink_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("valid") is True

    @pytest.mark.anyio
    async def test_validate_engagement_code_invalid(self, mavenlink_tool, test_db):
        """Test validation of non-existing engagement code."""
        # Arrange
        request_data = {
            "action": "validate_engagement_code",
            "engagement_code": "ENG-9999999",
        }

        # Act
        result = await mavenlink_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("valid") is False

    @pytest.mark.anyio
    async def test_validate_engagement_code_missing_code(self, mavenlink_tool, test_db):
        """Test error when engagement_code is missing."""
        # Arrange
        request_data = {"action": "validate_engagement_code"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: engagement_code"
        ):
            await mavenlink_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_validate_engagement_code_ignores_status(
        self, mavenlink_tool, test_db
    ):
        """Test that validation checks existence regardless of status."""
        # Arrange - pipeline status engagement
        request_data = {
            "action": "validate_engagement_code",
            "engagement_code": "ENG-0034567",
        }

        # Act
        result = await mavenlink_tool.run_with_validation(test_db, request_data)

        # Assert - should be valid regardless of pipeline status
        assert result.get("valid") is True

    # Test for invalid action
    @pytest.mark.anyio
    async def test_invalid_action(self, mavenlink_tool, test_db):
        """Test error with invalid action."""
        # Arrange
        request_data = {"action": "invalid_action"}

        # Act & Assert
        # Pydantic validates enum before our code, so expect input validation error
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await mavenlink_tool.run_with_validation(test_db, request_data)

    # Test for empty database
    @pytest.mark.anyio
    async def test_get_engagement_empty_database(self, mavenlink_tool):
        """Test get_engagement with empty database."""
        # Arrange
        empty_db = InMemoryDatabase.__new__(InMemoryDatabase)
        empty_db._stem_to_model_cls = {"mv_engagements": MvEngagement}
        empty_db._model_cls_to_stem = {MvEngagement: "mv_engagements"}
        empty_db._store = {MvEngagement: []}

        request_data = {"action": "get_engagement", "engagement_code": "ENG-0012345"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Engagement not found"):
            await mavenlink_tool.run_with_validation(empty_db, request_data)

    @pytest.mark.anyio
    async def test_get_employee_assignments_empty_database(self, mavenlink_tool):
        """Test get_employee_assignments with empty database."""
        # Arrange
        empty_db = InMemoryDatabase.__new__(InMemoryDatabase)
        empty_db._stem_to_model_cls = {"employee_assignments": EmployeeAssignment}
        empty_db._model_cls_to_stem = {EmployeeAssignment: "employee_assignments"}
        empty_db._store = {EmployeeAssignment: []}

        request_data = {
            "action": "get_employee_assignments",
            "email": "test@msg.com",
        }

        # Act
        result = await mavenlink_tool.run_with_validation(empty_db, request_data)

        # Assert
        assert result.get("assignments") is not None
        assert len(result["assignments"]) == 0
