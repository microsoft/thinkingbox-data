# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for approver_lookup_api_get_security_contact tool."""

import pytest
from ms_toloka_servers.toolslib.sandbox_neobank_support.main.tools.approver_lookup_api_get_security_contact import (
    GetApproverContactTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestApproverLookupGetSecurityContact:
    @pytest.fixture
    def get_approver_contact_tool(self):
        """Create an instance of the Get Approver Contact tool."""
        return GetApproverContactTool()

    @pytest.mark.anyio
    async def test_get_approver_contact_it_security_success(
        self, get_approver_contact_tool, db
    ):
        """Test successful approver contact lookup for it_security."""
        # Arrange
        request_data = {"required_approver": "it_security"}

        # Act
        result = await get_approver_contact_tool.run_with_validation(db, request_data)

        # Assert
        # Should return the highest-level employee from IT Security department
        assert result["contact_email"] == "amanda.lee@vdb.com"
        assert result["contact_name"] == "Amanda Lee"
        assert result["employee_id"] == "WD-753918"

    @pytest.mark.anyio
    async def test_get_approver_contact_finance_accounting_success(
        self, get_approver_contact_tool, db
    ):
        """Test successful approver contact lookup for finance_accounting."""
        # Arrange
        request_data = {"required_approver": "finance_accounting"}

        # Act
        result = await get_approver_contact_tool.run_with_validation(db, request_data)

        # Assert
        # Should return the highest-level employee from Finance Accounting department
        assert "contact_email" in result
        assert "contact_name" in result
        assert "employee_id" in result

    @pytest.mark.anyio
    async def test_get_approver_contact_compliance_risk_success(
        self, get_approver_contact_tool, db
    ):
        """Test successful approver contact lookup for compliance_risk."""
        # Arrange
        request_data = {"required_approver": "compliance_risk"}

        # Act
        result = await get_approver_contact_tool.run_with_validation(db, request_data)

        # Assert
        # Should return the highest-level employee from Compliance Risk department
        assert "contact_email" in result
        assert "contact_name" in result
        assert "employee_id" in result

    @pytest.mark.anyio
    async def test_get_approver_contact_invalid_department(
        self, get_approver_contact_tool, db
    ):
        """Test error when invalid department is provided."""
        # Arrange
        request_data = {"required_approver": "legal"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as exc_info:
            await get_approver_contact_tool.run_with_validation(db, request_data)
        assert "Invalid required_approver" in str(exc_info.value)
