# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for approval_api_create_request tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
    ApprovalRequest,
    ApprovalRequestStatus,
    ApprovalUrgency,
)
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.approval_api_create_request import (
    CreateRequestTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    Tool,
)


class TestApprovalCreateRequest:
    @pytest.fixture
    def approval_tool(self):
        """Create an instance of the Create Request tool."""
        return CreateRequestTool()

    @pytest.mark.anyio
    async def test_create_request_success(self, approval_tool, db):
        """Test successful approval request creation."""
        # Arrange
        request_data = {
            "request_type": "access_request",
            "requester_email": "marcus.thompson@vdb.com",
            "approver_email": "sarah.jones@vdb.com",
            "details": "Requesting Snowflake read-only access for Q4 reporting project",
        }

        # Act
        result = await approval_tool.run_with_validation(db, request_data)

        # Assert
        assert result.get("approval_request_id") is not None
        assert result["approval_request_id"].startswith("APR-")
        assert result["status"] == "pending"

        # Verify approval was created in database
        approvals = db.get_all(ApprovalRequest)
        new_approvals = [a for a in approvals if a.requester_id == "WD-847291"]
        assert len(new_approvals) >= 1

    @pytest.mark.anyio
    async def test_create_request_with_urgency(self, approval_tool, db):
        """Test approval request creation with urgency specified."""
        # Arrange
        request_data = {
            "request_type": "access_request",
            "requester_email": "marcus.thompson@vdb.com",
            "approver_email": "sarah.jones@vdb.com",
            "details": "Urgent access needed",
            "urgency": "urgent",
        }

        # Act
        result = await approval_tool.run_with_validation(db, request_data)

        # Assert
        assert result.get("approval_request_id") is not None
        approvals = db.get_all(ApprovalRequest)
        new_approval = [a for a in approvals if a.id == result["approval_request_id"]]
        assert len(new_approval) == 1
        assert new_approval[0].urgency == ApprovalUrgency.URGENT

    @pytest.mark.anyio
    async def test_create_request_with_ticket_id(self, approval_tool, db):
        """Test approval request creation with ticket ID."""
        # Arrange
        request_data = {
            "request_type": "access_request",
            "requester_email": "marcus.thompson@vdb.com",
            "approver_email": "sarah.jones@vdb.com",
            "details": "Access needed",
            "ticket_id": "TCK-99999999",
        }

        # Act
        result = await approval_tool.run_with_validation(db, request_data)

        # Assert
        approvals = db.get_all(ApprovalRequest)
        new_approval = [a for a in approvals if a.ticket_id == "TCK-99999999"]
        assert len(new_approval) == 1

    @pytest.mark.anyio
    async def test_create_request_requester_not_found(self, approval_tool, db):
        """Test that nonexistent requester raises error."""
        # Arrange
        request_data = {
            "request_type": "access_request",
            "requester_email": "nonexistent@vdb.com",
            "approver_email": "sarah.jones@vdb.com",
            "details": "Request",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Requester not found"):
            await approval_tool.run_with_validation(db, request_data)

    @pytest.mark.anyio
    async def test_create_request_approver_not_found(self, approval_tool, db):
        """Test that nonexistent approver raises error."""
        # Arrange
        request_data = {
            "request_type": "access_request",
            "requester_email": "marcus.thompson@vdb.com",
            "approver_email": "nonexistent@vdb.com",
            "details": "Request",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Approver not found"):
            await approval_tool.run_with_validation(db, request_data)

    @pytest.mark.anyio
    async def test_create_request_missing_required_fields(self, approval_tool, db):
        """Test that missing required fields raises validation error."""
        # Missing details
        request_data = {
            "request_type": "access_request",
            "requester_email": "marcus.thompson@vdb.com",
            "approver_email": "sarah.jones@vdb.com",
        }

        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await approval_tool.run_with_validation(db, request_data)

    @pytest.mark.anyio
    async def test_create_request_default_urgency(self, approval_tool, db):
        """Test that default urgency is STANDARD when not provided."""
        # Arrange
        request_data = {
            "request_type": "access_request",
            "requester_email": "marcus.thompson@vdb.com",
            "approver_email": "sarah.jones@vdb.com",
            "details": "Request",
        }

        # Act
        result = await approval_tool.run_with_validation(db, request_data)

        # Assert
        approvals = db.get_all(ApprovalRequest)
        new_approval = [a for a in approvals if a.id == result["approval_request_id"]]
        assert len(new_approval) == 1
        assert new_approval[0].urgency == ApprovalUrgency.STANDARD

    @pytest.mark.anyio
    async def test_create_request_status_is_pending(self, approval_tool, db):
        """Test that new approval requests are created with status=pending."""
        # Arrange
        request_data = {
            "request_type": "access_request",
            "requester_email": "marcus.thompson@vdb.com",
            "approver_email": "sarah.jones@vdb.com",
            "details": "Request",
        }

        # Act
        result = await approval_tool.run_with_validation(db, request_data)

        # Assert
        approvals = db.get_all(ApprovalRequest)
        new_approval = [a for a in approvals if a.id == result["approval_request_id"]]
        assert len(new_approval) == 1
        assert new_approval[0].status == ApprovalRequestStatus.PENDING
