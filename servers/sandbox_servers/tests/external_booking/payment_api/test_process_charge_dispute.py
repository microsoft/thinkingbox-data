# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for process_charge_dispute tool."""

import pytest
from sandbox_servers.toolslib.external_booking.payment_api.models import (
    PaymentStatus,
    Transaction,
    TransactionType,
)
from sandbox_servers.toolslib.external_booking.payment_api.tools.process_charge_dispute import (
    ProcessChargeDispute,
)
from sandbox_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db_with_transaction():
    """Create a database with test transaction."""
    db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)

    # Manually register models
    db._stem_to_model_cls["transactions"] = Transaction
    db._model_cls_to_stem[Transaction] = "transactions"

    # Add test transaction
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

    return db


@pytest.mark.anyio
async def test_process_charge_dispute_success(db_with_transaction):
    """Test successfully processing a charge dispute."""
    tool = ProcessChargeDispute()

    result = await tool.run_with_validation(
        db_with_transaction,
        {
            "transaction_id": "TXN-00000001",
            "dispute_reason": "unrecognized charge",
            "dispute_amount": 450.00,
        },
    )

    assert "dispute_case_id" in result
    assert result["dispute_case_id"].startswith("DSP-")
    assert result["dispute_status"] == "under_review"


@pytest.mark.anyio
async def test_process_charge_dispute_creates_transaction(db_with_transaction):
    """Test that dispute creates a transaction record."""
    tool = ProcessChargeDispute()

    result = await tool.run_with_validation(
        db_with_transaction,
        {
            "transaction_id": "TXN-00000001",
            "dispute_reason": "unrecognized charge",
            "dispute_amount": 150.00,
        },
    )

    # Verify dispute transaction was created
    transactions = db_with_transaction.get_all(Transaction)
    dispute_txns = [
        t for t in transactions if t.transaction_type == TransactionType.DISPUTE
    ]

    assert len(dispute_txns) == 1
    dispute = dispute_txns[0]
    assert dispute.transaction_type == TransactionType.DISPUTE
    assert dispute.amount == 150.00
    assert dispute.payment_status == PaymentStatus.PENDING
    assert dispute.reason == "unrecognized charge"


@pytest.mark.anyio
async def test_process_charge_dispute_sequential_ids(db_with_transaction):
    """Test that dispute IDs are sequential."""
    tool = ProcessChargeDispute()

    result1 = await tool.run_with_validation(
        db_with_transaction,
        {
            "transaction_id": "TXN-00000001",
            "dispute_reason": "first dispute",
            "dispute_amount": 100.00,
        },
    )

    result2 = await tool.run_with_validation(
        db_with_transaction,
        {
            "transaction_id": "TXN-00000001",
            "dispute_reason": "second dispute",
            "dispute_amount": 50.00,
        },
    )

    assert result1["dispute_case_id"] == "DSP-00000001"
    assert result2["dispute_case_id"] == "DSP-00000002"


@pytest.mark.anyio
async def test_process_charge_dispute_links_to_original(db_with_transaction):
    """Test that dispute is linked to original transaction."""
    tool = ProcessChargeDispute()

    await tool.run_with_validation(
        db_with_transaction,
        {
            "transaction_id": "TXN-00000001",
            "dispute_reason": "test",
            "dispute_amount": 200.00,
        },
    )

    transactions = db_with_transaction.get_all(Transaction)
    dispute_txns = [
        t for t in transactions if t.transaction_type == TransactionType.DISPUTE
    ]

    assert dispute_txns[0].customer_id == "CUS-00012345"
    assert dispute_txns[0].booking_reference == "BKG-00012345"


@pytest.mark.anyio
async def test_process_charge_dispute_invalid_transaction(db_with_transaction):
    """Test dispute for non-existent transaction fails."""
    tool = ProcessChargeDispute()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_transaction,
            {
                "transaction_id": "TXN-99999999",
                "dispute_reason": "test",
                "dispute_amount": 100.00,
            },
        )

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_process_charge_dispute_partial_amount(db_with_transaction):
    """Test processing a partial amount dispute."""
    tool = ProcessChargeDispute()

    result = await tool.run_with_validation(
        db_with_transaction,
        {
            "transaction_id": "TXN-00000001",
            "dispute_reason": "partial dispute",
            "dispute_amount": 100.00,
        },
    )

    transactions = db_with_transaction.get_all(Transaction)
    dispute_txns = [
        t for t in transactions if t.transaction_type == TransactionType.DISPUTE
    ]
    assert dispute_txns[0].amount == 100.00


@pytest.mark.anyio
async def test_process_charge_dispute_full_amount(db_with_transaction):
    """Test processing a full amount dispute."""
    tool = ProcessChargeDispute()

    result = await tool.run_with_validation(
        db_with_transaction,
        {
            "transaction_id": "TXN-00000001",
            "dispute_reason": "full dispute",
            "dispute_amount": 450.00,
        },
    )

    transactions = db_with_transaction.get_all(Transaction)
    dispute_txns = [
        t for t in transactions if t.transaction_type == TransactionType.DISPUTE
    ]
    assert dispute_txns[0].amount == 450.00


@pytest.mark.anyio
async def test_process_charge_dispute_different_reasons(db_with_transaction):
    """Test disputes with different reasons."""
    tool = ProcessChargeDispute()

    reasons = ["unrecognized charge", "duplicate charge", "incorrect amount"]

    for i, reason in enumerate(reasons):
        result = await tool.run_with_validation(
            db_with_transaction,
            {
                "transaction_id": "TXN-00000001",
                "dispute_reason": reason,
                "dispute_amount": 100.00 * (i + 1),
            },
        )

        assert result["dispute_status"] == "under_review"

    transactions = db_with_transaction.get_all(Transaction)
    dispute_txns = [
        t for t in transactions if t.transaction_type == TransactionType.DISPUTE
    ]
    assert len(dispute_txns) == 3
