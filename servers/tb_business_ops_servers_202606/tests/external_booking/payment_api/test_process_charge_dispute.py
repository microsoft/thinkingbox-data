# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for process_charge_dispute tool."""

from decimal import Decimal

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.payment_api.models import (
    PaymentStatus,
    Transaction,
    TransactionType,
)
from tb_business_ops_servers_202606.toolslib.external_booking.payment_api.tools.process_charge_dispute import (
    ProcessChargeDispute,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
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


def test_process_charge_dispute_schema_uses_json_number():
    """Test that the tool schema is compatible with the Responses API."""
    amount_schema = ProcessChargeDispute().input_schema["properties"]["dispute_amount"]

    assert amount_schema["type"] == "number"
    assert "pattern" not in amount_schema


@pytest.mark.parametrize("dispute_amount", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.anyio
async def test_process_charge_dispute_rejects_non_finite_amount(
    db_with_transaction, dispute_amount
):
    """Test that non-finite amounts fail input validation."""
    with pytest.raises(Exception, match="finite number"):
        await ProcessChargeDispute().run_with_validation(
            db_with_transaction,
            {
                "transaction_id": "TXN-00000001",
                "dispute_reason": "test",
                "dispute_amount": dispute_amount,
            },
        )


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
    """Test that dispute creates a transaction record, rounding the amount half-up.

    2.675 is not exactly representable as a float, so this also pins the
    decimal-string conversion that keeps rounding away from the binary value.
    """
    tool = ProcessChargeDispute()

    await tool.run_with_validation(
        db_with_transaction,
        {
            "transaction_id": "TXN-00000001",
            "dispute_reason": "unrecognized charge",
            "dispute_amount": 2.675,
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
    # Decimal equality ignores scale, so also pin the exact 2-decimal-place repr.
    assert dispute.amount == Decimal("2.68")
    assert str(dispute.amount) == "2.68"
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

    await tool.run_with_validation(
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

    await tool.run_with_validation(
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
