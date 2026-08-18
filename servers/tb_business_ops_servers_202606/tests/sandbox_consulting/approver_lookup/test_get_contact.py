# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for Approver Lookup Service get_contact tool."""

from datetime import datetime

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.approver_lookup.tools.get_contact import (
    ApproverLookupGetContactTool,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.workday.models import (
    ApproverAvailability,
    Employee,
    EmployeeLevel,
    OfficeLocation,
    OnboardingPhase,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)


class TestApproverLookupGetContactTool:
    """Test cases for Approver Lookup Get Contact tool."""

    @pytest.fixture
    def test_db(self):
        """Create a test database with sample employee data."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "employees": Employee,
        }
        db._model_cls_to_stem = {
            Employee: "employees",
        }

        # Create test employees
        employee1 = Employee(
            email="available.manager@msg.com",
            name="Available Manager",
            level=EmployeeLevel.MANAGER,
            office_location=OfficeLocation.NEW_YORK,
            start_date=datetime(2020, 1, 15),
            manager_email="senior.manager@msg.com",
            partner_email="partner@msg.com",
            onboarding_phase=OnboardingPhase.COMPLETED,
            availability_status=ApproverAvailability.AVAILABLE,
            backup_approver_email="backup.manager@msg.com",
        )
        employee2 = Employee(
            email="on.leave.manager@msg.com",
            name="On Leave Manager",
            level=EmployeeLevel.SENIOR_MANAGER,
            office_location=OfficeLocation.SAN_FRANCISCO,
            start_date=datetime(2018, 3, 1),
            manager_email="partner@msg.com",
            partner_email="partner@msg.com",
            onboarding_phase=OnboardingPhase.COMPLETED,
            availability_status=ApproverAvailability.ON_LEAVE,
            backup_approver_email="available.manager@msg.com",
        )
        employee3 = Employee(
            email="no.backup.manager@msg.com",
            name="No Backup Manager",
            level=EmployeeLevel.MANAGER,
            office_location=OfficeLocation.CHICAGO,
            start_date=datetime(2021, 6, 10),
            manager_email="senior.manager@msg.com",
            partner_email=None,
            onboarding_phase=OnboardingPhase.COMPLETED,
            availability_status=ApproverAvailability.AVAILABLE,
            backup_approver_email=None,
        )
        employee4 = Employee(
            email="partner@msg.com",
            name="Partner Executive",
            level=EmployeeLevel.PARTNER,
            office_location=OfficeLocation.NEW_YORK,
            start_date=datetime(2015, 1, 1),
            manager_email=None,
            partner_email=None,
            onboarding_phase=OnboardingPhase.COMPLETED,
            availability_status=ApproverAvailability.AVAILABLE,
            backup_approver_email=None,
        )

        db._store = {
            Employee: [employee1, employee2, employee3, employee4],
        }

        return db

    @pytest.fixture
    def get_contact_tool(self):
        """Create an instance of the get_contact tool."""
        return ApproverLookupGetContactTool()

    @pytest.mark.anyio
    async def test_get_contact_available_with_backup(self, get_contact_tool, test_db):
        """Test retrieving contact info for available approver with backup."""
        request_data = {
            "email": "available.manager@msg.com",
        }

        result = await get_contact_tool.run_with_validation(test_db, request_data)

        assert result["email"] == "available.manager@msg.com"
        assert result["name"] == "Available Manager"
        assert result["availability_status"] == "available"
        assert result["backup_approver_email"] == "backup.manager@msg.com"

    @pytest.mark.anyio
    async def test_get_contact_on_leave_with_backup(self, get_contact_tool, test_db):
        """Test retrieving contact info for approver on leave with backup."""
        request_data = {
            "email": "on.leave.manager@msg.com",
        }

        result = await get_contact_tool.run_with_validation(test_db, request_data)

        assert result["email"] == "on.leave.manager@msg.com"
        assert result["name"] == "On Leave Manager"
        assert result["availability_status"] == "on_leave"
        assert result["backup_approver_email"] == "available.manager@msg.com"

    @pytest.mark.anyio
    async def test_get_contact_available_no_backup(self, get_contact_tool, test_db):
        """Test retrieving contact info for approver without backup."""
        request_data = {
            "email": "no.backup.manager@msg.com",
        }

        result = await get_contact_tool.run_with_validation(test_db, request_data)

        assert result["email"] == "no.backup.manager@msg.com"
        assert result["name"] == "No Backup Manager"
        assert result["availability_status"] == "available"
        assert result.get("backup_approver_email") is None

    @pytest.mark.anyio
    async def test_get_contact_partner_level(self, get_contact_tool, test_db):
        """Test retrieving contact info for partner-level approver."""
        request_data = {
            "email": "partner@msg.com",
        }

        result = await get_contact_tool.run_with_validation(test_db, request_data)

        assert result["email"] == "partner@msg.com"
        assert result["name"] == "Partner Executive"
        assert result["availability_status"] == "available"
        assert result.get("backup_approver_email") is None

    @pytest.mark.anyio
    async def test_get_contact_not_found(self, get_contact_tool, test_db):
        """Test error when approver is not found."""
        request_data = {
            "email": "nonexistent@msg.com",
        }

        with pytest.raises(
            Tool.ExecutionError, match="Approver not found: nonexistent@msg.com"
        ):
            await get_contact_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_contact_missing_email(self, get_contact_tool, test_db):
        """Test error when email parameter is missing."""
        request_data = {}

        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await get_contact_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_contact_output_fields(self, get_contact_tool, test_db):
        """Test that all required output fields are present."""
        request_data = {
            "email": "available.manager@msg.com",
        }

        result = await get_contact_tool.run_with_validation(test_db, request_data)

        # Verify all required fields are present
        assert "email" in result
        assert "name" in result
        assert "availability_status" in result
        assert "backup_approver_email" in result

        # Verify field types
        assert isinstance(result["email"], str)
        assert isinstance(result["name"], str)
        assert isinstance(result["availability_status"], str)
        # backup_approver_email can be str or None

    @pytest.mark.anyio
    async def test_get_contact_backup_approver_email_handling(
        self, get_contact_tool, test_db
    ):
        """Test backup_approver_email field handling for different values."""
        # Test with backup present
        request_data1 = {
            "email": "available.manager@msg.com",
        }
        result1 = await get_contact_tool.run_with_validation(test_db, request_data1)
        assert result1["backup_approver_email"] == "backup.manager@msg.com"

        # Test without backup (None values are excluded from output by Pydantic)
        request_data2 = {
            "email": "no.backup.manager@msg.com",
        }
        result2 = await get_contact_tool.run_with_validation(test_db, request_data2)
        assert result2.get("backup_approver_email") is None
