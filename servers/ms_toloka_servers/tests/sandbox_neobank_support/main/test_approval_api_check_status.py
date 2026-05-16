# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for approval_api_check_status tool."""

import pytest
from ms_toloka_servers.toolslib.sandbox_neobank_support.main.tools.approval_api_check_status import (
    CheckStatusTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestApprovalCheckStatus:
    @pytest.fixture
    def check_status_tool(self):
        """Create an instance of the Check Status tool."""
        return CheckStatusTool()

    @pytest.mark.anyio
    async def test_check_status_pending(self, check_status_tool, db):
        """Test checking status of pending approval request."""
        # Arrange
        request_data = {
            "approval_request_id": "APR-05847293",
        }

        # Act
        result = await check_status_tool.run_with_validation(db, request_data)

        # Assert
        assert result["status"] == "pending"
        assert result.get("decided_at") is None
        assert result.get("approver_feedback") is None

    @pytest.mark.anyio
    async def test_check_status_approved(self, check_status_tool, db):
        """Test checking status of approved approval request."""
        # Arrange
        request_data = {
            "approval_request_id": "APR-19263847",
        }

        # Act
        result = await check_status_tool.run_with_validation(db, request_data)

        # Assert
        assert result["status"] == "approved"
        assert result["decided_at"] is not None
        assert result["approver_feedback"] == "Approved for 30-day access period"

    @pytest.mark.anyio
    async def test_check_status_rejected(self, check_status_tool, db):
        """Test checking status of rejected approval request."""
        # Arrange
        request_data = {
            "approval_request_id": "APR-34719582",
        }

        # Act
        result = await check_status_tool.run_with_validation(db, request_data)

        # Assert
        assert result["status"] == "rejected"
        assert result["decided_at"] is not None
        assert result["approver_feedback"] == "Current laptop is less than 2 years old"

    @pytest.mark.anyio
    async def test_check_status_not_found(self, check_status_tool, db):
        """Test that nonexistent approval request raises error."""
        # Arrange
        request_data = {
            "approval_request_id": "APR-99999999",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Approval request not found"):
            await check_status_tool.run_with_validation(db, request_data)

    @pytest.mark.anyio
    async def test_check_status_missing_id(self, check_status_tool, db):
        """Test that missing approval_request_id raises validation error."""
        # Arrange
        request_data = {}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await check_status_tool.run_with_validation(db, request_data)
