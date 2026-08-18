# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for process_charge tool."""

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
from tb_business_ops_servers_202606.toolslib.external_booking.payment_api.tools.process_charge import (
    ProcessCharge,
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
        booking_value=Decimal("450.00"),
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


@pytest.mark.anyio
async def test_process_charge_success(db_with_booking):
    """Test successfully processing a charge."""
    tool = ProcessCharge()

    result = await tool.run_with_validation(
        db_with_booking,
        {
            "booking_reference": "BKG-00012345",
            "charge_amount": 50.00,
            "reason": "modification_fee",
        },
    )

    assert "transaction_id" in result
    assert result["transaction_id"].startswith("TXN-")
    assert result["payment_status"] == "successful"


@pytest.mark.anyio
async def test_process_charge_creates_transaction(db_with_booking):
    """Test that charge creates a transaction record."""
    tool = ProcessCharge()

    result = await tool.run_with_validation(
        db_with_booking,
        {
            "booking_reference": "BKG-00012345",
            "charge_amount": 75.00,
            "reason": "late_checkout_fee",
        },
    )

    # Verify transaction was created
    transactions = db_with_booking.get_all(Transaction)
    assert len(transactions) == 1

    txn = transactions[0]
    assert txn.transaction_type == TransactionType.CHARGE
    assert txn.amount == Decimal("75.00")
    assert txn.payment_status == PaymentStatus.SUCCESSFUL
    assert txn.reason == "late_checkout_fee"


@pytest.mark.anyio
async def test_process_charge_modification_fee(db_with_booking):
    """Test processing a modification fee."""
    tool = ProcessCharge()

    result = await tool.run_with_validation(
        db_with_booking,
        {
            "booking_reference": "BKG-00012345",
            "charge_amount": 50.00,
            "reason": "modification_fee",
        },
    )

    assert result["payment_status"] == "successful"

    transactions = db_with_booking.get_all(Transaction)
    assert transactions[0].amount == Decimal("50.00")
    assert transactions[0].transaction_type == TransactionType.CHARGE


@pytest.mark.anyio
async def test_process_charge_invalid_booking(db_with_booking):
    """Test charge for non-existent booking fails."""
    tool = ProcessCharge()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_booking,
            {
                "booking_reference": "BKG-99999999",
                "charge_amount": 50.00,
                "reason": "test",
            },
        )

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_process_charge_invalid_amount(db_with_booking):
    """Test charge with invalid amount fails."""
    tool = ProcessCharge()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_booking,
            {"booking_reference": "BKG-00012345", "charge_amount": 0, "reason": "test"},
        )

    assert "invalid" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_process_charge_negative_amount(db_with_booking):
    """Test charge with negative amount fails."""
    tool = ProcessCharge()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_booking,
            {
                "booking_reference": "BKG-00012345",
                "charge_amount": -50.00,
                "reason": "test",
            },
        )

    assert (
        "invalid" in str(exc_info.value).lower()
        or "must be greater than 0" in str(exc_info.value).lower()
    )


@pytest.mark.anyio
async def test_process_charge_multiple_charges(db_with_booking):
    """Test processing multiple charges for same booking."""
    tool = ProcessCharge()

    # First charge
    result1 = await tool.run_with_validation(
        db_with_booking,
        {
            "booking_reference": "BKG-00012345",
            "charge_amount": 50.00,
            "reason": "modification_fee",
        },
    )

    # Second charge
    result2 = await tool.run_with_validation(
        db_with_booking,
        {
            "booking_reference": "BKG-00012345",
            "charge_amount": 25.00,
            "reason": "additional_service",
        },
    )

    assert result1["transaction_id"] != result2["transaction_id"]

    transactions = db_with_booking.get_all(Transaction)
    assert len(transactions) == 2


@pytest.mark.anyio
async def test_process_charge_sequential_ids(db_with_booking):
    """Test that transaction IDs are sequential."""
    tool = ProcessCharge()

    result1 = await tool.run_with_validation(
        db_with_booking,
        {"booking_reference": "BKG-00012345", "charge_amount": 50.00, "reason": "test"},
    )

    result2 = await tool.run_with_validation(
        db_with_booking,
        {"booking_reference": "BKG-00012345", "charge_amount": 30.00, "reason": "test"},
    )

    assert result1["transaction_id"] == "TXN-00000001"
    assert result2["transaction_id"] == "TXN-00000002"


@pytest.mark.anyio
async def test_process_charge_links_to_customer(db_with_booking):
    """Test that charge is linked to correct customer."""
    tool = ProcessCharge()

    await tool.run_with_validation(
        db_with_booking,
        {"booking_reference": "BKG-00012345", "charge_amount": 50.00, "reason": "test"},
    )

    transactions = db_with_booking.get_all(Transaction)
    assert transactions[0].customer_id == "CUS-00012345"
    assert transactions[0].booking_reference == "BKG-00012345"
