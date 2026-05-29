# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for update_item tool."""

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.tools.update_item import (
    UpdateItemInput,
    UpdateItemTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestUpdateItemTool:
    """Test cases for UpdateItemTool."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database with test data."""
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import (
            Comment,
            Organization,
            Ticket,
            TicketComment,
            User,
        )

        # Create database with manual initialization (similar to test_create_item.py)
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "tickets": Ticket,
            "users": User,
            "organizations": Organization,
            "comments": Comment,
            "ticket_comments": TicketComment,
        }
        db._model_cls_to_stem = {
            Ticket: "tickets",
            User: "users",
            Organization: "organizations",
            Comment: "comments",
            TicketComment: "ticket_comments",
        }

        # Create initial test data
        existing_ticket = Ticket(
            id="1",
            subject="Original subject",
            description="Original description",
            status="open",
            priority="normal",
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
            tags=[],
        )

        existing_user = User(
            id="1",
            name="Original Name",
            email="original@example.com",
            role="end-user",
            verified=True,
            active=True,
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )

        existing_ticket_comment = TicketComment(
            id=23118465221916,
            ticket_id=1,
            author_id=22677105199388,
            body="Test comment",
            public=True,
            created_at="2025-01-01T00:00:00Z",
            key="23118465221916",
        )

        db._store = {
            Ticket: [existing_ticket],
            User: [existing_user],
            Organization: [],
            Comment: [],
            TicketComment: [existing_ticket_comment],
        }

        return db

    @pytest.fixture
    def update_item_tool(self):
        """Create an instance of UpdateItemTool."""
        return UpdateItemTool()

    @pytest.mark.anyio
    async def test_update_ticket_priority(self, update_item_tool, mock_db):
        """Test updating ticket priority."""
        request_data = {"table": "tickets", "id": "1", "item": {"priority": "urgent"}}

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        assert result["item"]["id"] == "1"
        assert result["item"]["priority"] == "urgent"
        assert result["item"]["subject"] == "Original subject"  # Unchanged
        assert (
            result["item"]["updated_at"] == "2025-10-01T13:00:10Z"
        )  # Tickets use update timestamp

    @pytest.mark.anyio
    async def test_update_ticket_status(self, update_item_tool, mock_db):
        """Test updating ticket status."""
        request_data = {"table": "tickets", "id": "1", "item": {"status": "solved"}}

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        assert result["item"]["status"] == "solved"

    @pytest.mark.anyio
    async def test_update_multiple_fields(self, update_item_tool, mock_db):
        """Test updating multiple fields at once."""
        request_data = {
            "table": "tickets",
            "id": "1",
            "item": {
                "priority": "high",
                "status": "pending",
                "subject": "Updated subject",
            },
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        assert result["item"]["priority"] == "high"
        assert result["item"]["status"] == "pending"
        assert result["item"]["subject"] == "Updated subject"

    @pytest.mark.anyio
    async def test_update_nonexistent_ticket(self, update_item_tool, mock_db):
        """Test updating non-existent ticket (error scenario)."""
        request_data = {
            "table": "tickets",
            "id": "999999999",
            "item": {"priority": "high"},
        }

        with pytest.raises(
            update_item_tool.ExecutionError, match="Item with ID '999999999' not found"
        ):
            await update_item_tool.run_with_validation(mock_db, request_data)

    @pytest.mark.anyio
    async def test_update_user(self, update_item_tool, mock_db):
        """Test updating a user."""
        request_data = {
            "table": "users",
            "id": "1",
            "item": {"name": "Updated Name", "role": "agent"},
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        assert result["item"]["name"] == "Updated Name"
        assert result["item"]["role"] == "agent"
        assert result["item"]["email"] == "original@example.com"  # Unchanged

    @pytest.mark.anyio
    async def test_update_ticket_comment_not_allowed(self, update_item_tool, mock_db):
        """Test that updating ticket comments is not allowed."""
        request_data = {
            "table": "ticket_comments",
            "id": "23118465221916",
            "item": {"body": "Updated comment"},
        }

        with pytest.raises(
            update_item_tool.ExecutionError,
            match="The value is not updatable. Ticket comments cannot be modified.",
        ):
            await update_item_tool.run_with_validation(mock_db, request_data)

    @pytest.mark.anyio
    async def test_update_unsupported_table(self, update_item_tool, mock_db):
        """Test updating item in unsupported table."""
        request_data = {
            "table": "articles",  # Valid enum value but not supported for CRUD
            "id": "1",
            "item": {"field": "value"},
        }

        with pytest.raises(update_item_tool.ExecutionError, match="Unsupported table"):
            await update_item_tool.run_with_validation(mock_db, request_data)

    @pytest.mark.anyio
    async def test_update_ticket_with_enum_validation(self, update_item_tool, mock_db):
        """Test that ticket update validates enums correctly."""
        # Valid enum values should work
        request_data = {
            "table": "tickets",
            "id": "1",
            "item": {"status": "solved", "priority": "high", "type": "incident"},
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        assert result["item"]["status"] == "solved"
        assert result["item"]["priority"] == "high"
        assert result["item"]["type"] == "incident"

    @pytest.mark.anyio
    async def test_update_user_with_role_validation(self, update_item_tool, mock_db):
        """Test that user update validates role enum correctly."""
        request_data = {"table": "users", "id": "1", "item": {"role": "admin"}}

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        assert result["item"]["role"] == "admin"

    @pytest.mark.anyio
    async def test_update_organization_with_multiple_domains(
        self, update_item_tool, mock_db
    ):
        """Test updating organization with list of domains."""
        # Add an organization to the database
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import (
            Organization,
        )

        org = Organization(
            id="1",
            name="Test Org",
            domain_names=["test.com"],
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        # Directly add to store since create() might not work in test db
        mock_db._store[Organization].append(org)

        request_data = {
            "table": "organizations",
            "id": "1",
            "item": {"domain_names": ["test.com", "test.net", "test.org"]},
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        assert result["item"]["domain_names"] == ["test.com", "test.net", "test.org"]

    @pytest.mark.anyio
    async def test_update_comment_public_flag(self, update_item_tool, mock_db):
        """Test updating comment public flag."""
        # Add a comment to the database
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import Comment

        comment = Comment(
            id="1",
            ticket_id="1",
            author_id="1",
            body="Original comment",
            public=True,
            created_at="2025-01-01T00:00:00Z",
        )
        # Directly add to store since create() might not work in test db
        mock_db._store[Comment].append(comment)

        request_data = {
            "table": "comments",
            "id": "1",
            "item": {"public": False, "body": "Updated comment body"},
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        assert result["item"]["public"] is False
        assert result["item"]["body"] == "Updated comment body"

    @pytest.mark.anyio
    async def test_update_ticket_with_null_tags(self, update_item_tool, mock_db):
        """Test updating a ticket with tags=null should preserve existing tags."""
        # First, set some tags on the ticket
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import Ticket

        ticket = mock_db.get_by_id(Ticket, "1")
        ticket.tags = ["existing", "tags"]
        mock_db.update(ticket)

        # This simulates UI sending "tags": null when the field is unchanged
        request_data = {
            "table": "tickets",
            "id": "1",
            "item": {"tags": None, "status": "solved"},
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        # Should preserve existing tags when null is sent
        assert result["item"]["tags"] == ["existing", "tags"]
        assert result["item"]["status"] == "solved"

        # Verify the ticket is persisted correctly in the database
        ticket = mock_db.get_by_id(Ticket, "1")
        assert ticket.tags == ["existing", "tags"]
        assert ticket.status == "solved"

    @pytest.mark.anyio
    async def test_update_ticket_tags_filtered_and_sorted(
        self, update_item_tool, mock_db
    ):
        """When tags list is provided, ignored tags should not be stored in DB but should appear in output; remaining tags should be sorted in DB."""
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import Ticket

        request_data = {
            "table": "tickets",
            "id": "1",
            "item": {
                "tags": [
                    "urgent",
                    "VIP-Customer",
                    "Hardware",
                    "repeat-ISSUE",
                    "printer",
                ],
            },
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        # Output should contain original unfiltered tags
        assert result["item"]["tags"] == [
            "urgent",
            "VIP-Customer",
            "Hardware",
            "repeat-ISSUE",
            "printer",
        ]

        # Database should only contain filtered and sorted tags (ignored tags removed)
        ticket = mock_db.get_by_id(Ticket, "1")
        assert ticket.tags == ["Hardware", "printer", "urgent"]

    @pytest.mark.anyio
    async def test_update_organization_with_null_domain_names(
        self, update_item_tool, mock_db
    ):
        """Test updating an organization with domain_names=null should preserve existing domains."""
        # Add an organization to the database
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import (
            Organization,
        )

        org = Organization(
            id="1",
            name="Test Org",
            domain_names=["test.com", "example.com"],
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        mock_db._store[Organization].append(org)

        # Update with null domain_names (simulates UI behavior where field is unchanged)
        request_data = {
            "table": "organizations",
            "id": "1",
            "item": {"domain_names": None, "name": "Updated Org"},
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        # Should preserve existing domain_names when null is sent
        assert result["item"]["domain_names"] == ["test.com", "example.com"]
        assert result["item"]["name"] == "Updated Org"

        # Verify the organization is persisted correctly in the database
        org = mock_db.get_by_id(Organization, "1")
        assert org.domain_names == ["test.com", "example.com"]
        assert org.name == "Updated Org"

    @pytest.mark.anyio
    async def test_update_ticket_tags_with_null_does_not_affect_other_fields(
        self, update_item_tool, mock_db
    ):
        """Test that updating tags with null preserves tags and updates other fields."""
        # Update the existing ticket with some tags first
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import Ticket

        ticket = mock_db.get_by_id(Ticket, "1")
        ticket.tags = ["existing", "tags"]
        mock_db.update(ticket)

        # Now update with null tags and another field
        request_data = {
            "table": "tickets",
            "id": "1",
            "item": {"tags": None, "priority": "high"},
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        # Should preserve tags and update priority
        assert result["item"]["tags"] == ["existing", "tags"]
        assert result["item"]["priority"] == "high"
        assert result["item"]["subject"] == "Original subject"  # Unchanged

    @pytest.mark.anyio
    async def test_update_ticket_with_null_subject(self, update_item_tool, mock_db):
        """Test updating ticket with subject=null should keep existing subject (not fail validation)."""
        # Update with null subject (simulates UI behavior)
        request_data = {
            "table": "tickets",
            "id": "1",
            "item": {"subject": None, "priority": "high"},
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        # Should keep existing subject (not overwrite with null) and update priority
        assert result["item"]["subject"] == "Original subject"
        assert result["item"]["priority"] == "high"

        # Verify the ticket is persisted correctly in the database
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import Ticket

        ticket = mock_db.get_by_id(Ticket, "1")
        assert ticket.subject == "Original subject"
        assert ticket.priority == "high"

    @pytest.mark.anyio
    async def test_update_user_with_null_name(self, update_item_tool, mock_db):
        """Test updating user with name=null should keep existing name (not fail validation)."""
        # Update with null name (simulates UI behavior)
        request_data = {
            "table": "users",
            "id": "1",
            "item": {"name": None, "phone": "+1-555-1234"},
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        # Should keep existing name (not overwrite with null) and update phone
        assert result["item"]["name"] == "Original Name"
        assert result["item"]["phone"] == "+1-555-1234"

        # Verify the user is persisted correctly in the database
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import User

        user = mock_db.get_by_id(User, "1")
        assert user.name == "Original Name"
        assert user.phone == "+1-555-1234"

    @pytest.mark.anyio
    async def test_update_user_with_null_email(self, update_item_tool, mock_db):
        """Test updating user with email=null should keep existing email (not fail validation)."""
        # Update with null email (simulates UI behavior)
        request_data = {
            "table": "users",
            "id": "1",
            "item": {"email": None, "verified": False},
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        # Should keep existing email (not overwrite with null) and update verified
        assert result["item"]["email"] == "original@example.com"
        assert result["item"]["verified"] is False

        # Verify the user is persisted correctly in the database
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import User

        user = mock_db.get_by_id(User, "1")
        assert user.email == "original@example.com"
        assert user.verified is False

    @pytest.mark.anyio
    async def test_update_with_multiple_null_fields(self, update_item_tool, mock_db):
        """Test updating with multiple null fields should keep existing values for all null fields."""
        # First set some tags
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import Ticket

        ticket = mock_db.get_by_id(Ticket, "1")
        ticket.tags = ["important", "urgent"]
        mock_db.update(ticket)

        # Update with multiple null fields (simulates UI behavior)
        request_data = {
            "table": "tickets",
            "id": "1",
            "item": {
                "subject": None,
                "description": None,
                "tags": None,
                "priority": "urgent",
            },
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        # Should keep existing values for all null fields and update priority
        assert result["item"]["subject"] == "Original subject"
        assert result["item"]["description"] == "Original description"
        assert result["item"]["tags"] == [
            "important",
            "urgent",
        ]  # Preserve existing tags
        assert result["item"]["priority"] == "urgent"

        # Verify the ticket is persisted correctly in the database
        ticket = mock_db.get_by_id(Ticket, "1")
        assert ticket.subject == "Original subject"
        assert ticket.description == "Original description"
        assert ticket.tags == ["important", "urgent"]
        assert ticket.priority == "urgent"

    @pytest.mark.anyio
    async def test_update_ticket_status_preserves_tags(self, update_item_tool, mock_db):
        """Test the specific user scenario: create ticket with tags, update status with tags=null."""
        # Create a ticket with tags
        from tb_business_ops_servers_202606.toolslib.external_booking.zendesk.models import Ticket

        ticket_with_tags = Ticket(
            id="7",
            subject="Test ticket",
            description="Test description",
            status="open",
            priority="normal",
            tags=["important", "customer-request"],
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        mock_db._store[Ticket].append(ticket_with_tags)

        # Update only the status with all other fields as null (simulates UI behavior)
        request_data = {
            "table": "tickets",
            "id": "7",
            "item": {
                "subject": None,
                "description": None,
                "status": "solved",
                "priority": None,
                "type": None,
                "requester_id": None,
                "assignee_id": None,
                "organization_id": None,
                "tags": None,
                "due_at": None,
            },
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        # Tags should be preserved, only status should change
        assert result["item"]["tags"] == ["important", "customer-request"]
        assert result["item"]["status"] == "solved"
        assert result["item"]["subject"] == "Test ticket"
        assert result["item"]["description"] == "Test description"

        # Verify in database
        ticket = mock_db.get_by_id(Ticket, "7")
        assert ticket.tags == ["important", "customer-request"]
        assert ticket.status == "solved"

    @pytest.mark.anyio
    async def test_update_ticket_with_custom_fields(self, update_item_tool, mock_db):
        """Test updating a ticket with booking-specific custom fields."""
        request_data = {
            "table": "tickets",
            "id": "1",
            "item": {
                "booking_reference": "BKG-12345678",
                "hotel_id": "HTL-87654321",
                "request_type_detail": "modify-dates",
            },
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        assert result["item"]["booking_reference"] == "BKG-12345678"
        assert result["item"]["hotel_id"] == "HTL-87654321"
        assert result["item"]["request_type_detail"] == "modify-dates"
        # Original fields should be unchanged
        assert result["item"]["subject"] == "Original subject"

    @pytest.mark.anyio
    async def test_update_ticket_with_all_custom_field_types(
        self, update_item_tool, mock_db
    ):
        """Test updating with all booking-specific custom field types."""
        request_data = {
            "table": "tickets",
            "id": "1",
            "item": {
                "booking_reference": "BKG-12345678",
                "hotel_id": "HTL-87654321",
                "check_in_date": "2025-01-15T14:00:00Z",
                "booking_value": 1250.00,
                "request_type_detail": "modify-dates",
                "corporate_account_id": "CRP-12345678",
                "group_booking_id": "GRP-12345678",
                "resolution_action": "refund-partial",
                "refund_amount": 250.00,
                "escalation_reason": "hotel-confirmation-required",
            },
        }

        result = await update_item_tool.run_with_validation(mock_db, request_data)

        # Verify all booking-specific custom fields were updated
        assert result["item"]["booking_reference"] == "BKG-12345678"
        assert result["item"]["hotel_id"] == "HTL-87654321"
        assert result["item"]["check_in_date"] == "2025-01-15T14:00:00Z"
        assert result["item"]["booking_value"] == 1250.00
        assert result["item"]["request_type_detail"] == "modify-dates"
        assert result["item"]["corporate_account_id"] == "CRP-12345678"
        assert result["item"]["group_booking_id"] == "GRP-12345678"
        assert result["item"]["resolution_action"] == "refund-partial"
        assert result["item"]["refund_amount"] == 250.00
        assert result["item"]["escalation_reason"] == "hotel-confirmation-required"
