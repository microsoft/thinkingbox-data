# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Test for unstable fields in Payment API tools.

This test validates that fields marked as UnstableField are properly excluded
from database hash calculations during test case validation.
"""

from decimal import Decimal

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.payment_api.models import (
    PaymentStatus,
    Transaction,
    TransactionType,
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
        """Create a test database with Transaction models."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "transactions": Transaction,
        }
        db._model_cls_to_stem = {
            Transaction: "transactions",
        }
        db._store = {
            Transaction: [],
        }
        return db

    @pytest.mark.anyio
    async def test_reason_field_is_unstable(self):
        """Verify that reason field is marked as unstable in Transaction model."""
        unstable_fields = UnstableField.extract_names(Transaction)
        assert (
            "reason" in unstable_fields
        ), "reason field should be marked as UnstableField"

    @pytest.mark.anyio
    async def test_created_at_and_updated_at_fields_are_stable(self):
        """Verify that created_at and updated_at fields are NOT marked as unstable in Transaction model."""
        unstable_fields = UnstableField.extract_names(Transaction)
        assert (
            "created_at" not in unstable_fields
        ), "created_at field should NOT be marked as UnstableField"
        assert (
            "updated_at" not in unstable_fields
        ), "updated_at field should NOT be marked as UnstableField"

    @pytest.mark.anyio
    async def test_hash_unchanged_when_reason_differs(self):
        """Test that database hashes are identical when only reason differs.

        This test creates two databases with transactions that have different reasons.
        The database hashes should be the same because reason is an
        unstable field that's excluded from hash calculation.
        """
        # Create first database
        db1 = self._create_test_db()

        transaction1 = Transaction(
            id="TXN-00000001",
            transaction_id="TX-001",
            booking_reference="BKG-001",
            customer_id="CUS-001",
            amount=Decimal("100.00"),
            currency="USD",
            transaction_type=TransactionType.REFUND,
            payment_status=PaymentStatus.SUCCESSFUL,
            payment_method="credit_card",
            reason="Customer requested full refund due to cancellation",
            processing_time_estimate="3-5 business days",
            created_at="2025-01-15T10:00:00Z",
            updated_at="2025-01-15T10:00:00Z",
        )
        db1.create(transaction1)

        # Create second database
        db2 = self._create_test_db()

        transaction2 = Transaction(
            id="TXN-00000001",
            transaction_id="TX-001",
            booking_reference="BKG-001",
            customer_id="CUS-001",
            amount=Decimal("100.00"),
            currency="USD",
            transaction_type=TransactionType.REFUND,
            payment_status=PaymentStatus.SUCCESSFUL,
            payment_method="credit_card",
            reason="Policy violation - hotel cancelled booking",
            processing_time_estimate="3-5 business days",
            created_at="2025-01-15T10:00:00Z",
            updated_at="2025-01-15T10:00:00Z",
        )
        db2.create(transaction2)

        # Get transactions from both databases to verify they exist and differ
        transactions_db1 = db1.get_all(Transaction)
        transactions_db2 = db2.get_all(Transaction)

        assert len(transactions_db1) == 1, "First database should have 1 transaction"
        assert len(transactions_db2) == 1, "Second database should have 1 transaction"
        assert (
            transactions_db1[0].reason != transactions_db2[0].reason
        ), "Reasons should be different"

        # Calculate hashes (with unstable fields excluded by default)
        hash1 = calculate_database_hash(db1)
        hash2 = calculate_database_hash(db2)

        # Hashes should be identical because reason is unstable
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

        transaction1 = Transaction(
            id="TXN-00000001",
            transaction_id="TX-001",
            booking_reference="BKG-001",
            customer_id="CUS-001",
            amount=Decimal("100.00"),
            currency="USD",
            transaction_type=TransactionType.REFUND,
            payment_status=PaymentStatus.SUCCESSFUL,
            payment_method="credit_card",
            reason="Refund requested",
            processing_time_estimate="3-5 business days",
            created_at="2025-01-15T10:00:00Z",
            updated_at="2025-01-15T10:00:00Z",
        )
        db1.create(transaction1)

        # Create second database
        db2 = self._create_test_db()

        transaction2 = Transaction(
            id="TXN-00000001",
            transaction_id="TX-001",
            booking_reference="BKG-001",
            customer_id="CUS-001",
            amount=Decimal("150.00"),  # Different amount (stable field)
            currency="USD",
            transaction_type=TransactionType.REFUND,
            payment_status=PaymentStatus.SUCCESSFUL,
            payment_method="credit_card",
            reason="Refund requested",
            processing_time_estimate="3-5 business days",
            created_at="2025-01-15T10:00:00Z",
            updated_at="2025-01-15T10:00:00Z",
        )
        db2.create(transaction2)

        # Calculate hashes
        hash1 = calculate_database_hash(db1)
        hash2 = calculate_database_hash(db2)

        # Hashes should be different because amount is a stable field
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

        transaction1 = Transaction(
            id="TXN-00000001",
            transaction_id="TX-001",
            booking_reference="BKG-001",
            customer_id="CUS-001",
            amount=Decimal("100.00"),
            currency="USD",
            transaction_type=TransactionType.REFUND,
            payment_status=PaymentStatus.SUCCESSFUL,
            payment_method="credit_card",
            reason="First reason for refund",
            processing_time_estimate="3-5 business days",
            created_at="2025-01-15T10:00:00Z",
            updated_at="2025-01-15T10:00:00Z",
        )
        db1.create(transaction1)

        # Create second database
        db2 = self._create_test_db()

        transaction2 = Transaction(
            id="TXN-00000001",
            transaction_id="TX-001",
            booking_reference="BKG-001",
            customer_id="CUS-001",
            amount=Decimal("100.00"),
            currency="USD",
            transaction_type=TransactionType.REFUND,
            payment_status=PaymentStatus.SUCCESSFUL,
            payment_method="credit_card",
            reason="Completely different reason for refund",
            processing_time_estimate="3-5 business days",
            created_at="2025-01-15T10:00:00Z",
            updated_at="2025-01-15T10:00:00Z",
        )
        db2.create(transaction2)

        # Calculate hashes with unstable fields included
        hash1 = calculate_database_hash(db1, exclude_unstable_fields=False)
        hash2 = calculate_database_hash(db2, exclude_unstable_fields=False)

        # Hashes should be different because reason is included in the hash
        assert hash1 != hash2, (
            f"Database hashes should differ when unstable fields are included. "
            f"Hash1: {hash1}, Hash2: {hash2}"
        )
