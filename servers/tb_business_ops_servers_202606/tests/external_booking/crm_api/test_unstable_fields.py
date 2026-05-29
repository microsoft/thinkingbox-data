# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for unstable fields in CRM API tools.

This test validates that fields marked as UnstableField are properly excluded
from database hash calculations during test case validation.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.crm_api.models import (
    CustomerProfile,
    VipTier,
)
from tb_business_ops_servers_202606.utils.db_utils import calculate_database_hash
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestUnstableFields:
    """Test that unstable fields are properly excluded from database hashes."""

    def _create_test_db(self):
        """Create a test database with CustomerProfile models."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "customer_profiles": CustomerProfile,
        }
        db._model_cls_to_stem = {
            CustomerProfile: "customer_profiles",
        }
        db._store = {
            CustomerProfile: [],
        }
        return db

    @pytest.mark.anyio
    async def test_preferences_and_special_notes_fields_are_unstable(self):
        """Verify that preferences and special_notes fields are marked as unstable in CustomerProfile model."""
        unstable_fields = UnstableField.extract_names(CustomerProfile)
        assert (
            "preferences" in unstable_fields
        ), "preferences field should be marked as UnstableField"
        assert (
            "special_notes" in unstable_fields
        ), "special_notes field should be marked as UnstableField"

    @pytest.mark.anyio
    async def test_created_at_and_updated_at_fields_are_stable(self):
        """Verify that created_at and updated_at fields are NOT marked as unstable in CustomerProfile model."""
        unstable_fields = UnstableField.extract_names(CustomerProfile)
        assert (
            "created_at" not in unstable_fields
        ), "created_at field should NOT be marked as UnstableField"
        assert (
            "updated_at" not in unstable_fields
        ), "updated_at field should NOT be marked as UnstableField"

    @pytest.mark.anyio
    async def test_hash_unchanged_when_preferences_differs(self):
        """Test that database hashes are identical when only preferences differs.

        This test creates two databases with customer profiles that have different preferences.
        The database hashes should be the same because preferences is an
        unstable field that's excluded from hash calculation.
        """
        # Create first database
        db1 = self._create_test_db()

        profile1 = CustomerProfile(
            id="PROF-00000001",
            customer_id="CUS-00000001",
            email="customer@example.com",
            full_name="John Doe",
            vip_tier=VipTier.VIP,
            loyalty_program_status="Gold Member",
            lifetime_value=Decimal("5000.00"),
            total_bookings_count=10,
            preferences=["Ocean view", "Non-smoking", "High floor"],
            special_notes=["Allergic to feather pillows"],
            complaint_count=0,
            last_booking_date=datetime(2025, 1, 15, 10, 0, 0),
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 15, 10, 0, 0),
        )
        db1.create(profile1)

        # Create second database
        db2 = self._create_test_db()

        profile2 = CustomerProfile(
            id="PROF-00000001",
            customer_id="CUS-00000001",
            email="customer@example.com",
            full_name="John Doe",
            vip_tier=VipTier.VIP,
            loyalty_program_status="Gold Member",
            lifetime_value=Decimal("5000.00"),
            total_bookings_count=10,
            preferences=["Mountain view", "Pet-friendly", "Ground floor"],
            special_notes=["Allergic to feather pillows"],
            complaint_count=0,
            last_booking_date=datetime(2025, 1, 15, 10, 0, 0),
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 15, 10, 0, 0),
        )
        db2.create(profile2)

        # Get profiles from both databases to verify they exist and differ
        profiles_db1 = db1.get_all(CustomerProfile)
        profiles_db2 = db2.get_all(CustomerProfile)

        assert len(profiles_db1) == 1, "First database should have 1 profile"
        assert len(profiles_db2) == 1, "Second database should have 1 profile"
        assert (
            profiles_db1[0].preferences != profiles_db2[0].preferences
        ), "Preferences should be different"

        # Calculate hashes (with unstable fields excluded by default)
        hash1 = calculate_database_hash(db1)
        hash2 = calculate_database_hash(db2)

        # Hashes should be identical because preferences is unstable
        assert hash1 == hash2, (
            f"Database hashes should be identical when only unstable fields differ. "
            f"Hash1: {hash1}, Hash2: {hash2}"
        )

    @pytest.mark.anyio
    async def test_hash_unchanged_when_special_notes_differs(self):
        """Test that database hashes are identical when only special_notes differs.

        This test creates two databases with customer profiles that have different special_notes.
        The database hashes should be the same because special_notes is an
        unstable field that's excluded from hash calculation.
        """
        # Create first database
        db1 = self._create_test_db()

        profile1 = CustomerProfile(
            id="PROF-00000001",
            customer_id="CUS-00000001",
            email="customer@example.com",
            full_name="John Doe",
            vip_tier=VipTier.VIP,
            loyalty_program_status="Gold Member",
            lifetime_value=Decimal("5000.00"),
            total_bookings_count=10,
            preferences=["Ocean view"],
            special_notes=["Regular customer, prefers late checkout"],
            complaint_count=0,
            last_booking_date=datetime(2025, 1, 15, 10, 0, 0),
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 15, 10, 0, 0),
        )
        db1.create(profile1)

        # Create second database
        db2 = self._create_test_db()

        profile2 = CustomerProfile(
            id="PROF-00000001",
            customer_id="CUS-00000001",
            email="customer@example.com",
            full_name="John Doe",
            vip_tier=VipTier.VIP,
            loyalty_program_status="Gold Member",
            lifetime_value=Decimal("5000.00"),
            total_bookings_count=10,
            preferences=["Ocean view"],
            special_notes=[
                "VIP guest, requires special attention",
                "Previous complaint resolved",
            ],
            complaint_count=0,
            last_booking_date=datetime(2025, 1, 15, 10, 0, 0),
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 15, 10, 0, 0),
        )
        db2.create(profile2)

        # Get profiles from both databases to verify they exist and differ
        profiles_db1 = db1.get_all(CustomerProfile)
        profiles_db2 = db2.get_all(CustomerProfile)

        assert len(profiles_db1) == 1, "First database should have 1 profile"
        assert len(profiles_db2) == 1, "Second database should have 1 profile"
        assert (
            profiles_db1[0].special_notes != profiles_db2[0].special_notes
        ), "Special notes should be different"

        # Calculate hashes (with unstable fields excluded by default)
        hash1 = calculate_database_hash(db1)
        hash2 = calculate_database_hash(db2)

        # Hashes should be identical because special_notes is unstable
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

        profile1 = CustomerProfile(
            id="PROF-00000001",
            customer_id="CUS-00000001",
            email="customer@example.com",
            full_name="John Doe",
            vip_tier=VipTier.VIP,
            loyalty_program_status="Gold Member",
            lifetime_value=Decimal("5000.00"),
            total_bookings_count=10,
            preferences=["Ocean view"],
            special_notes=["Regular customer"],
            complaint_count=0,
            last_booking_date=datetime(2025, 1, 15, 10, 0, 0),
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 15, 10, 0, 0),
        )
        db1.create(profile1)

        # Create second database
        db2 = self._create_test_db()

        profile2 = CustomerProfile(
            id="PROF-00000001",
            customer_id="CUS-00000001",
            email="customer@example.com",
            full_name="John Doe",
            vip_tier=VipTier.PLATINUM,  # Different VIP tier (stable field)
            loyalty_program_status="Gold Member",
            lifetime_value=Decimal("5000.00"),
            total_bookings_count=10,
            preferences=["Ocean view"],
            special_notes=["Regular customer"],
            complaint_count=0,
            last_booking_date=datetime(2025, 1, 15, 10, 0, 0),
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 15, 10, 0, 0),
        )
        db2.create(profile2)

        # Calculate hashes
        hash1 = calculate_database_hash(db1)
        hash2 = calculate_database_hash(db2)

        # Hashes should be different because vip_tier is a stable field
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

        profile1 = CustomerProfile(
            id="PROF-00000001",
            customer_id="CUS-00000001",
            email="customer@example.com",
            full_name="John Doe",
            vip_tier=VipTier.VIP,
            loyalty_program_status="Gold Member",
            lifetime_value=Decimal("5000.00"),
            total_bookings_count=10,
            preferences=["First preference set"],
            special_notes=["First note set"],
            complaint_count=0,
            last_booking_date=datetime(2025, 1, 15, 10, 0, 0),
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 15, 10, 0, 0),
        )
        db1.create(profile1)

        # Create second database
        db2 = self._create_test_db()

        profile2 = CustomerProfile(
            id="PROF-00000001",
            customer_id="CUS-00000001",
            email="customer@example.com",
            full_name="John Doe",
            vip_tier=VipTier.VIP,
            loyalty_program_status="Gold Member",
            lifetime_value=Decimal("5000.00"),
            total_bookings_count=10,
            preferences=["Different preference set"],
            special_notes=["Different note set"],
            complaint_count=0,
            last_booking_date=datetime(2025, 1, 15, 10, 0, 0),
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 15, 10, 0, 0),
        )
        db2.create(profile2)

        # Calculate hashes with unstable fields included
        hash1 = calculate_database_hash(db1, exclude_unstable_fields=False)
        hash2 = calculate_database_hash(db2, exclude_unstable_fields=False)

        # Hashes should be different because preferences and special_notes are included in the hash
        assert hash1 != hash2, (
            f"Database hashes should differ when unstable fields are included. "
            f"Hash1: {hash1}, Hash2: {hash2}"
        )
