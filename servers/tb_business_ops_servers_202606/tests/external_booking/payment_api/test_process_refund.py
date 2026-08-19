# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for process_refund tool."""

from decimal import Decimal

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.booking_api.models import (
    BoardType,
    Booking,
    BookingStatus,
    RoomType,
)
from tb_business_ops_servers_202606.toolslib.external_booking.payment_api.models import (
    PaymentStatus,
    Transaction,
    TransactionType,
)
from tb_business_ops_servers_202606.toolslib.external_booking.payment_api.tools.process_refund import (
    ProcessRefund,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
)


@pytest.fixture
def db_with_booking():
    """Create a database with test booking."""
    db = InMemoryDatabase(domain=STUB_DOMAIN, data_dir=None)

    # Manually register models
    db._stem_to_model_cls["bookings"] = Booking
    db._model_cls_to_stem[Booking] = "bookings"

    db._stem_to_model_cls["transactions"] = Transaction
    db._model_cls_to_stem[Transaction] = "transactions"

    # Add test booking
    booking = Booking(
        id="BKG-00012345",
        booking_reference="BKG-00012345",
        customer_id="CUS-00012345",
        hotel_id="HTL-00012345",
        check_in_date="2025-12-15T15:00:00Z",
        check_out_date="2025-12-18T11:00:00Z",
        booking_value=450.00,
        room_type=RoomType.DELUXE_ROOM,
        board_type=BoardType.WITH_BREAKFAST,
        adults_count=2,
        children_count=1,
        booking_status=BookingStatus.CONFIRMED,
        created_at="2025-11-20T10:00:00Z",
        updated_at="2025-11-20T10:00:00Z",
    )
    db.create(booking)

    return db


def test_process_refund_schema_uses_json_number():
    """Test that the tool schema is compatible with the Responses API."""
    amount_schema = ProcessRefund().input_schema["properties"]["refund_amount"]

    assert amount_schema["type"] == "number"
    assert "pattern" not in amount_schema


@pytest.mark.parametrize("refund_amount", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.anyio
async def test_process_refund_rejects_non_finite_amount(db_with_booking, refund_amount):
    """Test that non-finite amounts fail input validation."""
    with pytest.raises(Exception, match="finite number"):
        await ProcessRefund().run_with_validation(
            db_with_booking,
            {
                "booking_reference": "BKG-00012345",
                "refund_amount": refund_amount,
                "reason": "test",
            },
        )


@pytest.mark.anyio
async def test_process_refund_success(db_with_booking):
    """Test successfully processing a refund."""
    tool = ProcessRefund()

    result = await tool.run_with_validation(
        db_with_booking,
        {
            "booking_reference": "BKG-00012345",
            "refund_amount": 250.00,
            "reason": "cancellation",
        },
    )

    assert "transaction_id" in result
    assert result["transaction_id"].startswith("TXN-")
    assert result["refund_status"] == "successful"
    assert result["processing_time_estimate"] == "3-5 business days"


@pytest.mark.anyio
async def test_process_refund_creates_transaction(db_with_booking):
    """Test that refund creates a transaction record, rounding the amount half-up.

    2.675 is not exactly representable as a float, so this also pins the
    decimal-string conversion that keeps rounding away from the binary value.
    """
    tool = ProcessRefund()

    await tool.run_with_validation(
        db_with_booking,
        {
            "booking_reference": "BKG-00012345",
            "refund_amount": 2.675,
            "reason": "service issue",
        },
    )

    # Verify transaction was created
    transactions = db_with_booking.get_all(Transaction)
    assert len(transactions) == 1

    txn = transactions[0]
    assert txn.transaction_type == TransactionType.REFUND
    # Decimal equality ignores scale, so also pin the exact 2-decimal-place repr.
    assert txn.amount == Decimal("2.68")
    assert str(txn.amount) == "2.68"
    assert txn.payment_status == PaymentStatus.SUCCESSFUL
    assert txn.reason == "service issue"


@pytest.mark.anyio
async def test_process_refund_full_amount(db_with_booking):
    """Test processing a full refund."""
    tool = ProcessRefund()

    result = await tool.run_with_validation(
        db_with_booking,
        {
            "booking_reference": "BKG-00012345",
            "refund_amount": 450.00,
            "reason": "cancellation within policy",
        },
    )

    assert result["refund_status"] == "successful"

    transactions = db_with_booking.get_all(Transaction)
    assert transactions[0].amount == 450.00


@pytest.mark.anyio
async def test_process_refund_partial_amount(db_with_booking):
    """Test processing a partial refund."""
    tool = ProcessRefund()

    await tool.run_with_validation(
        db_with_booking,
        {
            "booking_reference": "BKG-00012345",
            "refund_amount": 100.00,
            "reason": "partial refund",
        },
    )

    transactions = db_with_booking.get_all(Transaction)
    assert transactions[0].amount == 100.00


@pytest.mark.anyio
async def test_process_refund_invalid_booking(db_with_booking):
    """Test refund for non-existent booking fails."""
    tool = ProcessRefund()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_booking,
            {
                "booking_reference": "BKG-99999999",
                "refund_amount": 100.00,
                "reason": "test",
            },
        )

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_process_refund_multiple_refunds(db_with_booking):
    """Test processing multiple refunds for same booking."""
    tool = ProcessRefund()

    # First refund
    result1 = await tool.run_with_validation(
        db_with_booking,
        {
            "booking_reference": "BKG-00012345",
            "refund_amount": 100.00,
            "reason": "first refund",
        },
    )

    # Second refund
    result2 = await tool.run_with_validation(
        db_with_booking,
        {
            "booking_reference": "BKG-00012345",
            "refund_amount": 50.00,
            "reason": "second refund",
        },
    )

    assert result1["transaction_id"] != result2["transaction_id"]

    transactions = db_with_booking.get_all(Transaction)
    assert len(transactions) == 2


@pytest.mark.anyio
async def test_process_refund_sequential_ids(db_with_booking):
    """Test that transaction IDs are sequential."""
    tool = ProcessRefund()

    result1 = await tool.run_with_validation(
        db_with_booking,
        {
            "booking_reference": "BKG-00012345",
            "refund_amount": 100.00,
            "reason": "test",
        },
    )

    result2 = await tool.run_with_validation(
        db_with_booking,
        {"booking_reference": "BKG-00012345", "refund_amount": 50.00, "reason": "test"},
    )

    assert result1["transaction_id"] == "TXN-00000001"
    assert result2["transaction_id"] == "TXN-00000002"


@pytest.mark.anyio
async def test_process_refund_links_to_customer(db_with_booking):
    """Test that refund is linked to correct customer."""
    tool = ProcessRefund()

    await tool.run_with_validation(
        db_with_booking,
        {
            "booking_reference": "BKG-00012345",
            "refund_amount": 200.00,
            "reason": "test",
        },
    )

    transactions = db_with_booking.get_all(Transaction)
    assert transactions[0].customer_id == "CUS-00012345"
    assert transactions[0].booking_reference == "BKG-00012345"
