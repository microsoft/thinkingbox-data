# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for the get_item tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import Ticket
from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.tools.get_item import (
    GetItemTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestGetItem:
    @pytest.fixture
    def test_db(self):
        """Create a test database with sample data."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"tickets": Ticket}
        db._model_cls_to_stem = {Ticket: "tickets"}

        # Create sample tickets
        ticket1 = Ticket(
            id="1",
            subject="Test Ticket 1",
            status="open",
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        ticket2 = Ticket(
            id="2",
            subject="Test Ticket 2",
            status="closed",
            created_at="2025-01-02T00:00:00Z",
            updated_at="2025-01-02T00:00:00Z",
        )

        db._store = {Ticket: [ticket1, ticket2]}
        return db

    @pytest.fixture
    def get_item_tool(self):
        """Create an instance of GetItemTool."""
        return GetItemTool()

    @pytest.mark.anyio
    async def test_get_existing_item(self, get_item_tool, test_db):
        """Test retrieving an existing item."""
        # Arrange
        request_data = {"table": "tickets", "id": "1"}

        # Act
        result = await get_item_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "item" in result
        item = result["item"]
        assert item["id"] == "1"
        assert item["subject"] == "Test Ticket 1"
        assert item["status"] == "open"

    @pytest.mark.anyio
    async def test_get_non_existing_item(self, get_item_tool, test_db):
        """Test retrieving a non-existing item raises an error."""
        # Arrange
        request_data = {"table": "tickets", "id": "999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="not found"):
            await get_item_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_item_unsupported_table(self, get_item_tool, test_db):
        """Test that getting an item from an unsupported table raises an error."""
        # Arrange
        request_data = {"table": "views", "id": "1"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Unsupported table"):
            await get_item_tool.run_with_validation(test_db, request_data)
