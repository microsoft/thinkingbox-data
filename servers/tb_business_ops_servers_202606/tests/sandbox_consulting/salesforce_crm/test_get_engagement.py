# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for salesforce_get_engagement tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.salesforce_crm.models import (
    EngagementStatus,
    SfEngagement,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.salesforce_crm.tools.get_engagement import (
    GetEngagementTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestGetEngagement:
    @pytest.fixture
    def test_db(self):
        """Create a test database with sf_engagements."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "sf_engagement": SfEngagement,
        }
        db._model_cls_to_stem = {
            SfEngagement: "sf_engagement",
        }

        # Create test engagements
        engagement1 = SfEngagement(
            engagement_code="ENG-0012345",
            client_id="CLT-0012345",
            engagement_manager_email="sarah.johnson@msg.com",
            status=EngagementStatus.ACTIVE,
            start_date="2024-01-15T00:00:00Z",
            end_date="2024-12-31T00:00:00Z",
        )

        engagement2 = SfEngagement(
            engagement_code="ENG-0023456",
            client_id="CLT-0023456",
            engagement_manager_email="michael.chen@msg.com",
            status=EngagementStatus.PIPELINE,
            start_date="2025-01-01T00:00:00Z",
            end_date=None,
        )

        engagement3 = SfEngagement(
            engagement_code="ENG-0034567",
            client_id="CLT-0034567",
            engagement_manager_email="david.kim@msg.com",
            status=EngagementStatus.COMPLETED,
            start_date="2023-06-01T00:00:00Z",
            end_date="2023-12-31T00:00:00Z",
        )

        db._store = {
            SfEngagement: [engagement1, engagement2, engagement3],
        }
        return db

    @pytest.fixture
    def get_engagement_tool(self):
        """Create an instance of the get_engagement tool."""
        return GetEngagementTool()

    @pytest.mark.anyio
    async def test_get_engagement_success(self, get_engagement_tool, test_db):
        """Test successful retrieval of engagement details."""
        # Arrange
        request_data = {"engagement_code": "ENG-0012345"}

        # Act
        result = await get_engagement_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["engagement_code"] == "ENG-0012345"
        assert result["client_id"] == "CLT-0012345"
        assert result["engagement_manager_email"] == "sarah.johnson@msg.com"
        assert result["status"] == "active"
        assert result["start_date"] == "2024-01-15T00:00:00+00:00"
        assert result["end_date"] == "2024-12-31T00:00:00+00:00"

    @pytest.mark.anyio
    async def test_get_engagement_pipeline_status(self, get_engagement_tool, test_db):
        """Test retrieval of engagement with pipeline status."""
        # Arrange
        request_data = {"engagement_code": "ENG-0023456"}

        # Act
        result = await get_engagement_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["engagement_code"] == "ENG-0023456"
        assert result["status"] == "pipeline"
        assert result.get("end_date") is None

    @pytest.mark.anyio
    async def test_get_engagement_completed_status(self, get_engagement_tool, test_db):
        """Test retrieval of engagement with completed status."""
        # Arrange
        request_data = {"engagement_code": "ENG-0034567"}

        # Act
        result = await get_engagement_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["engagement_code"] == "ENG-0034567"
        assert result["status"] == "completed"
        assert result["start_date"] == "2023-06-01T00:00:00+00:00"
        assert result["end_date"] == "2023-12-31T00:00:00+00:00"

    @pytest.mark.anyio
    async def test_get_engagement_not_found(self, get_engagement_tool, test_db):
        """Test error when engagement not found."""
        # Arrange
        request_data = {"engagement_code": "ENG-9999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Engagement not found"):
            await get_engagement_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_engagement_empty_database(self, get_engagement_tool):
        """Test get_engagement with empty database."""
        # Arrange
        empty_db = InMemoryDatabase.__new__(InMemoryDatabase)
        empty_db._stem_to_model_cls = {"sf_engagement": SfEngagement}
        empty_db._model_cls_to_stem = {SfEngagement: "sf_engagement"}
        empty_db._store = {SfEngagement: []}
        request_data = {"engagement_code": "ENG-0012345"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Engagement not found"):
            await get_engagement_tool.run_with_validation(empty_db, request_data)

    @pytest.mark.anyio
    async def test_get_engagement_all_fields_present(
        self, get_engagement_tool, test_db
    ):
        """Test that all expected fields are present in the output."""
        # Arrange
        request_data = {"engagement_code": "ENG-0012345"}

        # Act
        result = await get_engagement_tool.run_with_validation(test_db, request_data)

        # Assert - verify all expected fields are present
        assert "engagement_code" in result
        assert "client_id" in result
        assert "engagement_manager_email" in result
        assert "status" in result
        assert "start_date" in result
        assert "end_date" in result
