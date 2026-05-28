# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Modify booking tool for Booking Management System.

Execute modifications to an existing booking.

Updates booking details including dates, room type, board type, guest counts, or special requests.
Calculates price differences, applies modification tracking, and returns updated booking confirmation.
This is the primary write operation for all booking changes.
"""

from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional, Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import BoardType, Booking, BookingStatus, HotelInventory, RoomType

# Fixed time for deterministic behavior (2025-11-25T10:00:00Z)
FIXED_CURRENT_TIME = datetime(2025, 11, 25, 10, 0, 0, tzinfo=timezone.utc)

# Standard decimal precision for monetary amounts (2 decimal places)
TWO_PLACES = Decimal("0.01")


class ModifyBookingInput(BaseModel):
    """Input model for modify_booking tool."""

    model_config = ConfigDict(extra="forbid")

    booking_reference: str = Field(
        ..., description="Booking reference number", examples=["BKG-00012345"]
    )

    # Optional modification fields (flat structure)
    check_in_date: Optional[str] = Field(
        None,
        description="New check-in date (ISO 8601 format)",
        examples=["2025-12-16T15:00:00Z"],
    )
    check_out_date: Optional[str] = Field(
        None,
        description="New check-out date (ISO 8601 format)",
        examples=["2025-12-18T11:00:00Z"],
    )
    room_type: Optional[RoomType] = Field(
        None, description="New room type", examples=["suite"]
    )
    board_type: Optional[BoardType] = Field(
        None, description="New board type (meal plan)", examples=["half_board"]
    )
    adults_count: Optional[int] = Field(
        None, description="New number of adults", examples=[3]
    )
    children_count: Optional[int] = Field(
        None, description="New number of children", examples=[2]
    )
    special_requests: Optional[List[str]] = Field(
        None,
        description="New special requests",
        examples=[["late checkout", "high floor"]],
    )
    booking_status: Optional[BookingStatus] = Field(
        None, description="New booking status", examples=["confirmed"]
    )


class ModifyBookingOutput(BaseModel):
    """Output model for modify_booking tool."""

    model_config = ConfigDict(extra="forbid")

    updated_booking: dict = Field(
        ..., description="Updated booking record with new configuration"
    )
    price_difference: Decimal = Field(
        ...,
        description="Price difference due to modification (positive for additional charge, negative for refund)",
    )


class ModifyBookingTool(Tool):
    """Tool for executing modifications to an existing booking."""

    @property
    def name(self) -> str:
        return "modify_booking"

    @property
    def description(self) -> str:
        return (
            "Updates booking details including dates, room type, board type, guest counts, or special requests. "
            "Calculates price differences, applies modification tracking, and returns updated booking confirmation. "
            "This is the primary write operation for all booking changes."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return ModifyBookingInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ModifyBookingOutput

    async def run(
        self, db: InMemoryDatabase, request: ModifyBookingInput
    ) -> ModifyBookingOutput:
        """Execute booking modifications."""

        # Find the booking
        all_bookings = db.get_all(Booking)
        booking = None
        for b in all_bookings:
            if b.booking_reference == request.booking_reference:
                booking = b
                break

        if booking is None:
            raise Tool.ExecutionError(
                f"Booking not found with booking_reference '{request.booking_reference}'"
            )

        # Minimal hard guard: booking must be confirmed to modify
        if booking.booking_status != BookingStatus.CONFIRMED:
            raise Tool.ExecutionError(
                f"Booking cannot be modified. Current status is '{booking.booking_status.value}', must be 'confirmed'"
            )

        # Track what fields are being modified
        modifications = []
        price_difference = Decimal("0")

        # Store original values (used for comparisons + history + price calculation)
        original_check_in = booking.check_in_date
        original_check_out = booking.check_out_date
        original_room_type = booking.room_type
        original_board_type = booking.board_type
        original_adults_count = booking.adults_count
        original_children_count = booking.children_count
        original_special_requests = booking.special_requests
        original_booking_status = booking.booking_status
        original_value = booking.booking_value  # Already Decimal

        # Get only the fields that were provided (exclude None values)
        # This follows the Zendesk gold standard pattern
        updates = request.model_dump(exclude_none=True, exclude={"booking_reference"})

        # Apply modifications
        if "check_in_date" in updates:
            if original_check_in != request.check_in_date:
                booking.check_in_date = request.check_in_date
                modifications.append(
                    f"check_in_date: {original_check_in} -> {request.check_in_date}"
                )

        if "check_out_date" in updates:
            if original_check_out != request.check_out_date:
                booking.check_out_date = request.check_out_date
                modifications.append(
                    f"check_out_date: {original_check_out} -> {request.check_out_date}"
                )

        if "room_type" in updates:
            if original_room_type != request.room_type:
                booking.room_type = request.room_type
                modifications.append(
                    f"room_type: {original_room_type.value} -> {request.room_type.value}"
                )

        if "board_type" in updates:
            if original_board_type != request.board_type:
                booking.board_type = request.board_type
                modifications.append(
                    f"board_type: {original_board_type.value} -> {request.board_type.value}"
                )

        if "adults_count" in updates:
            if original_adults_count != request.adults_count:
                booking.adults_count = request.adults_count
                modifications.append(
                    f"adults_count: {original_adults_count} -> {request.adults_count}"
                )

        if "children_count" in updates:
            if original_children_count != request.children_count:
                booking.children_count = request.children_count
                modifications.append(
                    f"children_count: {original_children_count} -> {request.children_count}"
                )

        if "special_requests" in updates:
            if original_special_requests != request.special_requests:
                booking.special_requests = request.special_requests
                modifications.append("special_requests updated")

        if "booking_status" in updates:
            if original_booking_status != request.booking_status:
                booking.booking_status = request.booking_status
                modifications.append(
                    f"booking_status: {original_booking_status.value} -> {request.booking_status.value}"
                )

        # Calculate price difference if dates, room_type, or board_type changed
        if (
            "check_in_date" in updates
            or "check_out_date" in updates
            or "room_type" in updates
            or "board_type" in updates
        ):

            new_value = self._calculate_booking_value(
                db,
                booking.hotel_id,
                booking.check_in_date,
                booking.check_out_date,
                booking.room_type,
                booking.board_type,
            )

            if new_value is not None:
                price_difference = new_value - original_value
                booking.booking_value = new_value
            else:
                # If we can't calculate (no inventory data), keep original value
                price_difference = Decimal("0")

        if modifications:
            # Add modification history entry
            timestamp = FIXED_CURRENT_TIME.isoformat().replace("+00:00", "Z")
            history_entry = f"{timestamp}: " + "; ".join(modifications)
            booking.modification_history.append(history_entry)

            # Update timestamp
            booking.updated_at = timestamp

            # Save changes to database
            db.update(booking)

        return ModifyBookingOutput(
            updated_booking=booking.model_dump(),
            price_difference=price_difference.quantize(
                TWO_PLACES, rounding=ROUND_HALF_UP
            ),
        )

    def _calculate_booking_value(
        self,
        db: InMemoryDatabase,
        hotel_id: str,
        check_in_date: str,
        check_out_date: str,
        room_type: RoomType,
        board_type: BoardType,
    ) -> Optional[Decimal]:
        """Calculate booking value based on hotel inventory pricing."""

        try:
            check_in = datetime.fromisoformat(check_in_date.replace("Z", "+00:00"))
            check_out = datetime.fromisoformat(check_out_date.replace("Z", "+00:00"))
        except ValueError:
            return None

        check_in_d = check_in.date()
        check_out_d = check_out.date()

        # Get inventory records
        all_inventory = db.get_all(HotelInventory)
        total_value = Decimal("0")
        nights_counted = 0

        # Sum up price_per_night for each night in the date range
        for inv in all_inventory:
            if (
                inv.hotel_id == hotel_id
                and inv.room_type == room_type
                and inv.board_type == board_type
            ):

                try:
                    inv_date = datetime.fromisoformat(inv.date.replace("Z", "+00:00"))
                    if check_in_d <= inv_date.date() < check_out_d:
                        total_value += Decimal(str(inv.price_per_night))
                        nights_counted += 1
                except ValueError:
                    continue

        if nights_counted > 0:
            return total_value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        return None
