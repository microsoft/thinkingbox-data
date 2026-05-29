# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for unstable fields in Zendesk tools.

This test validates that fields marked as UnstableField are properly excluded
from database hash calculations during test case validation.
"""

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.zendesk.models import (
    Organization,
    Ticket,
    User,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.zendesk.tools.create_item import (
    CreateItemTool,
)
from tb_business_ops_servers_202606.utils.db_utils import calculate_database_hash
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestUnstableFields:
    """Test that unstable fields are properly excluded from database hashes."""

    @pytest.fixture
    def create_item_tool(self):
        """Create an instance of CreateItemTool."""
        return CreateItemTool()

    def _create_test_db(self):
        """Create a test database with Zendesk models."""
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

    @pytest.mark.anyio
    async def test_subject_and_description_fields_are_unstable(self):
        """Verify that subject and description fields are marked as unstable in Ticket model."""
        unstable_fields = UnstableField.extract_names(Ticket)
        assert (
            "subject" in unstable_fields
        ), "subject field should be marked as UnstableField"
        assert (
            "description" in unstable_fields
        ), "description field should be marked as UnstableField"

    @pytest.mark.anyio
    async def test_created_at_and_updated_at_fields_are_stable(self):
        """Verify that created_at and updated_at fields are NOT marked as unstable in Ticket model."""
        unstable_fields = UnstableField.extract_names(Ticket)
        assert (
            "created_at" not in unstable_fields
        ), "created_at field should NOT be marked as UnstableField"
        assert (
            "updated_at" not in unstable_fields
        ), "updated_at field should NOT be marked as UnstableField"

    @pytest.mark.anyio
    async def test_hash_unchanged_when_subject_differs(self, create_item_tool):
        """Test that database hashes are identical when only subject differs.

        This test creates two databases and creates tickets with different subjects
        in each. The database hashes should be the same because subject is an
        unstable field that's excluded from hash calculation.
        """
        # Create first database
        db1 = self._create_test_db()

        # Create ticket with first subject
        request_data_1 = {
            "table": "tickets",
            "item": {
                "subject": "First ticket subject",
                "description": "Same description",
                "priority": "high",
                "status": "open",
            },
        }
        await create_item_tool.run_with_validation(db1, request_data_1)

        # Create second database
        db2 = self._create_test_db()

        # Create ticket with different subject
        request_data_2 = {
            "table": "tickets",
            "item": {
                "subject": "Completely different ticket subject",
                "description": "Same description",
                "priority": "high",
                "status": "open",
            },
        }
        await create_item_tool.run_with_validation(db2, request_data_2)

        # Get tickets from both databases to verify they exist and differ
        tickets_db1 = db1.get_all(Ticket)
        tickets_db2 = db2.get_all(Ticket)

        assert len(tickets_db1) == 1, "First database should have 1 ticket"
        assert len(tickets_db2) == 1, "Second database should have 1 ticket"
        assert (
            tickets_db1[0].subject != tickets_db2[0].subject
        ), "Subjects should be different"

        # Calculate hashes (with unstable fields excluded by default)
        hash1 = calculate_database_hash(db1)
        hash2 = calculate_database_hash(db2)

        # Hashes should be identical because subject is unstable
        assert hash1 == hash2, (
            f"Database hashes should be identical when only unstable fields differ. "
            f"Hash1: {hash1}, Hash2: {hash2}"
        )

    @pytest.mark.anyio
    async def test_hash_unchanged_when_description_differs(self, create_item_tool):
        """Test that database hashes are identical when only description differs.

        This test creates two databases and creates tickets with different descriptions
        in each. The database hashes should be the same because description is an
        unstable field that's excluded from hash calculation.
        """
        # Create first database
        db1 = self._create_test_db()

        # Create ticket with first description
        request_data_1 = {
            "table": "tickets",
            "item": {
                "subject": "Test ticket",
                "description": "This is the first description",
                "priority": "high",
                "status": "open",
            },
        }
        await create_item_tool.run_with_validation(db1, request_data_1)

        # Create second database
        db2 = self._create_test_db()

        # Create ticket with different description
        request_data_2 = {
            "table": "tickets",
            "item": {
                "subject": "Test ticket",
                "description": "This is a completely different description",
                "priority": "high",
                "status": "open",
            },
        }
        await create_item_tool.run_with_validation(db2, request_data_2)

        # Get tickets from both databases to verify they exist and differ
        tickets_db1 = db1.get_all(Ticket)
        tickets_db2 = db2.get_all(Ticket)

        assert len(tickets_db1) == 1, "First database should have 1 ticket"
        assert len(tickets_db2) == 1, "Second database should have 1 ticket"
        assert (
            tickets_db1[0].description != tickets_db2[0].description
        ), "Descriptions should be different"

        # Calculate hashes (with unstable fields excluded by default)
        hash1 = calculate_database_hash(db1)
        hash2 = calculate_database_hash(db2)

        # Hashes should be identical because description is unstable
        assert hash1 == hash2, (
            f"Database hashes should be identical when only unstable fields differ. "
            f"Hash1: {hash1}, Hash2: {hash2}"
        )

    @pytest.mark.anyio
    async def test_hash_changes_when_stable_field_differs(self, create_item_tool):
        """Test that database hashes differ when stable fields change.

        This test verifies that the hash calculation still works correctly for
        stable fields - when a stable field changes, the hash should differ.
        """
        # Create first database
        db1 = self._create_test_db()

        # Create ticket with first priority
        request_data_1 = {
            "table": "tickets",
            "item": {
                "subject": "Test ticket",
                "description": "Same description",
                "priority": "high",
                "status": "open",
            },
        }
        await create_item_tool.run_with_validation(db1, request_data_1)

        # Create second database
        db2 = self._create_test_db()

        # Create ticket with different priority (stable field)
        request_data_2 = {
            "table": "tickets",
            "item": {
                "subject": "Test ticket",
                "description": "Same description",
                "priority": "low",  # Different priority
                "status": "open",
            },
        }
        await create_item_tool.run_with_validation(db2, request_data_2)

        # Calculate hashes
        hash1 = calculate_database_hash(db1)
        hash2 = calculate_database_hash(db2)

        # Hashes should be different because priority is a stable field
        assert hash1 != hash2, (
            f"Database hashes should differ when stable fields change. "
            f"Hash1: {hash1}, Hash2: {hash2}"
        )

    @pytest.mark.anyio
    async def test_hash_includes_unstable_fields_when_requested(self, create_item_tool):
        """Test that unstable fields can be included in hash when explicitly requested.

        This verifies that the exclude_unstable_fields parameter works correctly.
        """
        # Create first database
        db1 = self._create_test_db()

        request_data_1 = {
            "table": "tickets",
            "item": {
                "subject": "First ticket subject",
                "description": "Same description",
                "priority": "high",
                "status": "open",
            },
        }
        await create_item_tool.run_with_validation(db1, request_data_1)

        # Create second database
        db2 = self._create_test_db()

        request_data_2 = {
            "table": "tickets",
            "item": {
                "subject": "Second ticket subject",
                "description": "Same description",
                "priority": "high",
                "status": "open",
            },
        }
        await create_item_tool.run_with_validation(db2, request_data_2)

        # Calculate hashes with unstable fields included
        hash1 = calculate_database_hash(db1, exclude_unstable_fields=False)
        hash2 = calculate_database_hash(db2, exclude_unstable_fields=False)

        # Hashes should be different because subject is included in the hash
        assert hash1 != hash2, (
            f"Database hashes should differ when unstable fields are included. "
            f"Hash1: {hash1}, Hash2: {hash2}"
        )

    @pytest.mark.anyio
    async def test_hash_changes_when_timestamps_differ(self, create_item_tool):
        """Test that database hashes differ when created_at or updated_at fields differ.

        This test verifies that created_at and updated_at are stable fields that affect
        the database hash calculation.
        """
        # Create first database
        db1 = self._create_test_db()

        # Manually create a ticket with specific timestamps
        ticket1 = Ticket(
            id="1",
            subject="Test ticket",
            description="Test description",
            status="open",
            priority="high",
            created_at="2025-10-01T13:00:05Z",
            updated_at="2025-10-01T13:00:05Z",
        )
        db1.create(ticket1)

        # Create second database
        db2 = self._create_test_db()

        # Create ticket with different updated_at timestamp
        ticket2 = Ticket(
            id="1",
            subject="Test ticket",
            description="Test description",
            status="open",
            priority="high",
            created_at="2025-10-01T13:00:05Z",
            updated_at="2025-10-01T13:00:10Z",  # Different timestamp
        )
        db2.create(ticket2)

        # Calculate hashes
        hash1 = calculate_database_hash(db1)
        hash2 = calculate_database_hash(db2)

        # Hashes should be different because updated_at is now a stable field
        assert hash1 != hash2, (
            f"Database hashes should differ when stable timestamp fields change. "
            f"Hash1: {hash1}, Hash2: {hash2}"
        )
