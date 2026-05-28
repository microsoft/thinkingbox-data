# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for approval_create_request tool."""

import pytest
from sandbox_servers.toolslib.sandbox_consulting.approval.models import (
    ApprovalRequest,
    ApprovalRequestStatus,
    RequestType,
)
from sandbox_servers.toolslib.sandbox_consulting.approval.tools.create_request import (
    ApprovalCreateRequestTool,
)
from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestApprovalCreateRequest:
    @pytest.fixture
    def test_db(self):
        """Create a test database with approval requests."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "approval_requests": ApprovalRequest,
        }
        db._model_cls_to_stem = {
            ApprovalRequest: "approval_requests",
        }

        # Create test approval requests
        approval1 = ApprovalRequest(
            id="APR-1000001",
            request_type=RequestType.SOFTWARE_ACCESS,
            requester_email="jane.doe@msg.com",
            approver_email="senior.manager@msg.com",
            amount=1200,
            engagement_code="ENG-0012345",
            status=ApprovalRequestStatus.APPROVED,
        )

        approval2 = ApprovalRequest(
            id="APR-1000002",
            request_type=RequestType.HARDWARE_REPLACEMENT,
            requester_email="john.smith@msg.com",
            approver_email="manager@msg.com",
            amount=None,
            engagement_code="ENG-0067890",
            status=ApprovalRequestStatus.PENDING,
        )

        db._store = {
            ApprovalRequest: [approval1, approval2],
        }
        return db

    @pytest.fixture
    def approval_tool(self):
        """Create an instance of the Approval Create Request tool."""
        return ApprovalCreateRequestTool()

    @pytest.mark.anyio
    async def test_create_request_success(self, approval_tool, test_db):
        """Test successful approval request creation."""
        # Arrange
        request_data = {
            "request_type": "software_access",
            "requester_email": "new.user@msg.com",
            "approver_email": "manager@msg.com",
            "amount": 500,
            "engagement_code": "ENG-0012345",
        }

        # Act
        result = await approval_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("approval_id") is not None
        assert result["approval_id"].startswith("APR-2")

        # Verify approval was created
        approvals = test_db.get_all(ApprovalRequest)
        new_approval = [a for a in approvals if a.requester_email == "new.user@msg.com"]
        assert len(new_approval) == 1
        assert new_approval[0].request_type == RequestType.SOFTWARE_ACCESS
        assert new_approval[0].approver_email == "manager@msg.com"
        assert new_approval[0].amount == 500
        assert new_approval[0].engagement_code == "ENG-0012345"

    @pytest.mark.anyio
    async def test_create_request_without_optional_fields(self, approval_tool, test_db):
        """Test approval request creation without optional fields."""
        # Arrange
        request_data = {
            "request_type": "client_access",
            "requester_email": "user@msg.com",
            "approver_email": "partner@msg.com",
        }

        # Act
        result = await approval_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("approval_id") is not None

        # Verify approval was created without optional fields
        approvals = test_db.get_all(ApprovalRequest)
        new_approval = [a for a in approvals if a.requester_email == "user@msg.com"]
        assert len(new_approval) == 1
        assert new_approval[0].amount is None
        assert new_approval[0].engagement_code is None

    @pytest.mark.anyio
    async def test_create_request_all_request_types(self, approval_tool, test_db):
        """Test approval request creation with all request types."""
        request_types = [
            "software_access",
            "hardware_replacement",
            "client_access",
            "training_engagement_coordination",
            "training_cost",
            "expense_override",
            "travel",
            "document_access",
        ]

        for request_type in request_types:
            # Arrange
            request_data = {
                "request_type": request_type,
                "requester_email": f"{request_type}@msg.com",
                "approver_email": "manager@msg.com",
            }

            # Act
            result = await approval_tool.run_with_validation(test_db, request_data)

            # Assert
            assert result.get("approval_id") is not None

    @pytest.mark.anyio
    async def test_create_request_with_amount_only(self, approval_tool, test_db):
        """Test approval request with amount but no engagement code."""
        # Arrange
        request_data = {
            "request_type": "training_cost",
            "requester_email": "user@msg.com",
            "approver_email": "senior.manager@msg.com",
            "amount": 2500,
        }

        # Act
        result = await approval_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("approval_id") is not None

        # Verify approval was created
        approvals = test_db.get_all(ApprovalRequest)
        new_approval = [a for a in approvals if a.amount == 2500]
        assert len(new_approval) == 1
        assert new_approval[0].engagement_code is None

    @pytest.mark.anyio
    async def test_create_request_with_engagement_code_only(
        self, approval_tool, test_db
    ):
        """Test approval request with engagement code but no amount."""
        # Arrange
        request_data = {
            "request_type": "document_access",
            "requester_email": "user@msg.com",
            "approver_email": "partner@msg.com",
            "engagement_code": "ENG-0012345",
        }

        # Act
        result = await approval_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("approval_id") is not None

        # Verify approval was created
        approvals = test_db.get_all(ApprovalRequest)
        new_approval = [
            a
            for a in approvals
            if a.engagement_code == "ENG-0012345" and a.amount is None
        ]
        assert len(new_approval) >= 1

    @pytest.mark.anyio
    async def test_create_request_sequential_ids(self, approval_tool, test_db):
        """Test that approval IDs are generated sequentially."""
        # Arrange & Act - Create multiple requests
        approval_ids = []
        for i in range(3):
            request_data = {
                "request_type": "software_access",
                "requester_email": f"user{i}@msg.com",
                "approver_email": "manager@msg.com",
            }
            result = await approval_tool.run_with_validation(test_db, request_data)
            approval_ids.append(result["approval_id"])

        # Assert - IDs should be sequential
        assert len(set(approval_ids)) == 3  # All unique
        assert all(aid.startswith("APR-2") for aid in approval_ids)

    @pytest.mark.anyio
    async def test_create_request_empty_database(self, approval_tool):
        """Test approval request creation in empty database."""
        # Arrange - Empty database
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"approval_requests": ApprovalRequest}
        db._model_cls_to_stem = {ApprovalRequest: "approval_requests"}
        db._store = {ApprovalRequest: []}

        request_data = {
            "request_type": "software_access",
            "requester_email": "user@msg.com",
            "approver_email": "manager@msg.com",
        }

        # Act
        result = await approval_tool.run_with_validation(db, request_data)

        # Assert
        assert result["approval_id"] == "APR-2-000000"

    @pytest.mark.anyio
    async def test_create_request_missing_request_type(self, approval_tool, test_db):
        """Test that missing request_type raises validation error."""
        # Arrange
        request_data = {
            "requester_email": "user@msg.com",
            "approver_email": "manager@msg.com",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await approval_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_create_request_missing_requester_email(self, approval_tool, test_db):
        """Test that missing requester_email raises validation error."""
        # Arrange
        request_data = {
            "request_type": "software_access",
            "approver_email": "manager@msg.com",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await approval_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_create_request_missing_approver_email(self, approval_tool, test_db):
        """Test that missing approver_email raises validation error."""
        # Arrange
        request_data = {
            "request_type": "software_access",
            "requester_email": "user@msg.com",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await approval_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_create_request_invalid_request_type(self, approval_tool, test_db):
        """Test that invalid request_type raises validation error."""
        # Arrange
        request_data = {
            "request_type": "invalid_type",
            "requester_email": "user@msg.com",
            "approver_email": "manager@msg.com",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await approval_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_create_request_status_is_pending(self, approval_tool, test_db):
        """Test that new approval requests are created with status=pending."""
        # Arrange
        request_data = {
            "request_type": "software_access",
            "requester_email": "new.user@msg.com",
            "approver_email": "manager@msg.com",
            "amount": 500,
            "engagement_code": "ENG-0012345",
        }

        # Act
        result = await approval_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("approval_id") is not None

        # Verify the new approval has status=pending
        approvals = test_db.get_all(ApprovalRequest)
        new_approval = [a for a in approvals if a.id == result["approval_id"]]
        assert len(new_approval) == 1
        assert new_approval[0].status == ApprovalRequestStatus.PENDING
