# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for check_payment_status tool."""

import pytest
from ms_toloka_servers.toolslib.external_booking.payment_api.models import (
    PaymentStatus,
    Transaction,
    TransactionType,
)
from ms_toloka_servers.toolslib.external_booking.payment_api.tools.check_payment_status import (
    CheckPaymentStatus,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
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

    # Add test transactions
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

    # Add more recent transaction
    txn2 = Transaction(
        id="TXN-00000002",
        transaction_id="TXN-00000002",
        booking_reference="BKG-00012345",
        customer_id="CUS-00012345",
        amount=100.00,
        currency="USD",
        transaction_type=TransactionType.REFUND,
        payment_status=PaymentStatus.PENDING,
        payment_method=None,
        reason="partial refund",
        processing_time_estimate="3-5 business days",
        created_at="2025-11-20T10:00:00Z",
        updated_at="2025-11-20T10:00:00Z",
    )
    db.create(txn2)

    return db


@pytest.mark.anyio
async def test_check_payment_status_success(db_with_transactions):
    """Test successfully checking payment status."""
    tool = CheckPaymentStatus()

    result = await tool.run_with_validation(
        db_with_transactions, {"booking_reference": "BKG-00012345"}
    )

    assert "payment_status" in result
    assert "transaction_id" in result
    # Should return most recent transaction
    assert result["transaction_id"] == "TXN-00000002"
    assert result["payment_status"] == "pending"


@pytest.mark.anyio
async def test_check_payment_status_returns_most_recent(db_with_transactions):
    """Test that most recent transaction is returned."""
    tool = CheckPaymentStatus()

    result = await tool.run_with_validation(
        db_with_transactions, {"booking_reference": "BKG-00012345"}
    )

    # Most recent should be the refund (TXN-00000002)
    assert result["transaction_id"] == "TXN-00000002"
    assert result["payment_status"] == "pending"


@pytest.mark.anyio
async def test_check_payment_status_with_payment_method(db_with_transactions):
    """Test payment status includes payment method when available."""
    tool = CheckPaymentStatus()

    # Add transaction with payment method as most recent
    txn3 = Transaction(
        id="TXN-00000003",
        transaction_id="TXN-00000003",
        booking_reference="BKG-00012346",
        customer_id="CUS-00067890",
        amount=250.00,
        currency="USD",
        transaction_type=TransactionType.CHARGE,
        payment_status=PaymentStatus.SUCCESSFUL,
        payment_method="Mastercard ending in 5555",
        reason=None,
        processing_time_estimate=None,
        created_at="2025-11-25T10:00:00Z",
        updated_at="2025-11-25T10:00:00Z",
    )
    db_with_transactions.create(txn3)

    result = await tool.run_with_validation(
        db_with_transactions, {"booking_reference": "BKG-00012346"}
    )

    assert result["payment_method"] == "Mastercard ending in 5555"


@pytest.mark.anyio
async def test_check_payment_status_no_payment_method(db_with_transactions):
    """Test payment status without payment method."""
    tool = CheckPaymentStatus()

    result = await tool.run_with_validation(
        db_with_transactions, {"booking_reference": "BKG-00012345"}
    )

    # Most recent is refund, which has no payment method (optional field)
    assert result.get("payment_method") is None


@pytest.mark.anyio
async def test_check_payment_status_not_found(db_with_transactions):
    """Test checking status for non-existent booking."""
    tool = CheckPaymentStatus()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_transactions, {"booking_reference": "BKG-99999999"}
        )

    assert "no transactions found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_check_payment_status_successful():
    """Test status for successful payment."""
    db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)
    db._stem_to_model_cls["transactions"] = Transaction
    db._model_cls_to_stem[Transaction] = "transactions"

    txn = Transaction(
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
    db.create(txn)

    tool = CheckPaymentStatus()
    result = await tool.run_with_validation(db, {"booking_reference": "BKG-00012345"})

    assert result["payment_status"] == "successful"


@pytest.mark.anyio
async def test_check_payment_status_failed():
    """Test status for failed payment."""
    db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)
    db._stem_to_model_cls["transactions"] = Transaction
    db._model_cls_to_stem[Transaction] = "transactions"

    txn = Transaction(
        id="TXN-00000001",
        transaction_id="TXN-00000001",
        booking_reference="BKG-00012345",
        customer_id="CUS-00012345",
        amount=450.00,
        currency="USD",
        transaction_type=TransactionType.CHARGE,
        payment_status=PaymentStatus.FAILED,
        payment_method="Visa ending in 4242",
        reason="insufficient funds",
        processing_time_estimate=None,
        created_at="2025-11-01T10:00:00Z",
        updated_at="2025-11-01T10:00:00Z",
    )
    db.create(txn)

    tool = CheckPaymentStatus()
    result = await tool.run_with_validation(db, {"booking_reference": "BKG-00012345"})

    assert result["payment_status"] == "failed"
