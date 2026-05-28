# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for approval_get_status tool."""

import pytest
from sandbox_servers.toolslib.sandbox_consulting.approval.models import (
    ApprovalRequest,
    ApprovalRequestStatus,
    RequestType,
)
from sandbox_servers.toolslib.sandbox_consulting.approval.tools.get_status import (
    ApprovalGetStatusTool,
)
from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestApprovalGetStatus:
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

        # Create test approval requests with various statuses
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

        approval3 = ApprovalRequest(
            id="APR-1000003",
            request_type=RequestType.SOFTWARE_ACCESS,
            requester_email="jane.doe@msg.com",
            approver_email="partner@msg.com",
            amount=500,
            engagement_code="ENG-0012345",
            status=ApprovalRequestStatus.PENDING,
        )

        approval4 = ApprovalRequest(
            id="APR-1000004",
            request_type=RequestType.TRAINING_COST,
            requester_email="bob.wilson@msg.com",
            approver_email="senior.manager@msg.com",
            amount=2500,
            engagement_code=None,
            status=ApprovalRequestStatus.REJECTED,
        )

        db._store = {
            ApprovalRequest: [approval1, approval2, approval3, approval4],
        }
        return db

    @pytest.fixture
    def get_status_tool(self):
        """Create an instance of the Approval Get Status tool."""
        return ApprovalGetStatusTool()

    @pytest.mark.anyio
    async def test_get_status_success(self, get_status_tool, test_db):
        """Test successful status retrieval by required fields."""
        # Arrange
        request_data = {
            "request_type": "software_access",
            "requester_email": "jane.doe@msg.com",
        }

        # Act
        result = await get_status_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("results") is not None
        assert len(result["results"]) == 2
        # Should return both software_access requests for jane.doe@msg.com
        approval_ids = {r["approval_id"] for r in result["results"]}
        assert "APR-1000001" in approval_ids
        assert "APR-1000003" in approval_ids

    @pytest.mark.anyio
    async def test_get_status_with_engagement_code(self, get_status_tool, test_db):
        """Test status retrieval filtered by engagement_code."""
        # Arrange
        request_data = {
            "request_type": "software_access",
            "requester_email": "jane.doe@msg.com",
            "engagement_code": "ENG-0012345",
        }

        # Act
        result = await get_status_tool.run_with_validation(test_db, request_data)

        # Assert
        assert len(result["results"]) == 2
        for r in result["results"]:
            assert r["engagement_code"] == "ENG-0012345"

    @pytest.mark.anyio
    async def test_get_status_with_approver_email(self, get_status_tool, test_db):
        """Test status retrieval filtered by approver_email."""
        # Arrange
        request_data = {
            "request_type": "software_access",
            "requester_email": "jane.doe@msg.com",
            "approver_email": "senior.manager@msg.com",
        }

        # Act
        result = await get_status_tool.run_with_validation(test_db, request_data)

        # Assert
        assert len(result["results"]) == 1
        assert result["results"][0]["approval_id"] == "APR-1000001"
        assert result["results"][0]["approver_email"] == "senior.manager@msg.com"
        assert result["results"][0]["status"] == "approved"

    @pytest.mark.anyio
    async def test_get_status_all_filters(self, get_status_tool, test_db):
        """Test status retrieval with all filters applied."""
        # Arrange
        request_data = {
            "request_type": "software_access",
            "requester_email": "jane.doe@msg.com",
            "engagement_code": "ENG-0012345",
            "approver_email": "partner@msg.com",
        }

        # Act
        result = await get_status_tool.run_with_validation(test_db, request_data)

        # Assert
        assert len(result["results"]) == 1
        assert result["results"][0]["approval_id"] == "APR-1000003"
        assert result["results"][0]["status"] == "pending"

    @pytest.mark.anyio
    async def test_get_status_no_results(self, get_status_tool, test_db):
        """Test returns dummy result with 'not_found' status when no matches found."""
        # Arrange
        request_data = {
            "request_type": "travel",
            "requester_email": "nonexistent@msg.com",
        }

        # Act
        result = await get_status_tool.run_with_validation(test_db, request_data)

        # Assert
        assert len(result["results"]) == 1
        assert result["results"][0]["approval_id"] == "NOT_FOUND"
        assert result["results"][0]["status"] == "not_found"
        assert result["results"][0]["request_type"] == "travel"

    @pytest.mark.anyio
    async def test_get_status_different_statuses(self, get_status_tool, test_db):
        """Test that all status values are returned correctly."""
        # Test pending status
        result = await get_status_tool.run_with_validation(
            test_db,
            {
                "request_type": "hardware_replacement",
                "requester_email": "john.smith@msg.com",
            },
        )
        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == "pending"

        # Test rejected status
        result = await get_status_tool.run_with_validation(
            test_db,
            {
                "request_type": "training_cost",
                "requester_email": "bob.wilson@msg.com",
            },
        )
        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == "rejected"

        # Test approved status
        result = await get_status_tool.run_with_validation(
            test_db,
            {
                "request_type": "software_access",
                "requester_email": "jane.doe@msg.com",
                "approver_email": "senior.manager@msg.com",
            },
        )
        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == "approved"

    @pytest.mark.anyio
    async def test_get_status_missing_request_type(self, get_status_tool, test_db):
        """Test that missing request_type raises validation error."""
        # Arrange
        request_data = {
            "requester_email": "jane.doe@msg.com",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await get_status_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_status_missing_requester_email(self, get_status_tool, test_db):
        """Test that missing requester_email raises validation error."""
        # Arrange
        request_data = {
            "request_type": "software_access",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await get_status_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_status_invalid_request_type(self, get_status_tool, test_db):
        """Test that invalid request_type raises validation error."""
        # Arrange
        request_data = {
            "request_type": "invalid_type",
            "requester_email": "jane.doe@msg.com",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await get_status_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_status_output_structure(self, get_status_tool, test_db):
        """Test that output structure contains all expected fields."""
        # Arrange
        request_data = {
            "request_type": "software_access",
            "requester_email": "jane.doe@msg.com",
            "approver_email": "senior.manager@msg.com",
        }

        # Act
        result = await get_status_tool.run_with_validation(test_db, request_data)

        # Assert
        assert len(result["results"]) == 1
        status_result = result["results"][0]
        assert "approval_id" in status_result
        assert "status" in status_result
        assert "request_type" in status_result
        assert "approver_email" in status_result
        assert "engagement_code" in status_result

        # Verify values
        assert status_result["approval_id"] == "APR-1000001"
        assert status_result["status"] == "approved"
        assert status_result["request_type"] == "software_access"
        assert status_result["approver_email"] == "senior.manager@msg.com"
        assert status_result["engagement_code"] == "ENG-0012345"

    @pytest.mark.anyio
    async def test_get_status_empty_database(self, get_status_tool):
        """Test status retrieval with empty database returns dummy result."""
        # Arrange - Empty database
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"approval_requests": ApprovalRequest}
        db._model_cls_to_stem = {ApprovalRequest: "approval_requests"}
        db._store = {ApprovalRequest: []}

        request_data = {
            "request_type": "software_access",
            "requester_email": "user@msg.com",
        }

        # Act
        result = await get_status_tool.run_with_validation(db, request_data)

        # Assert
        assert len(result["results"]) == 1
        assert result["results"][0]["approval_id"] == "NOT_FOUND"
        assert result["results"][0]["status"] == "not_found"
