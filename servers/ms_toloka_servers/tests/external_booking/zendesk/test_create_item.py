# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for the create_item tool."""

import pytest
from ms_toloka_servers.toolslib.external_booking.zendesk.models import (
    Organization,
    Ticket,
    User,
)
from ms_toloka_servers.toolslib.external_booking.zendesk.tools.create_item import (
    CreateItemTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestCreateItem:
    @pytest.fixture
    def test_db(self):
        """Create a test database."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "tickets": Ticket,
            "users": User,
            "organizations": Organization,
        }
        db._model_cls_to_stem = {
            Ticket: "tickets",
            User: "users",
            Organization: "organizations",
        }
        db._store = {
            Ticket: [],
            User: [],
            Organization: [],
        }
        return db

    @pytest.fixture
    def create_item_tool(self):
        """Create an instance of CreateItemTool."""
        return CreateItemTool()

    @pytest.mark.anyio
    async def test_create_ticket(self, create_item_tool, test_db):
        """Test creating a new ticket."""
        # Arrange
        request_data = {
            "table": "tickets",
            "item": {
                "subject": "Test ticket",
                "description": "This is a test ticket",
                "priority": "high",
                "status": "open",
            },
        }

        # Act
        result = await create_item_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "item" in result
        item = result["item"]
        assert item["subject"] == "Test ticket"
        assert item["description"] == "This is a test ticket"
        assert item["priority"] == "high"
        assert item["status"] == "open"
        assert "id" in item
        assert "created_at" in item
        assert "updated_at" in item

        # Check that the ticket was added to the database
        tickets = test_db.get_all(Ticket)
        assert len(tickets) == 1
        assert tickets[0].subject == "Test ticket"

    @pytest.mark.anyio
    async def test_create_user(self, create_item_tool, test_db):
        """Test creating a new user."""
        # Arrange
        request_data = {
            "table": "users",
            "item": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "role": "end-user",
            },
        }

        # Act
        result = await create_item_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "item" in result
        item = result["item"]
        assert item["name"] == "John Doe"
        assert item["email"] == "john.doe@example.com"
        assert item["role"] == "end-user"
        assert "id" in item
        assert "created_at" in item

        # Check that the user was added to the database
        users = test_db.get_all(User)
        assert len(users) == 1
        assert users[0].name == "John Doe"

    @pytest.mark.anyio
    async def test_create_organization(self, create_item_tool, test_db):
        """Test creating a new organization."""
        # Arrange
        request_data = {
            "table": "organizations",
            "item": {
                "name": "Test Corp",
                "domain_names": ["testcorp.com"],
                "details": "Test organization",
            },
        }

        # Act
        result = await create_item_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "item" in result
        item = result["item"]
        assert item["name"] == "Test Corp"
        assert item["domain_names"] == ["testcorp.com"]
        assert "id" in item

        # Check that the organization was added to the database
        orgs = test_db.get_all(Organization)
        assert len(orgs) == 1
        assert orgs[0].name == "Test Corp"

    @pytest.mark.anyio
    async def test_create_item_unsupported_table(self, create_item_tool, test_db):
        """Test that creating an item in an unsupported table raises an error."""
        # Arrange
        request_data = {"table": "views", "item": {"name": "Test View"}}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Unsupported table"):
            await create_item_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_create_multiple_tickets(self, create_item_tool, test_db):
        """Test creating multiple tickets generates unique IDs."""
        # Create first ticket
        request_data_1 = {"table": "tickets", "item": {"subject": "First ticket"}}
        result_1 = await create_item_tool.run_with_validation(test_db, request_data_1)

        # Create second ticket
        request_data_2 = {"table": "tickets", "item": {"subject": "Second ticket"}}
        result_2 = await create_item_tool.run_with_validation(test_db, request_data_2)

        # Assert
        assert result_1["item"]["id"] != result_2["item"]["id"]

        # Check database
        tickets = test_db.get_all(Ticket)
        assert len(tickets) == 2
        assert tickets[0].id != tickets[1].id

    @pytest.mark.anyio
    async def test_create_ticket_with_null_tags(self, create_item_tool, test_db):
        """Test creating a ticket with tags=null should use empty list instead."""
        # Arrange - This matches the exact request from the error report
        request_data = {
            "table": "tickets",
            "item": {
                "tags": None,
                "type": "incident",
                "due_at": None,
                "status": "open",
                "subject": "Shipping address change request for order ORD-06005555",
                "priority": "normal",
                "assignee_id": "2",
                "description": "Customer requests to update shipping address from 123 Oak St, Portland, OR 97201 to 456 Elm St, Portland, OR 97202 for order ORD-06005555.",
                "requester_id": "301",
                "organization_id": None,
            },
        }

        # Act
        result = await create_item_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "item" in result
        item = result["item"]
        assert (
            item["subject"] == "Shipping address change request for order ORD-06005555"
        )
        assert item["tags"] == []  # Should be empty list, not None
        assert item["status"] == "open"
        assert item["priority"] == "normal"
        assert "id" in item

        # Check that the ticket was added to the database
        tickets = test_db.get_all(Ticket)
        assert len(tickets) == 1
        assert tickets[0].tags == []  # Should be empty list

    @pytest.mark.anyio
    async def test_create_ticket_tags_filtered_and_sorted(
        self, create_item_tool, test_db
    ):
        """Ignored tags should not be stored in DB, but should appear in output; remaining tags should be stored sorted."""
        request_data = {
            "table": "tickets",
            "item": {
                "subject": "Tags normalization",
                "tags": [
                    "urgent",
                    "VIP-Customer",
                    "Hardware",
                    "repeat-ISSUE",
                    "printer",
                ],
            },
        }

        result = await create_item_tool.run_with_validation(test_db, request_data)

        # Output should contain original unfiltered tags
        assert result["item"]["tags"] == [
            "urgent",
            "VIP-Customer",
            "Hardware",
            "repeat-ISSUE",
            "printer",
        ]

        # Database should only contain filtered and sorted tags (ignored tags removed)
        tickets = test_db.get_all(Ticket)
        assert len(tickets) == 1
        assert tickets[0].tags == ["Hardware", "printer", "urgent"]

    @pytest.mark.anyio
    async def test_create_organization_with_null_domain_names(
        self, create_item_tool, test_db
    ):
        """Test creating an organization with domain_names=null should use empty list instead."""
        # Arrange
        request_data = {
            "table": "organizations",
            "item": {
                "name": "Test Corp",
                "domain_names": None,
                "details": "Test organization",
            },
        }

        # Act
        result = await create_item_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "item" in result
        item = result["item"]
        assert item["name"] == "Test Corp"
        assert item["domain_names"] == []  # Should be empty list, not None
        assert "id" in item

        # Check that the organization was added to the database
        orgs = test_db.get_all(Organization)
        assert len(orgs) == 1
        assert orgs[0].domain_names == []  # Should be empty list

    @pytest.mark.anyio
    async def test_create_ticket_with_custom_fields(self, create_item_tool, test_db):
        """Test creating a ticket with booking-specific custom fields."""
        # Arrange
        request_data = {
            "table": "tickets",
            "item": {
                "subject": "Booking modification request",
                "description": "Need to change check-in date",
                "booking_reference": "BKG-12345678",
                "hotel_id": "HTL-87654321",
                "check_in_date": "2025-01-15T14:00:00Z",
                "booking_value": 1250.00,
                "request_type_detail": "modify-dates",
            },
        }

        # Act
        result = await create_item_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "item" in result
        item = result["item"]
        assert item["subject"] == "Booking modification request"
        assert item["booking_reference"] == "BKG-12345678"
        assert item["hotel_id"] == "HTL-87654321"
        assert item["check_in_date"] == "2025-01-15T14:00:00Z"
        assert item["booking_value"] == 1250.00
        assert item["request_type_detail"] == "modify-dates"

        # Check database
        tickets = test_db.get_all(Ticket)
        assert len(tickets) == 1
        assert tickets[0].booking_reference == "BKG-12345678"
        assert tickets[0].request_type_detail == "modify-dates"

    @pytest.mark.anyio
    async def test_create_ticket_with_partial_custom_fields(
        self, create_item_tool, test_db
    ):
        """Test creating a ticket with only some booking custom fields."""
        # Arrange
        request_data = {
            "table": "tickets",
            "item": {
                "subject": "Refund request",
                "resolution_action": "refund-partial",
                "refund_amount": 250.00,
                "escalation_reason": "high-value-dispute",
            },
        }

        # Act
        result = await create_item_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "item" in result
        item = result["item"]
        assert item["subject"] == "Refund request"
        assert item["resolution_action"] == "refund-partial"
        assert item["refund_amount"] == 250.00
        assert item["escalation_reason"] == "high-value-dispute"
        # Other booking custom fields should be None/absent
        assert item.get("booking_reference") is None
        assert item.get("hotel_id") is None

    @pytest.mark.anyio
    async def test_create_ticket_refund_amount_missing_defaults_to_zero(
        self, create_item_tool, test_db
    ):
        """If refund_amount is missing on ticket creation, it should be stored as 0.0."""
        request_data = {
            "table": "tickets",
            "item": {"subject": "Refund amount missing"},
        }

        result = await create_item_tool.run_with_validation(test_db, request_data)

        assert result["item"]["refund_amount"] == 0.0
        tickets = test_db.get_all(Ticket)
        assert len(tickets) == 1
        assert tickets[0].refund_amount == 0.0

    @pytest.mark.anyio
    async def test_create_ticket_refund_amount_null_defaults_to_zero(
        self, create_item_tool, test_db
    ):
        """If refund_amount is explicitly null/None on ticket creation, it should be stored as 0.0."""
        request_data = {
            "table": "tickets",
            "item": {"subject": "Refund amount null", "refund_amount": None},
        }

        result = await create_item_tool.run_with_validation(test_db, request_data)

        assert result["item"]["refund_amount"] == 0.0
        tickets = test_db.get_all(Ticket)
        assert len(tickets) == 1
        assert tickets[0].refund_amount == 0.0

    @pytest.mark.anyio
    async def test_create_ticket_refund_amount_zero_canonicalized(
        self, create_item_tool, test_db
    ):
        """If refund_amount is 0/0.0 on ticket creation, it should be stored canonically as 0.0."""
        request_data = {
            "table": "tickets",
            "item": {"subject": "Refund amount zero", "refund_amount": 0},
        }

        result = await create_item_tool.run_with_validation(test_db, request_data)

        assert result["item"]["refund_amount"] == 0.0
        tickets = test_db.get_all(Ticket)
        assert len(tickets) == 1
        assert tickets[0].refund_amount == 0.0
