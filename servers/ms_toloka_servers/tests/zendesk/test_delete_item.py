# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for the delete_item tool."""

import pytest
from ms_toloka_servers.toolslib.zendesk.models import Ticket, TicketComment
from ms_toloka_servers.toolslib.zendesk.tools.delete_item import DeleteItemTool
from ms_toloka_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestDeleteItem:
    @pytest.fixture
    def test_db(self):
        """Create a test database with sample data."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "tickets": Ticket,
            "ticket_comments": TicketComment,
        }
        db._model_cls_to_stem = {
            Ticket: "tickets",
            TicketComment: "ticket_comments",
        }

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

        # Create sample ticket comment
        comment1 = TicketComment(
            id=123,
            ticket_id=1,
            author_id=1,
            body="Test comment",
            created_at="2025-01-01T00:00:00Z",
        )

        db._store = {
            Ticket: [ticket1, ticket2],
            TicketComment: [comment1],
        }
        return db

    @pytest.fixture
    def delete_item_tool(self):
        """Create an instance of DeleteItemTool."""
        return DeleteItemTool()

    @pytest.mark.anyio
    async def test_delete_existing_item(self, delete_item_tool, test_db):
        """Test deleting an existing item."""
        # Arrange
        request_data = {"table": "tickets", "id": "1"}

        # Verify item exists before deletion
        tickets_before = test_db.get_all(Ticket)
        assert len(tickets_before) == 2

        # Act
        result = await delete_item_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["success"] is True

        # Verify item was deleted
        tickets_after = test_db.get_all(Ticket)
        assert len(tickets_after) == 1
        assert tickets_after[0].id == "2"

    @pytest.mark.anyio
    async def test_delete_non_existing_item(self, delete_item_tool, test_db):
        """Test deleting a non-existing item raises an error."""
        # Arrange
        request_data = {"table": "tickets", "id": "999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="not found"):
            await delete_item_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_delete_ticket_comment_not_allowed(self, delete_item_tool, test_db):
        """Test that deleting a ticket comment raises an error."""
        # Arrange
        request_data = {"table": "ticket_comments", "id": "123"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="cannot be deleted"):
            await delete_item_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_delete_item_unsupported_table(self, delete_item_tool, test_db):
        """Test that deleting an item from an unsupported table raises an error."""
        # Arrange
        request_data = {"table": "views", "id": "1"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Unsupported table"):
            await delete_item_tool.run_with_validation(test_db, request_data)
