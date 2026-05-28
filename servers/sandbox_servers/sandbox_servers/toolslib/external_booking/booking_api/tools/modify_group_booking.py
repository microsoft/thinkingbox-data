# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Modify group booking tool for Booking Management System.

Execute modifications to a group booking and optionally cascade to individual bookings.

Updates group booking details including dates at the group level. Can optionally cascade date changes
to all associated individual bookings. Returns updated group booking confirmation and list of affected
individual bookings.
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

from ..models import BoardType, Booking, GroupBooking, HotelInventory, RoomType

# Fixed time for deterministic behavior (2025-11-25T10:00:00Z)
FIXED_CURRENT_TIME = datetime(2025, 11, 25, 10, 0, 0, tzinfo=timezone.utc)

# Standard decimal precision for monetary amounts (2 decimal places)
TWO_PLACES = Decimal("0.01")


class ModificationDetails(BaseModel):
    """Modification details for group booking."""

    check_in_date: Optional[str] = Field(
        None,
        description="New check-in date (ISO 8601 format)",
        examples=["2025-12-16T15:00:00Z"],
    )
    check_out_date: Optional[str] = Field(
        None,
        description="New check-out date (ISO 8601 format)",
        examples=["2025-12-20T11:00:00Z"],
    )


class ModifyGroupBookingInput(BaseModel):
    """Input model for modify_group_booking tool."""

    model_config = ConfigDict(extra="forbid")

    group_booking_id: str = Field(
        ..., description="Group booking identifier", examples=["GRP-00012345"]
    )
    modification_details: ModificationDetails = Field(
        ...,
        description="Details of modifications to apply",
        examples=[
            {
                "check_in_date": "2025-12-16T15:00:00Z",
                "check_out_date": "2025-12-20T11:00:00Z",
            }
        ],
    )
    cascade_to_individual_bookings: bool = Field(
        ...,
        description="Whether to cascade changes to all individual bookings in the group",
        examples=[True],
    )


class ModifyGroupBookingOutput(BaseModel):
    """Output model for modify_group_booking tool."""

    model_config = ConfigDict(extra="forbid")

    updated_group_booking: dict = Field(
        ..., description="Updated group booking record with new configuration"
    )
    modified_booking_references: List[str] = Field(
        ...,
        description="List of individual booking references that were modified (if cascade=true)",
    )
    total_price_difference: Decimal = Field(
        ...,
        description="Total price difference across all modified bookings (positive for additional charge, negative for refund)",
    )


class ModifyGroupBookingTool(Tool):
    """Tool for executing modifications to a group booking with optional cascade to individual bookings."""

    @property
    def name(self) -> str:
        return "modify_group_booking"

    @property
    def description(self) -> str:
        return (
            "Execute modifications to a group booking and optionally cascade to individual bookings. "
            "Updates group booking details including dates at the group level. "
            "Can optionally cascade date changes to all associated individual bookings. "
            "Returns updated group booking confirmation and list of affected individual bookings."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return ModifyGroupBookingInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ModifyGroupBookingOutput

    async def run(
        self, db: InMemoryDatabase, request: ModifyGroupBookingInput
    ) -> ModifyGroupBookingOutput:
        """Execute group booking modifications."""

        # Find the group booking
        all_group_bookings = db.get_all(GroupBooking)
        group_booking = None
        for gb in all_group_bookings:
            if gb.group_booking_id == request.group_booking_id:
                group_booking = gb
                break

        if group_booking is None:
            raise Tool.ExecutionError(
                f"Group booking not found with group_booking_id '{request.group_booking_id}'"
            )

        # Track modifications
        modified_booking_references = []
        total_price_difference = Decimal("0")
        timestamp = FIXED_CURRENT_TIME.isoformat().replace("+00:00", "Z")

        group_booking_changed = False
        any_booking_changed = False

        # Update group booking dates only when values actually change
        if request.modification_details.check_in_date:
            if (
                group_booking.check_in_date
                != request.modification_details.check_in_date
            ):
                group_booking.check_in_date = request.modification_details.check_in_date
                group_booking_changed = True

        if request.modification_details.check_out_date:
            if (
                group_booking.check_out_date
                != request.modification_details.check_out_date
            ):
                group_booking.check_out_date = (
                    request.modification_details.check_out_date
                )
                group_booking_changed = True

        # Cascade to individual bookings if requested
        if request.cascade_to_individual_bookings:
            all_bookings = db.get_all(Booking)

            for booking_ref in group_booking.booking_references:
                # Find the booking
                booking = None
                for b in all_bookings:
                    if b.booking_reference == booking_ref:
                        booking = b
                        break

                if booking is None:
                    # Skip if booking not found (could have been deleted)
                    continue

                # Calculate original value
                original_value = booking.booking_value  # Already Decimal
                original_check_in = booking.check_in_date
                original_check_out = booking.check_out_date

                modifications: List[str] = []

                # Update dates only when values actually change
                if request.modification_details.check_in_date:
                    if original_check_in != request.modification_details.check_in_date:
                        booking.check_in_date = (
                            request.modification_details.check_in_date
                        )
                        modifications.append(
                            f"check_in_date updated via group booking {request.group_booking_id}"
                        )

                if request.modification_details.check_out_date:
                    if (
                        original_check_out
                        != request.modification_details.check_out_date
                    ):
                        booking.check_out_date = (
                            request.modification_details.check_out_date
                        )
                        modifications.append(
                            f"check_out_date updated via group booking {request.group_booking_id}"
                        )

                # Only calculate value / write history when something actually changed
                if modifications:
                    any_booking_changed = True

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
                        total_price_difference += price_difference
                        # Avoid rewriting booking_value when there is no numeric change
                        if price_difference != 0:
                            booking.booking_value = new_value

                    history_entry = f"{timestamp}: " + "; ".join(modifications)
                    booking.modification_history.append(history_entry)
                    booking.updated_at = timestamp

                    # Save booking changes
                    db.update(booking)
                    modified_booking_references.append(booking_ref)

        # Save group booking changes only when something actually changed
        if group_booking_changed or any_booking_changed:
            group_booking.updated_at = timestamp
            db.update(group_booking)

        return ModifyGroupBookingOutput(
            updated_group_booking=group_booking.model_dump(),
            modified_booking_references=modified_booking_references,
            total_price_difference=total_price_difference.quantize(
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
