# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for background_check_api master tool."""

import pytest
from sandbox_servers.toolslib.sandbox_consulting.background_check.tools.api import (
    BackgroundCheckApiTool,
)
from sandbox_servers.toolslib.sandbox_consulting.client_access.models import (
    ClearanceRecord,
    ClearanceStatus,
)
from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestBackgroundCheckApi:
    @pytest.fixture
    def test_db(self):
        """Create a test database with clearance records."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "clearance_records": ClearanceRecord,
        }
        db._model_cls_to_stem = {
            ClearanceRecord: "clearance_records",
        }

        # Create test clearance records
        clearance1 = ClearanceRecord(
            employee_email="jane.doe@msg.com",
            clearance_level="standard",
            status=ClearanceStatus.CLEARED,
        )

        clearance2 = ClearanceRecord(
            employee_email="john.smith@msg.com",
            clearance_level="high_security",
            status=ClearanceStatus.IN_PROGRESS,
        )

        clearance3 = ClearanceRecord(
            employee_email="bob.wilson@msg.com",
            clearance_level="standard",
            status=ClearanceStatus.FAILED,
        )

        db._store = {
            ClearanceRecord: [clearance1, clearance2, clearance3],
        }
        return db

    @pytest.fixture
    def background_check_tool(self):
        """Create an instance of the Background Check API tool."""
        return BackgroundCheckApiTool()

    # Tests for get_status action
    @pytest.mark.anyio
    async def test_get_status_success(self, background_check_tool, test_db):
        """Test successful status retrieval."""
        # Arrange
        request_data = {"action": "get_status", "email": "jane.doe@msg.com"}

        # Act
        result = await background_check_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("clearance_data") is not None
        clearance = result["clearance_data"]
        assert clearance["clearance_level"] == "standard"
        assert clearance["status"] == "cleared"

    @pytest.mark.anyio
    async def test_get_status_in_progress(self, background_check_tool, test_db):
        """Test status retrieval for in-progress clearance."""
        # Arrange
        request_data = {"action": "get_status", "email": "john.smith@msg.com"}

        # Act
        result = await background_check_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("clearance_data") is not None
        clearance = result["clearance_data"]
        assert clearance["clearance_level"] == "high_security"
        assert clearance["status"] == "in_progress"

    @pytest.mark.anyio
    async def test_get_status_failed(self, background_check_tool, test_db):
        """Test status retrieval for failed clearance."""
        # Arrange
        request_data = {"action": "get_status", "email": "bob.wilson@msg.com"}

        # Act
        result = await background_check_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("clearance_data") is not None
        clearance = result["clearance_data"]
        assert clearance["status"] == "failed"

    @pytest.mark.anyio
    async def test_get_status_not_initiated(self, background_check_tool, test_db):
        """Test status retrieval for employee with no clearance record."""
        # Arrange
        request_data = {"action": "get_status", "email": "nobody@msg.com"}

        # Act
        result = await background_check_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("clearance_data") is not None
        clearance = result["clearance_data"]
        assert clearance["status"] == "not_initiated"
        assert clearance["clearance_level"] == "standard"  # Default

    @pytest.mark.anyio
    async def test_get_status_missing_email(self, background_check_tool, test_db):
        """Test get_status without email raises error."""
        # Arrange
        request_data = {"action": "get_status"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await background_check_tool.run_with_validation(test_db, request_data)

    # Tests for initiate action
    @pytest.mark.anyio
    async def test_initiate_new_clearance(self, background_check_tool, test_db):
        """Test initiating clearance for new employee."""
        # Arrange
        request_data = {
            "action": "initiate",
            "email": "new.user@msg.com",
            "clearance_level": "standard",
        }

        # Act
        result = await background_check_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["success"] is True

        # Verify clearance record was created
        clearances = test_db.get_all(ClearanceRecord)
        new_clearance = [
            c for c in clearances if c.employee_email == "new.user@msg.com"
        ]
        assert len(new_clearance) == 1
        assert new_clearance[0].clearance_level == "standard"
        assert new_clearance[0].status == ClearanceStatus.IN_PROGRESS

    @pytest.mark.anyio
    async def test_initiate_update_existing(self, background_check_tool, test_db):
        """Test initiating clearance for existing employee (UPSERT update)."""
        # Arrange
        request_data = {
            "action": "initiate",
            "email": "jane.doe@msg.com",
            "clearance_level": "high_security",
        }

        # Act
        result = await background_check_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["success"] is True

        # Verify clearance record was updated
        clearances = test_db.get_all(ClearanceRecord)
        updated_clearance = [
            c for c in clearances if c.employee_email == "jane.doe@msg.com"
        ]
        assert len(updated_clearance) == 1
        assert updated_clearance[0].clearance_level == "high_security"
        assert updated_clearance[0].status == ClearanceStatus.IN_PROGRESS

    @pytest.mark.anyio
    async def test_initiate_high_security_clearance(
        self, background_check_tool, test_db
    ):
        """Test initiating high_security clearance."""
        # Arrange
        request_data = {
            "action": "initiate",
            "email": "vip.user@msg.com",
            "clearance_level": "high_security",
        }

        # Act
        result = await background_check_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["success"] is True

        # Verify high security clearance
        clearances = test_db.get_all(ClearanceRecord)
        new_clearance = [
            c for c in clearances if c.employee_email == "vip.user@msg.com"
        ]
        assert len(new_clearance) == 1
        assert new_clearance[0].clearance_level == "high_security"

    @pytest.mark.anyio
    async def test_initiate_missing_email(self, background_check_tool, test_db):
        """Test initiate without email raises error."""
        # Arrange
        request_data = {"action": "initiate", "clearance_level": "standard"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await background_check_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_initiate_missing_clearance_level(
        self, background_check_tool, test_db
    ):
        """Test initiate without clearance_level raises error."""
        # Arrange
        request_data = {"action": "initiate", "email": "user@msg.com"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: clearance_level"
        ):
            await background_check_tool.run_with_validation(test_db, request_data)

    # Tests for get_timeline action
    @pytest.mark.anyio
    async def test_get_timeline_standard(self, background_check_tool, test_db):
        """Test timeline for standard clearance."""
        # Arrange
        request_data = {"action": "get_timeline", "clearance_level": "standard"}

        # Act
        result = await background_check_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["estimated_days"] == 14

    @pytest.mark.anyio
    async def test_get_timeline_high_security(self, background_check_tool, test_db):
        """Test timeline for high_security clearance."""
        # Arrange
        request_data = {"action": "get_timeline", "clearance_level": "high_security"}

        # Act
        result = await background_check_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["estimated_days"] == 28

    @pytest.mark.anyio
    async def test_get_timeline_missing_clearance_level(
        self, background_check_tool, test_db
    ):
        """Test get_timeline without clearance_level raises error."""
        # Arrange
        request_data = {"action": "get_timeline"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: clearance_level"
        ):
            await background_check_tool.run_with_validation(test_db, request_data)

    # Test for invalid action
    @pytest.mark.anyio
    async def test_invalid_action(self, background_check_tool, test_db):
        """Test that invalid action raises validation error."""
        # Arrange
        request_data = {"action": "invalid_action"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await background_check_tool.run_with_validation(test_db, request_data)

    # Test for empty database
    @pytest.mark.anyio
    async def test_get_status_empty_database(self, background_check_tool):
        """Test get_status in empty database returns not_initiated."""
        # Arrange - Empty database
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"clearance_records": ClearanceRecord}
        db._model_cls_to_stem = {ClearanceRecord: "clearance_records"}
        db._store = {ClearanceRecord: []}

        request_data = {"action": "get_status", "email": "user@msg.com"}

        # Act
        result = await background_check_tool.run_with_validation(db, request_data)

        # Assert
        assert result.get("clearance_data") is not None
        assert result["clearance_data"]["status"] == "not_initiated"
