# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for Box Document Management API tool."""

import pytest
from sandbox_servers.toolslib.sandbox_consulting.box.models import (
    ConfidentialityLevel,
    Folder,
    FolderAccessLog,
    PermissionLevel,
)
from sandbox_servers.toolslib.sandbox_consulting.box.tools.api import BoxApiTool
from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestBoxApiTool:
    """Test cases for Box API tool."""

    @pytest.fixture
    def test_db(self):
        """Create a test database with sample data."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "folders": Folder,
            "folder_access_logs": FolderAccessLog,
        }
        db._model_cls_to_stem = {
            Folder: "folders",
            FolderAccessLog: "folder_access_logs",
        }

        # Create test folders
        folder1 = Folder(
            id="FLD-1000001",
            folder_name="Test Public Folder",
            confidentiality_level=ConfidentialityLevel.PUBLIC,
            owner_email="owner@msg.com",
            client_id=None,
            engagement_code=None,
        )
        folder2 = Folder(
            id="FLD-1000002",
            folder_name="Test Client Folder",
            confidentiality_level=ConfidentialityLevel.CLIENT_CONFIDENTIAL,
            owner_email="manager@msg.com",
            client_id="CLT-1000001",
            engagement_code="ENG-1000001",
        )
        folder3 = Folder(
            id="FLD-1000003",
            folder_name="Test Confidential Folder",
            confidentiality_level=ConfidentialityLevel.CONFIDENTIAL,
            owner_email="admin@msg.com",
            client_id=None,
            engagement_code=None,
        )

        # Create test access logs
        access_log1 = FolderAccessLog(
            id="FAL-1000001",
            folder_id="FLD-1000001",
            employee_email="user@msg.com",
            permission_level=PermissionLevel.VIEWER,
        )

        db._store = {
            Folder: [folder1, folder2, folder3],
            FolderAccessLog: [access_log1],
        }

        return db

    @pytest.fixture
    def box_api_tool(self):
        """Create an instance of the Box API tool."""
        return BoxApiTool()

    # Tests for get_folder_details action

    @pytest.mark.anyio
    async def test_get_folder_details_success(self, box_api_tool, test_db):
        """Test successfully retrieving folder details."""
        request_data = {
            "action": "get_folder_details",
            "folder_id": "FLD-1000001",
        }

        result = await box_api_tool.run_with_validation(test_db, request_data)

        assert result.get("folder_data") is not None
        folder_data = result["folder_data"]
        assert folder_data["id"] == "FLD-1000001"
        assert folder_data["folder_name"] == "Test Public Folder"
        assert folder_data["confidentiality_level"] == "public"
        assert folder_data["owner_email"] == "owner@msg.com"
        assert folder_data.get("client_id") is None
        assert folder_data.get("engagement_code") is None

    @pytest.mark.anyio
    async def test_get_folder_details_with_client(self, box_api_tool, test_db):
        """Test retrieving folder details with client_id and engagement_code."""
        request_data = {
            "action": "get_folder_details",
            "folder_id": "FLD-1000002",
        }

        result = await box_api_tool.run_with_validation(test_db, request_data)

        assert result.get("folder_data") is not None
        folder_data = result["folder_data"]
        assert folder_data["id"] == "FLD-1000002"
        assert folder_data["folder_name"] == "Test Client Folder"
        assert folder_data["confidentiality_level"] == "client_confidential"
        assert folder_data["owner_email"] == "manager@msg.com"
        assert folder_data["client_id"] == "CLT-1000001"
        assert folder_data["engagement_code"] == "ENG-1000001"

    @pytest.mark.anyio
    async def test_get_folder_details_not_found(self, box_api_tool, test_db):
        """Test error when folder is not found."""
        request_data = {
            "action": "get_folder_details",
            "folder_id": "FLD-9999999",
        }

        with pytest.raises(Tool.ExecutionError, match="Folder not found: FLD-9999999"):
            await box_api_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_folder_details_missing_folder_id(self, box_api_tool, test_db):
        """Test error when folder_id is missing."""
        request_data = {
            "action": "get_folder_details",
        }

        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: folder_id"
        ):
            await box_api_tool.run_with_validation(test_db, request_data)

    # Tests for grant_folder_access action

    @pytest.mark.anyio
    async def test_grant_folder_access_success(self, box_api_tool, test_db):
        """Test successfully granting folder access."""
        request_data = {
            "action": "grant_folder_access",
            "email": "newuser@msg.com",
            "folder_id": "FLD-1000001",
            "permission_level": "editor",
        }

        result = await box_api_tool.run_with_validation(test_db, request_data)

        assert result.get("success") is True

        # Verify access log was created
        access_logs = test_db.get_all(FolderAccessLog)
        assert len(access_logs) == 2  # Original 1 + new 1

        # Find the new access log
        new_log = [
            log for log in access_logs if log.employee_email == "newuser@msg.com"
        ][0]
        assert new_log.folder_id == "FLD-1000001"
        assert new_log.permission_level == PermissionLevel.EDITOR
        assert new_log.id.startswith("FAL-2-")

    @pytest.mark.anyio
    async def test_grant_folder_access_viewer_permission(self, box_api_tool, test_db):
        """Test granting viewer permission."""
        request_data = {
            "action": "grant_folder_access",
            "email": "viewer@msg.com",
            "folder_id": "FLD-1000002",
            "permission_level": "viewer",
        }

        result = await box_api_tool.run_with_validation(test_db, request_data)

        assert result.get("success") is True

        # Verify access log
        access_logs = test_db.get_all(FolderAccessLog)
        new_log = [
            log for log in access_logs if log.employee_email == "viewer@msg.com"
        ][0]
        assert new_log.permission_level == PermissionLevel.VIEWER

    @pytest.mark.anyio
    async def test_grant_folder_access_co_owner_permission(self, box_api_tool, test_db):
        """Test granting co_owner permission."""
        request_data = {
            "action": "grant_folder_access",
            "email": "coowner@msg.com",
            "folder_id": "FLD-1000003",
            "permission_level": "co_owner",
        }

        result = await box_api_tool.run_with_validation(test_db, request_data)

        assert result.get("success") is True

        # Verify access log
        access_logs = test_db.get_all(FolderAccessLog)
        new_log = [
            log for log in access_logs if log.employee_email == "coowner@msg.com"
        ][0]
        assert new_log.permission_level == PermissionLevel.CO_OWNER

    @pytest.mark.anyio
    async def test_grant_folder_access_missing_email(self, box_api_tool, test_db):
        """Test error when email is missing."""
        request_data = {
            "action": "grant_folder_access",
            "folder_id": "FLD-1000001",
            "permission_level": "viewer",
        }

        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await box_api_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_grant_folder_access_missing_folder_id(self, box_api_tool, test_db):
        """Test error when folder_id is missing."""
        request_data = {
            "action": "grant_folder_access",
            "email": "user@msg.com",
            "permission_level": "viewer",
        }

        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: folder_id"
        ):
            await box_api_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_grant_folder_access_missing_permission_level(
        self, box_api_tool, test_db
    ):
        """Test error when permission_level is missing."""
        request_data = {
            "action": "grant_folder_access",
            "email": "user@msg.com",
            "folder_id": "FLD-1000001",
        }

        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: permission_level"
        ):
            await box_api_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_grant_folder_access_folder_not_found(self, box_api_tool, test_db):
        """Test error when folder does not exist."""
        request_data = {
            "action": "grant_folder_access",
            "email": "user@msg.com",
            "folder_id": "FLD-9999999",
            "permission_level": "viewer",
        }

        with pytest.raises(Tool.ExecutionError, match="Folder not found: FLD-9999999"):
            await box_api_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_grant_folder_access_deterministic_id_generation(
        self, box_api_tool, test_db
    ):
        """Test that ID generation is deterministic and handles collisions."""
        # Grant access multiple times
        for i in range(3):
            request_data = {
                "action": "grant_folder_access",
                "email": f"user{i}@msg.com",
                "folder_id": "FLD-1000001",
                "permission_level": "viewer",
            }
            result = await box_api_tool.run_with_validation(test_db, request_data)
            assert result.get("success") is True

        # Verify all access logs have unique IDs
        access_logs = test_db.get_all(FolderAccessLog)
        assert len(access_logs) == 4  # Original 1 + 3 new
        ids = [log.id for log in access_logs]
        assert len(ids) == len(set(ids))  # All IDs are unique

        # Verify new IDs follow the pattern
        new_ids = [log.id for log in access_logs if log.id.startswith("FAL-2-")]
        assert len(new_ids) == 3
        assert "FAL-2-000000" in new_ids
        assert "FAL-2-000001" in new_ids
        assert "FAL-2-000002" in new_ids

    # Tests for invalid action

    @pytest.mark.anyio
    async def test_invalid_action(self, box_api_tool, test_db):
        """Test error when invalid action is provided."""
        request_data = {
            "action": "invalid_action",
        }

        with pytest.raises(
            Tool.ExecutionError,
            match="Input validation failed: action: Input should be 'get_folder_details' or 'grant_folder_access'",
        ):
            await box_api_tool.run_with_validation(test_db, request_data)
