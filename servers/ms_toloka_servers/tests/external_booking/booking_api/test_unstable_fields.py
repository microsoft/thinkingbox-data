# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for unstable fields in Booking API tools.

This test validates that fields marked as UnstableField are properly excluded
from database hash calculations during test case validation.
"""

from decimal import Decimal

import pytest
from ms_toloka_servers.toolslib.external_booking.booking_api.models import (
    BoardType,
    Booking,
    BookingStatus,
    RoomType,
)
from ms_toloka_servers.utils.db_utils import calculate_database_hash
from ms_toloka_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestUnstableFields:
    """Test that unstable fields are properly excluded from database hashes."""

    def _create_test_db(self):
        """Create a test database with Booking models."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "bookings": Booking,
        }
        db._model_cls_to_stem = {
            Booking: "bookings",
        }
        db._store = {
            Booking: [],
        }
        return db

    @pytest.mark.anyio
    async def test_special_requests_field_is_unstable(self):
        """Verify that special_requests field is marked as unstable in Booking model."""
        unstable_fields = UnstableField.extract_names(Booking)
        assert (
            "special_requests" in unstable_fields
        ), "special_requests field should be marked as UnstableField"

    @pytest.mark.anyio
    async def test_created_at_and_updated_at_fields_are_stable(self):
        """Verify that created_at and updated_at fields are NOT marked as unstable in Booking model."""
        unstable_fields = UnstableField.extract_names(Booking)
        assert (
            "created_at" not in unstable_fields
        ), "created_at field should NOT be marked as UnstableField"
        assert (
            "updated_at" not in unstable_fields
        ), "updated_at field should NOT be marked as UnstableField"

    @pytest.mark.anyio
    async def test_hash_unchanged_when_special_requests_differs(self):
        """Test that database hashes are identical when only special_requests differs.

        This test creates two databases with bookings that have different special_requests.
        The database hashes should be the same because special_requests is an
        unstable field that's excluded from hash calculation.
        """
        # Create first database
        db1 = self._create_test_db()

        booking1 = Booking(
            id="BKG-00000001",
            booking_reference="REF-001",
            customer_id="CUS-001",
            hotel_id="HTL-001",
            check_in_date="2025-02-01T14:00:00Z",
            check_out_date="2025-02-05T11:00:00Z",
            booking_value=Decimal("500.00"),
            room_type=RoomType.STANDARD_ROOM,
            board_type=BoardType.WITH_BREAKFAST,
            adults_count=2,
            children_count=0,
            booking_status=BookingStatus.CONFIRMED,
            special_requests=["Early check-in", "High floor"],
            created_at="2025-01-15T10:00:00Z",
            updated_at="2025-01-15T10:00:00Z",
        )
        db1.create(booking1)

        # Create second database
        db2 = self._create_test_db()

        booking2 = Booking(
            id="BKG-00000001",
            booking_reference="REF-001",
            customer_id="CUS-001",
            hotel_id="HTL-001",
            check_in_date="2025-02-01T14:00:00Z",
            check_out_date="2025-02-05T11:00:00Z",
            booking_value=Decimal("500.00"),
            room_type=RoomType.STANDARD_ROOM,
            board_type=BoardType.WITH_BREAKFAST,
            adults_count=2,
            children_count=0,
            booking_status=BookingStatus.CONFIRMED,
            special_requests=["Late checkout", "Extra pillows", "Quiet room"],
            created_at="2025-01-15T10:00:00Z",
            updated_at="2025-01-15T10:00:00Z",
        )
        db2.create(booking2)

        # Get bookings from both databases to verify they exist and differ
        bookings_db1 = db1.get_all(Booking)
        bookings_db2 = db2.get_all(Booking)

        assert len(bookings_db1) == 1, "First database should have 1 booking"
        assert len(bookings_db2) == 1, "Second database should have 1 booking"
        assert (
            bookings_db1[0].special_requests != bookings_db2[0].special_requests
        ), "Special requests should be different"

        # Calculate hashes (with unstable fields excluded by default)
        hash1 = calculate_database_hash(db1)
        hash2 = calculate_database_hash(db2)

        # Hashes should be identical because special_requests is unstable
        assert hash1 == hash2, (
            f"Database hashes should be identical when only unstable fields differ. "
            f"Hash1: {hash1}, Hash2: {hash2}"
        )

    @pytest.mark.anyio
    async def test_hash_changes_when_stable_field_differs(self):
        """Test that database hashes differ when stable fields change.

        This test verifies that the hash calculation still works correctly for
        stable fields - when a stable field changes, the hash should differ.
        """
        # Create first database
        db1 = self._create_test_db()

        booking1 = Booking(
            id="BKG-00000001",
            booking_reference="REF-001",
            customer_id="CUS-001",
            hotel_id="HTL-001",
            check_in_date="2025-02-01T14:00:00Z",
            check_out_date="2025-02-05T11:00:00Z",
            booking_value=Decimal("500.00"),
            room_type=RoomType.STANDARD_ROOM,
            board_type=BoardType.WITH_BREAKFAST,
            adults_count=2,
            children_count=0,
            booking_status=BookingStatus.CONFIRMED,
            special_requests=["Early check-in"],
            created_at="2025-01-15T10:00:00Z",
            updated_at="2025-01-15T10:00:00Z",
        )
        db1.create(booking1)

        # Create second database
        db2 = self._create_test_db()

        booking2 = Booking(
            id="BKG-00000001",
            booking_reference="REF-001",
            customer_id="CUS-001",
            hotel_id="HTL-001",
            check_in_date="2025-02-01T14:00:00Z",
            check_out_date="2025-02-05T11:00:00Z",
            booking_value=Decimal("500.00"),
            room_type=RoomType.DELUXE_ROOM,  # Different room type (stable field)
            board_type=BoardType.WITH_BREAKFAST,
            adults_count=2,
            children_count=0,
            booking_status=BookingStatus.CONFIRMED,
            special_requests=["Early check-in"],
            created_at="2025-01-15T10:00:00Z",
            updated_at="2025-01-15T10:00:00Z",
        )
        db2.create(booking2)

        # Calculate hashes
        hash1 = calculate_database_hash(db1)
        hash2 = calculate_database_hash(db2)

        # Hashes should be different because room_type is a stable field
        assert hash1 != hash2, (
            f"Database hashes should differ when stable fields change. "
            f"Hash1: {hash1}, Hash2: {hash2}"
        )

    @pytest.mark.anyio
    async def test_hash_includes_unstable_fields_when_requested(self):
        """Test that unstable fields can be included in hash when explicitly requested.

        This verifies that the exclude_unstable_fields parameter works correctly.
        """
        # Create first database
        db1 = self._create_test_db()

        booking1 = Booking(
            id="BKG-00000001",
            booking_reference="REF-001",
            customer_id="CUS-001",
            hotel_id="HTL-001",
            check_in_date="2025-02-01T14:00:00Z",
            check_out_date="2025-02-05T11:00:00Z",
            booking_value=Decimal("500.00"),
            room_type=RoomType.STANDARD_ROOM,
            board_type=BoardType.WITH_BREAKFAST,
            adults_count=2,
            children_count=0,
            booking_status=BookingStatus.CONFIRMED,
            special_requests=["First request"],
            created_at="2025-01-15T10:00:00Z",
            updated_at="2025-01-15T10:00:00Z",
        )
        db1.create(booking1)

        # Create second database
        db2 = self._create_test_db()

        booking2 = Booking(
            id="BKG-00000001",
            booking_reference="REF-001",
            customer_id="CUS-001",
            hotel_id="HTL-001",
            check_in_date="2025-02-01T14:00:00Z",
            check_out_date="2025-02-05T11:00:00Z",
            booking_value=Decimal("500.00"),
            room_type=RoomType.STANDARD_ROOM,
            board_type=BoardType.WITH_BREAKFAST,
            adults_count=2,
            children_count=0,
            booking_status=BookingStatus.CONFIRMED,
            special_requests=["Different request"],
            created_at="2025-01-15T10:00:00Z",
            updated_at="2025-01-15T10:00:00Z",
        )
        db2.create(booking2)

        # Calculate hashes with unstable fields included
        hash1 = calculate_database_hash(db1, exclude_unstable_fields=False)
        hash2 = calculate_database_hash(db2, exclude_unstable_fields=False)

        # Hashes should be different because special_requests is included in the hash
        assert hash1 != hash2, (
            f"Database hashes should differ when unstable fields are included. "
            f"Hash1: {hash1}, Hash2: {hash2}"
        )
