# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for nda_api master tool."""

import pytest
from sandbox_servers.toolslib.sandbox_consulting.client_access.models import (
    NdaRecord,
    NdaStatus,
)
from sandbox_servers.toolslib.sandbox_consulting.nda.tools.api import NdaApiTool
from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestNdaApi:
    @pytest.fixture
    def test_db(self):
        """Create a test database with NDA records."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "nda_records": NdaRecord,
        }
        db._model_cls_to_stem = {
            NdaRecord: "nda_records",
        }

        # Create test NDA records
        nda1 = NdaRecord(
            employee_email="jane.doe@msg.com",
            client_id="CLT-0012345",
            status=NdaStatus.SIGNED,
        )

        nda2 = NdaRecord(
            employee_email="john.smith@msg.com",
            client_id="CLT-0012345",
            status=NdaStatus.SENT_FOR_SIGNATURE,
        )

        nda3 = NdaRecord(
            employee_email="bob.wilson@msg.com",
            client_id="CLT-0067890",
            status=NdaStatus.EXPIRED,
        )

        db._store = {
            NdaRecord: [nda1, nda2, nda3],
        }
        return db

    @pytest.fixture
    def nda_tool(self):
        """Create an instance of the NDA API tool."""
        return NdaApiTool()

    # Tests for check_status action
    @pytest.mark.anyio
    async def test_check_status_signed(self, nda_tool, test_db):
        """Test status check for signed NDA."""
        # Arrange
        request_data = {
            "action": "check_status",
            "email": "jane.doe@msg.com",
            "client_id": "CLT-0012345",
        }

        # Act
        result = await nda_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["signed"] is True
        assert result.get("nda_data") is not None
        assert result["nda_data"]["status"] == "signed"

    @pytest.mark.anyio
    async def test_check_status_sent_for_signature(self, nda_tool, test_db):
        """Test status check for NDA sent for signature."""
        # Arrange
        request_data = {
            "action": "check_status",
            "email": "john.smith@msg.com",
            "client_id": "CLT-0012345",
        }

        # Act
        result = await nda_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["signed"] is False
        assert result.get("nda_data") is not None
        assert result["nda_data"]["status"] == "sent_for_signature"

    @pytest.mark.anyio
    async def test_check_status_expired(self, nda_tool, test_db):
        """Test status check for expired NDA."""
        # Arrange
        request_data = {
            "action": "check_status",
            "email": "bob.wilson@msg.com",
            "client_id": "CLT-0067890",
        }

        # Act
        result = await nda_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["signed"] is False
        assert result.get("nda_data") is not None
        assert result["nda_data"]["status"] == "expired"

    @pytest.mark.anyio
    async def test_check_status_not_signed(self, nda_tool, test_db):
        """Test status check when no NDA record exists."""
        # Arrange
        request_data = {
            "action": "check_status",
            "email": "nobody@msg.com",
            "client_id": "CLT-0012345",
        }

        # Act
        result = await nda_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["signed"] is False
        assert result.get("nda_data") is not None
        assert result["nda_data"]["status"] == "not_signed"

    @pytest.mark.anyio
    async def test_check_status_missing_email(self, nda_tool, test_db):
        """Test check_status without email raises error."""
        # Arrange
        request_data = {"action": "check_status", "client_id": "CLT-0012345"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await nda_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_check_status_missing_client_id(self, nda_tool, test_db):
        """Test check_status without client_id raises error."""
        # Arrange
        request_data = {"action": "check_status", "email": "user@msg.com"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: client_id"
        ):
            await nda_tool.run_with_validation(test_db, request_data)

    # Tests for send_for_signature action
    @pytest.mark.anyio
    async def test_send_for_signature_new_record(self, nda_tool, test_db):
        """Test sending NDA for new employee-client pair."""
        # Arrange
        request_data = {
            "action": "send_for_signature",
            "email": "new.user@msg.com",
            "client_id": "CLT-0012345",
        }

        # Act
        result = await nda_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["success"] is True

        # Verify NDA record was created
        ndas = test_db.get_all(NdaRecord)
        new_nda = [
            n
            for n in ndas
            if n.employee_email == "new.user@msg.com" and n.client_id == "CLT-0012345"
        ]
        assert len(new_nda) == 1
        assert new_nda[0].status == NdaStatus.SENT_FOR_SIGNATURE

    @pytest.mark.anyio
    async def test_send_for_signature_update_existing(self, nda_tool, test_db):
        """Test sending NDA when record exists (UPSERT update)."""
        # Arrange
        request_data = {
            "action": "send_for_signature",
            "email": "bob.wilson@msg.com",
            "client_id": "CLT-0067890",
        }

        # Act
        result = await nda_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["success"] is True

        # Verify NDA record was updated
        ndas = test_db.get_all(NdaRecord)
        updated_nda = [
            n
            for n in ndas
            if n.employee_email == "bob.wilson@msg.com" and n.client_id == "CLT-0067890"
        ]
        assert len(updated_nda) == 1
        assert updated_nda[0].status == NdaStatus.SENT_FOR_SIGNATURE

    @pytest.mark.anyio
    async def test_send_for_signature_already_signed(self, nda_tool, test_db):
        """Test sending NDA for already signed record (updates status)."""
        # Arrange
        request_data = {
            "action": "send_for_signature",
            "email": "jane.doe@msg.com",
            "client_id": "CLT-0012345",
        }

        # Act
        result = await nda_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["success"] is True

        # Verify status was updated to sent_for_signature
        ndas = test_db.get_all(NdaRecord)
        updated_nda = [
            n
            for n in ndas
            if n.employee_email == "jane.doe@msg.com" and n.client_id == "CLT-0012345"
        ]
        assert len(updated_nda) == 1
        assert updated_nda[0].status == NdaStatus.SENT_FOR_SIGNATURE

    @pytest.mark.anyio
    async def test_send_for_signature_missing_email(self, nda_tool, test_db):
        """Test send_for_signature without email raises error."""
        # Arrange
        request_data = {"action": "send_for_signature", "client_id": "CLT-0012345"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await nda_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_send_for_signature_missing_client_id(self, nda_tool, test_db):
        """Test send_for_signature without client_id raises error."""
        # Arrange
        request_data = {"action": "send_for_signature", "email": "user@msg.com"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: client_id"
        ):
            await nda_tool.run_with_validation(test_db, request_data)

    # Test for invalid action
    @pytest.mark.anyio
    async def test_invalid_action(self, nda_tool, test_db):
        """Test that invalid action raises validation error."""
        # Arrange
        request_data = {"action": "invalid_action"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await nda_tool.run_with_validation(test_db, request_data)

    # Test for empty database
    @pytest.mark.anyio
    async def test_check_status_empty_database(self, nda_tool):
        """Test check_status in empty database returns not_signed."""
        # Arrange - Empty database
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"nda_records": NdaRecord}
        db._model_cls_to_stem = {NdaRecord: "nda_records"}
        db._store = {NdaRecord: []}

        request_data = {
            "action": "check_status",
            "email": "user@msg.com",
            "client_id": "CLT-0012345",
        }

        # Act
        result = await nda_tool.run_with_validation(db, request_data)

        # Assert
        assert result["signed"] is False
        assert result["nda_data"]["status"] == "not_signed"
