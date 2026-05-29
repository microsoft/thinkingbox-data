# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for the create_item tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.zendesk.models import (
    Organization,
    Ticket,
    TicketStatusViolation,
    User,
)
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.zendesk.tools.create_item import (
    CreateItemTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
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
            "ticket_status_violations": TicketStatusViolation,
        }
        db._model_cls_to_stem = {
            Ticket: "tickets",
            User: "users",
            Organization: "organizations",
            TicketStatusViolation: "ticket_status_violations",
        }
        db._store = {
            Ticket: [],
            User: [],
            Organization: [],
            TicketStatusViolation: [],
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
                "owner": "it_support",
                "approval_request_ids": "APR-00000001,APR-00000002",
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
        assert item["owner"] == "it_support"
        assert item["approval_request_ids"] == "APR-00000001,APR-00000002"
        assert "id" in item
        assert "created_at" in item
        assert "updated_at" in item

        # Check that the ticket was added to the database
        tickets = test_db.get_all(Ticket)
        assert len(tickets) == 1
        assert tickets[0].subject == "Test ticket"
        assert tickets[0].owner == "it_support"
        assert tickets[0].approval_request_ids == "APR-00000001,APR-00000002"

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
                "domain_names": "testcorp.com",
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
    async def test_create_ticket_without_custom_fields(self, create_item_tool, test_db):
        """Test creating a ticket without custom_fields (all should be None)."""
        # Arrange
        from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.zendesk.models import (
            Ticket,
        )

        request_data = {
            "table": "tickets",
            "item": {"subject": "Basic ticket", "status": "new"},
        }

        # Act
        result = await create_item_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "item" in result
        item = result["item"]
        assert item["subject"] == "Basic ticket"
        # All custom fields should be None when not provided
        assert item.get("resolution_category") is None
        assert item.get("approval_required") is None

        # Check database
        tickets = test_db.get_all(Ticket)
        assert len(tickets) == 1
        assert tickets[0].resolution_category is None
        assert tickets[0].approval_required is None

    @pytest.mark.anyio
    async def test_create_ticket_with_status_open_no_violation_logged(
        self, create_item_tool, test_db
    ):
        """Test that creating a ticket with status='open' does NOT log a violation."""
        # Arrange
        request_data = {
            "table": "tickets",
            "item": {"subject": "Test ticket with open status", "status": "open"},
        }

        # Act
        result = await create_item_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "item" in result
        assert result["item"]["status"] == "open"

        # Verify NO violation was logged
        violations = test_db.get_all(TicketStatusViolation)
        assert len(violations) == 0

    @pytest.mark.anyio
    async def test_create_ticket_with_status_new_logs_violation(
        self, create_item_tool, test_db
    ):
        """Test that creating a ticket with status='new' logs a violation."""
        # Arrange
        request_data = {
            "table": "tickets",
            "item": {"subject": "Test ticket with new status", "status": "new"},
        }

        # Act
        result = await create_item_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "item" in result
        ticket = result["item"]
        assert ticket["status"] == "new"

        # Verify violation WAS logged
        violations = test_db.get_all(TicketStatusViolation)
        assert len(violations) == 1
        assert violations[0].ticket_id == ticket["id"]
        assert violations[0].created_status == "new"
        assert violations[0].created_at == "2025-10-01T13:00:05Z"

    @pytest.mark.anyio
    async def test_create_ticket_with_status_pending_logs_violation(
        self, create_item_tool, test_db
    ):
        """Test that creating a ticket with status='pending' logs a violation."""
        # Arrange
        request_data = {
            "table": "tickets",
            "item": {"subject": "Test ticket with pending status", "status": "pending"},
        }

        # Act
        result = await create_item_tool.run_with_validation(test_db, request_data)

        # Assert
        ticket = result["item"]
        assert ticket["status"] == "pending"

        # Verify violation WAS logged
        violations = test_db.get_all(TicketStatusViolation)
        assert len(violations) == 1
        assert violations[0].created_status == "pending"

    @pytest.mark.anyio
    async def test_create_ticket_without_status_logs_violation(
        self, create_item_tool, test_db
    ):
        """Test that creating a ticket without status (defaults to 'new') logs a violation."""
        # Arrange
        request_data = {
            "table": "tickets",
            "item": {"subject": "Test ticket without status"},
        }

        # Act
        result = await create_item_tool.run_with_validation(test_db, request_data)

        # Assert
        ticket = result["item"]
        assert ticket["status"] == "new"  # Default status

        # Verify violation WAS logged
        violations = test_db.get_all(TicketStatusViolation)
        assert len(violations) == 1
        assert violations[0].created_status == "new"

    @pytest.mark.anyio
    async def test_create_multiple_tickets_logs_multiple_violations(
        self, create_item_tool, test_db
    ):
        """Test that creating multiple tickets with bad status logs multiple violations."""
        # Create first ticket with status='new'
        request_data_1 = {
            "table": "tickets",
            "item": {"subject": "First ticket", "status": "new"},
        }
        result_1 = await create_item_tool.run_with_validation(test_db, request_data_1)

        # Create second ticket with status='open' (no violation)
        request_data_2 = {
            "table": "tickets",
            "item": {"subject": "Second ticket", "status": "open"},
        }
        result_2 = await create_item_tool.run_with_validation(test_db, request_data_2)

        # Create third ticket with status='hold'
        request_data_3 = {
            "table": "tickets",
            "item": {"subject": "Third ticket", "status": "hold"},
        }
        result_3 = await create_item_tool.run_with_validation(test_db, request_data_3)

        # Assert
        tickets = test_db.get_all(Ticket)
        assert len(tickets) == 3

        # Verify only 2 violations logged (not the 'open' one)
        violations = test_db.get_all(TicketStatusViolation)
        assert len(violations) == 2
        assert violations[0].ticket_id == result_1["item"]["id"]
        assert violations[0].created_status == "new"
        assert violations[1].ticket_id == result_3["item"]["id"]
        assert violations[1].created_status == "hold"

    @pytest.mark.anyio
    async def test_create_non_ticket_item_no_violation_logged(
        self, create_item_tool, test_db
    ):
        """Test that creating non-ticket items does not log violations."""
        # Arrange
        request_data = {
            "table": "users",
            "item": {"name": "John Doe", "email": "john@example.com"},
        }

        # Act
        result = await create_item_tool.run_with_validation(test_db, request_data)

        # Assert
        assert "item" in result
        users = test_db.get_all(User)
        assert len(users) == 1

        # Verify NO violation was logged
        violations = test_db.get_all(TicketStatusViolation)
        assert len(violations) == 0
