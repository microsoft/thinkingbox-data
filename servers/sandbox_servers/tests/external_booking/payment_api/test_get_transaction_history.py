# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_transaction_history tool."""

import pytest
from sandbox_servers.toolslib.external_booking.payment_api.models import (
    PaymentStatus,
    Transaction,
    TransactionType,
)
from sandbox_servers.toolslib.external_booking.payment_api.tools.get_transaction_history import (
    GetTransactionHistory,
)
from sandbox_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db_with_transactions():
    """Create a database with test transactions."""
    db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)

    # Manually register models
    db._stem_to_model_cls["transactions"] = Transaction
    db._model_cls_to_stem[Transaction] = "transactions"

    # Add transactions for customer CUS-00012345
    txn1 = Transaction(
        id="TXN-00000001",
        transaction_id="TXN-00000001",
        booking_reference="BKG-00012345",
        customer_id="CUS-00012345",
        amount=450.00,
        currency="USD",
        transaction_type=TransactionType.CHARGE,
        payment_status=PaymentStatus.SUCCESSFUL,
        payment_method="Visa ending in 4242",
        reason=None,
        processing_time_estimate=None,
        created_at="2025-11-01T10:00:00Z",
        updated_at="2025-11-01T10:00:00Z",
    )
    db.create(txn1)

    txn2 = Transaction(
        id="TXN-00000002",
        transaction_id="TXN-00000002",
        booking_reference="BKG-00012346",
        customer_id="CUS-00012345",
        amount=300.00,
        currency="USD",
        transaction_type=TransactionType.CHARGE,
        payment_status=PaymentStatus.SUCCESSFUL,
        payment_method="Visa ending in 4242",
        reason=None,
        processing_time_estimate=None,
        created_at="2025-09-15T10:00:00Z",
        updated_at="2025-09-15T10:00:00Z",
    )
    db.create(txn2)

    # Add transaction for different customer
    txn3 = Transaction(
        id="TXN-00000003",
        transaction_id="TXN-00000003",
        booking_reference="BKG-00067890",
        customer_id="CUS-00067890",
        amount=250.00,
        currency="USD",
        transaction_type=TransactionType.CHARGE,
        payment_status=PaymentStatus.SUCCESSFUL,
        payment_method="Amex ending in 1009",
        reason=None,
        processing_time_estimate=None,
        created_at="2025-11-20T10:00:00Z",
        updated_at="2025-11-20T10:00:00Z",
    )
    db.create(txn3)

    return db


@pytest.mark.anyio
async def test_get_transaction_history_by_customer(db_with_transactions):
    """Test retrieving transaction history by customer_id."""
    tool = GetTransactionHistory()

    result = await tool.run_with_validation(
        db_with_transactions, {"customer_id": "CUS-00012345"}
    )

    assert "transactions" in result
    assert len(result["transactions"]) == 2
    # Should be sorted by created_at DESC
    assert result["transactions"][0]["transaction_id"] == "TXN-00000001"
    assert result["transactions"][1]["transaction_id"] == "TXN-00000002"


@pytest.mark.anyio
async def test_get_transaction_history_by_booking(db_with_transactions):
    """Test retrieving transaction history by booking_reference."""
    tool = GetTransactionHistory()

    result = await tool.run_with_validation(
        db_with_transactions, {"booking_reference": "BKG-00012345"}
    )

    assert "transactions" in result
    assert len(result["transactions"]) == 1
    assert result["transactions"][0]["booking_reference"] == "BKG-00012345"


@pytest.mark.anyio
async def test_get_transaction_history_empty():
    """Test retrieving history for customer with no transactions."""
    db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)
    db._stem_to_model_cls["transactions"] = Transaction
    db._model_cls_to_stem[Transaction] = "transactions"

    tool = GetTransactionHistory()

    result = await tool.run_with_validation(db, {"customer_id": "CUS-99999999"})

    assert result["transactions"] == []


@pytest.mark.anyio
async def test_get_transaction_history_includes_all_types(db_with_transactions):
    """Test that history includes all transaction types."""
    # Add refund and dispute
    refund = Transaction(
        id="TXN-00000004",
        transaction_id="TXN-00000004",
        booking_reference="BKG-00012345",
        customer_id="CUS-00012345",
        amount=100.00,
        currency="USD",
        transaction_type=TransactionType.REFUND,
        payment_status=PaymentStatus.SUCCESSFUL,
        payment_method=None,
        reason="partial refund",
        processing_time_estimate="3-5 business days",
        created_at="2025-11-15T10:00:00Z",
        updated_at="2025-11-15T10:00:00Z",
    )
    db_with_transactions.create(refund)

    tool = GetTransactionHistory()

    result = await tool.run_with_validation(
        db_with_transactions, {"customer_id": "CUS-00012345"}
    )

    assert len(result["transactions"]) == 3
    types = [t["transaction_type"] for t in result["transactions"]]
    assert "charge" in types
    assert "refund" in types


@pytest.mark.anyio
async def test_get_transaction_history_missing_parameters(db_with_transactions):
    """Test that missing both parameters raises error."""
    tool = GetTransactionHistory()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(db_with_transactions, {})

    assert "must be provided" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_get_transaction_history_includes_all_fields(db_with_transactions):
    """Test that all transaction fields are included."""
    tool = GetTransactionHistory()

    result = await tool.run_with_validation(
        db_with_transactions, {"booking_reference": "BKG-00012345"}
    )

    txn = result["transactions"][0]
    assert "id" in txn
    assert "transaction_id" in txn
    assert "booking_reference" in txn
    assert "customer_id" in txn
    assert "amount" in txn
    assert "currency" in txn
    assert "transaction_type" in txn
    assert "payment_status" in txn
    assert "created_at" in txn
    assert "updated_at" in txn


@pytest.mark.anyio
async def test_get_transaction_history_sorted_desc(db_with_transactions):
    """Test that transactions are sorted by created_at DESC."""
    tool = GetTransactionHistory()

    result = await tool.run_with_validation(
        db_with_transactions, {"customer_id": "CUS-00012345"}
    )

    # Most recent first
    assert (
        result["transactions"][0]["created_at"]
        > result["transactions"][1]["created_at"]
    )
