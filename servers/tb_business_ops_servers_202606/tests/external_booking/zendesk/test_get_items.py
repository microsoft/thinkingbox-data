# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_items tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.tools.get_items import (
    GetItemsTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestGetItemsTool:
    """Test cases for GetItemsTool."""

    @pytest.fixture
    def mock_db(self, tmp_path):
        """Create a mock database with test data."""
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import (
            Ticket,
            TicketComment,
        )

        # Create database without data directory
        db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)

        # Manually register the models
        db._stem_to_model_cls["tickets"] = Ticket
        db._model_cls_to_stem[Ticket] = "tickets"
        db._stem_to_model_cls["ticket_comments"] = TicketComment
        db._model_cls_to_stem[TicketComment] = "ticket_comments"

        # Create test tickets
        tickets = [
            Ticket(
                id="1",
                subject="Printer issue",
                description="Test 1",
                status="open",
                priority="high",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-01T00:00:00Z",
                tags=[],
            ),
            Ticket(
                id="2",
                subject="Network problem",
                description="Test 2",
                status="pending",
                priority="normal",
                created_at="2025-01-02T00:00:00Z",
                updated_at="2025-01-02T00:00:00Z",
                tags=[],
            ),
            Ticket(
                id="3",
                subject="Password reset",
                description="Test 3",
                status="solved",
                priority="low",
                created_at="2025-01-03T00:00:00Z",
                updated_at="2025-01-03T00:00:00Z",
                tags=[],
            ),
        ]

        # Add tickets to database store
        db._store[Ticket] = tickets
        # Initialize empty list for ticket_comments
        db._store[TicketComment] = []

        return db

    @pytest.fixture
    def get_items_tool(self):
        """Create an instance of GetItemsTool."""
        return GetItemsTool()

    @pytest.mark.anyio
    async def test_get_all_tickets(self, get_items_tool, mock_db):
        """Test retrieving all tickets."""
        request_data = {"table": "tickets"}

        result = await get_items_tool.run_with_validation(mock_db, request_data)

        assert len(result["items"]) == 3
        assert result["items"][0]["id"] == "1"
        assert result["items"][1]["id"] == "2"
        assert result["items"][2]["id"] == "3"

    @pytest.mark.anyio
    async def test_get_tickets_with_top(self, get_items_tool, mock_db):
        """Test retrieving tickets with $top parameter."""
        request_data = {"table": "tickets", "$top": 2}

        result = await get_items_tool.run_with_validation(mock_db, request_data)

        assert len(result["items"]) == 2

    @pytest.mark.anyio
    async def test_get_tickets_with_skip(self, get_items_tool, mock_db):
        """Test retrieving tickets with $skip parameter."""
        request_data = {"table": "tickets", "$skip": 1}

        result = await get_items_tool.run_with_validation(mock_db, request_data)

        assert len(result["items"]) == 2
        assert result["items"][0]["id"] == "2"

    @pytest.mark.anyio
    async def test_get_tickets_with_select(self, get_items_tool, mock_db):
        """Test retrieving tickets with $select parameter."""
        request_data = {"table": "tickets", "$select": "id,subject"}

        result = await get_items_tool.run_with_validation(mock_db, request_data)

        assert len(result["items"]) == 3
        assert "id" in result["items"][0]
        assert "subject" in result["items"][0]
        assert "description" not in result["items"][0]

    @pytest.mark.anyio
    async def test_get_tickets_with_orderby(self, get_items_tool, mock_db):
        """Test retrieving tickets with $orderby parameter."""
        request_data = {"table": "tickets", "$orderby": "created_at desc"}

        result = await get_items_tool.run_with_validation(mock_db, request_data)

        assert len(result["items"]) == 3
        assert result["items"][0]["id"] == "3"  # Most recent
        assert result["items"][2]["id"] == "1"  # Oldest

    @pytest.mark.anyio
    async def test_get_empty_table(self, get_items_tool, mock_db):
        """Test retrieving from empty table."""
        request_data = {"table": "users"}

        result = await get_items_tool.run_with_validation(mock_db, request_data)

        assert len(result["items"]) == 0

    @pytest.mark.anyio
    async def test_get_items_with_odata_filter_by_status(self, get_items_tool, mock_db):
        """Test getting items with OData filter by status."""
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import Ticket

        # Note: fixture already has 1 ticket with status="open" (id="1")
        # Add one more ticket with different status
        mock_db.create(
            Ticket(
                id="100",
                subject="New ticket",
                description="Test",
                status="new",
                priority="normal",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-01T00:00:00Z",
                tags=[],
            )
        )

        request_data = {"table": "tickets", "$filter": "status eq 'new'"}

        result = await get_items_tool.run_with_validation(mock_db, request_data)

        # Should only return tickets with status="new"
        assert len(result["items"]) == 1
        assert result["items"][0]["status"] == "new"
        assert result["items"][0]["subject"] == "New ticket"

    @pytest.mark.anyio
    async def test_get_items_with_odata_filter_by_integer(
        self, get_items_tool, mock_db
    ):
        """Test getting items with OData filter by integer field."""
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import (
            TicketComment,
        )

        # Add test comments
        mock_db.create(
            TicketComment(
                id=1000,
                ticket_id=99,
                author_id=1,
                body="Comment for ticket 99",
                public=True,
                created_at="2025-01-01T00:00:00Z",
                key="1000",
            )
        )
        mock_db.create(
            TicketComment(
                id=1001,
                ticket_id=100,
                author_id=1,
                body="Comment for ticket 100",
                public=True,
                created_at="2025-01-01T00:00:00Z",
                key="1001",
            )
        )

        request_data = {"table": "ticket_comments", "$filter": "ticket_id eq 99"}

        result = await get_items_tool.run_with_validation(mock_db, request_data)

        # Should only return comments for ticket_id=99
        assert len(result["items"]) == 1
        assert result["items"][0]["ticket_id"] == 99
        assert result["items"][0]["body"] == "Comment for ticket 99"

    @pytest.mark.anyio
    async def test_get_tickets_with_compound_odata_filter(
        self, get_items_tool, mock_db
    ):
        """Test getting items with compound OData filter (and/or)."""
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import Ticket

        # Add more tickets with requester_id for testing
        mock_db.create(
            Ticket(
                id="301",
                subject="Test ticket 1",
                description="Test",
                status="open",
                priority="normal",
                requester_id="301",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-01T00:00:00Z",
                tags=[],
            )
        )
        mock_db.create(
            Ticket(
                id="302",
                subject="Test ticket 2",
                description="Test",
                status="pending",
                priority="normal",
                requester_id="301",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-01T00:00:00Z",
                tags=[],
            )
        )
        mock_db.create(
            Ticket(
                id="303",
                subject="Test ticket 3",
                description="Test",
                status="hold",
                priority="normal",
                requester_id="301",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-01T00:00:00Z",
                tags=[],
            )
        )
        mock_db.create(
            Ticket(
                id="304",
                subject="Test ticket 4",
                description="Test",
                status="solved",
                priority="normal",
                requester_id="301",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-01T00:00:00Z",
                tags=[],
            )
        )

        # Test compound filter: requester_id eq '301' and (status eq 'open' or status eq 'pending' or status eq 'hold')
        request_data = {
            "table": "tickets",
            "$filter": "requester_id eq '301' and (status eq 'open' or status eq 'pending' or status eq 'hold')",
        }

        result = await get_items_tool.run_with_validation(mock_db, request_data)

        # Should return 3 tickets: 301 (open), 302 (pending), 303 (hold)
        # Should NOT return 304 (solved)
        assert len(result["items"]) == 3
        returned_ids = {item["id"] for item in result["items"]}
        assert returned_ids == {"301", "302", "303"}

    @pytest.mark.anyio
    async def test_get_items_with_ne_filter(self, get_items_tool, mock_db):
        """Test getting items with OData ne (not equal) filter."""
        request_data = {"table": "tickets", "$filter": "status ne 'open'"}

        result = await get_items_tool.run_with_validation(mock_db, request_data)

        # Should return tickets where status != 'open'
        assert len(result["items"]) >= 1
        for item in result["items"]:
            assert item["status"] != "open"

    @pytest.mark.anyio
    async def test_get_items_with_gt_filter(self, get_items_tool, mock_db):
        """Test getting items with OData gt (greater than) filter."""
        request_data = {"table": "tickets", "$filter": "id gt '1'"}

        result = await get_items_tool.run_with_validation(mock_db, request_data)

        # Should return tickets with id > '1'
        assert len(result["items"]) >= 1
        for item in result["items"]:
            assert item["id"] > "1"

    @pytest.mark.anyio
    async def test_get_items_with_ge_filter(self, get_items_tool, mock_db):
        """Test getting items with OData ge (greater than or equal) filter."""
        request_data = {"table": "tickets", "$filter": "id ge '2'"}

        result = await get_items_tool.run_with_validation(mock_db, request_data)

        # Should return tickets with id >= '2'
        assert len(result["items"]) >= 1
        for item in result["items"]:
            assert item["id"] >= "2"
        # Check that id='2' and id='3' are included
        ids = {item["id"] for item in result["items"]}
        assert "2" in ids and "3" in ids

    @pytest.mark.anyio
    async def test_get_items_with_lt_filter(self, get_items_tool, mock_db):
        """Test getting items with OData lt (less than) filter."""
        request_data = {"table": "tickets", "$filter": "id lt '3'"}

        result = await get_items_tool.run_with_validation(mock_db, request_data)

        # Should return tickets with id < '3'
        assert len(result["items"]) >= 1
        for item in result["items"]:
            assert item["id"] < "3"
        # Check that id='1' and id='2' are included
        ids = {item["id"] for item in result["items"]}
        assert "1" in ids and "2" in ids

    @pytest.mark.anyio
    async def test_get_items_with_le_filter(self, get_items_tool, mock_db):
        """Test getting items with OData le (less than or equal) filter."""
        request_data = {"table": "tickets", "$filter": "id le '2'"}

        result = await get_items_tool.run_with_validation(mock_db, request_data)

        # Should return tickets with id <= '2'
        assert len(result["items"]) >= 1
        for item in result["items"]:
            assert item["id"] <= "2"
        # Check that id='1' and id='2' are included
        ids = {item["id"] for item in result["items"]}
        assert "1" in ids and "2" in ids

    @pytest.mark.anyio
    async def test_get_unsupported_table(self, get_items_tool, mock_db):
        """Test getting items from unsupported table."""
        request_data = {
            "table": "articles"  # Valid enum value but not supported for CRUD
        }

        with pytest.raises(get_items_tool.ExecutionError, match="Unsupported table"):
            await get_items_tool.run_with_validation(mock_db, request_data)
