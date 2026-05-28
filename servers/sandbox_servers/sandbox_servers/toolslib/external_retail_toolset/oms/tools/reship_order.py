# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for reshipping an order."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Type

from sandbox_servers import InMemoryDatabase, Tool, get_schema_without_refs
from sandbox_servers.toolslib.external_retail_toolset.oms.models import (
    CarrierTracking,
    Order,
    Shipment,
    TrackingStatus,
)
from pydantic import BaseModel, ConfigDict, Field

# Fixed time for testing purposes
FIXED_DATETIME = datetime(2025, 10, 1, 13, 0, 5, tzinfo=timezone.utc)


class ReshipOrderInput(BaseModel):
    """Input for reship_order tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    order_id: str = Field(
        ..., description="Order identifier", examples=["ORD-00012345"]
    )
    corrected_address_line1: str = Field(
        ...,
        description="Corrected shipping address line 1",
        examples=["123 Main St Apt 5B"],
    )
    corrected_address_city: str = Field(
        ..., description="Corrected shipping address city", examples=["Memphis"]
    )
    corrected_address_state: str = Field(
        ..., description="Corrected shipping address state", examples=["TN"]
    )
    corrected_address_zip: str = Field(
        ..., description="Corrected shipping address ZIP code", examples=["38103"]
    )
    customer_fault: bool = Field(
        ...,
        description="Whether address error was customer's fault (affects who pays reship cost)",
        examples=[True],
    )


class ReshipOrderOutput(BaseModel):
    """Output for reship_order tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    order_id: str = Field(
        ..., description="Order identifier", examples=["ORD-00012345"]
    )
    new_shipment_id: str = Field(
        ..., description="New shipment identifier", examples=["SHP-00098765"]
    )
    new_tracking_number: str = Field(
        ..., description="New tracking number", examples=["TRK-987654321012"]
    )
    reship_cost: float = Field(
        ...,
        description="Reship cost ($15 if customer_fault=true, $0 if customer_fault=false)",
        examples=[15.00],
    )
    reship_initiated: bool = Field(
        ..., description="Whether reship was initiated", examples=[True]
    )


class ReshipOrderTool(Tool):
    """Tool implementation for reshipping an order."""

    @property
    def name(self) -> str:
        return "reship_order"

    @property
    def description(self) -> str:
        return (
            "Reship an order that was returned to sender due to address issues. Updates the "
            "shipping address and creates a new shipment for an order that was returned to "
            "sender."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(ReshipOrderInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(ReshipOrderOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return ReshipOrderInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ReshipOrderOutput

    async def run(
        self, db: InMemoryDatabase, request: ReshipOrderInput
    ) -> ReshipOrderOutput:
        """Reship an order with corrected address."""
        try:
            # Get all orders
            all_orders = db.get_all(Order)

            # Find matching order by ID
            matching_order = None
            for order in all_orders:
                if order.id == request.order_id:
                    matching_order = order
                    break

            # If no order found, raise 404 error
            if not matching_order:
                raise Tool.ExecutionError(f"Order not found: {request.order_id}")

            # Get shipment for this order
            all_shipments = db.get_all(Shipment)
            original_shipment = None
            for shipment in all_shipments:
                if shipment.order_id == request.order_id:
                    original_shipment = shipment
                    break

            if not original_shipment:
                raise Tool.ExecutionError(
                    f"No shipment found for order: {request.order_id}"
                )

            # Get carrier tracking to verify status
            all_tracking = db.get_all(CarrierTracking)
            tracking_record = None
            for tracking in all_tracking:
                if tracking.tracking_number == original_shipment.tracking_number:
                    tracking_record = tracking
                    break

            if not tracking_record:
                raise Tool.ExecutionError(
                    f"No tracking found for shipment: {original_shipment.id}"
                )

            # Update order shipping address
            matching_order.shipping_address_line1 = request.corrected_address_line1
            matching_order.shipping_address_city = request.corrected_address_city
            matching_order.shipping_address_state = request.corrected_address_state
            matching_order.shipping_address_zip = request.corrected_address_zip
            db.update(matching_order)

            # Generate new shipment ID
            existing_shipment_ids = [s.id for s in all_shipments]
            shipment_counter = 1
            while True:
                new_shipment_id = f"SHP-2{shipment_counter:07d}"
                if new_shipment_id not in existing_shipment_ids:
                    break
                shipment_counter += 1

            # Generate new tracking number (12-digit sequential)
            existing_tracking_numbers = [t.tracking_number for t in all_tracking]
            tracking_counter = 1
            while True:
                new_tracking_number = f"TRK-2{tracking_counter:011d}"
                if new_tracking_number not in existing_tracking_numbers:
                    break
                tracking_counter += 1

            # Create new shipment record
            now = FIXED_DATETIME
            estimated_delivery = now + timedelta(days=5)

            new_shipment = Shipment(
                id=new_shipment_id,
                order_id=request.order_id,
                carrier=original_shipment.carrier,  # Same carrier
                tracking_number=new_tracking_number,
                ship_date=now,
                estimated_delivery_date=estimated_delivery,
                actual_delivery_date=None,
            )

            # Create new carrier tracking record
            new_tracking = CarrierTracking(
                tracking_number=new_tracking_number,
                shipment_id=new_shipment_id,
                carrier=original_shipment.carrier,
                status=TrackingStatus.PENDING,  # Will transition to in_transit
                current_location=None,
                estimated_delivery=estimated_delivery,
                last_update=now,
            )

            # Save to database
            db.create(new_shipment)
            db.create(new_tracking)

            # Calculate reship cost
            reship_cost = 15.00 if request.customer_fault else 0.00

            # Return reship confirmation
            return ReshipOrderOutput(
                order_id=request.order_id,
                new_shipment_id=new_shipment_id,
                new_tracking_number=new_tracking_number,
                reship_cost=reship_cost,
                reship_initiated=True,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to reship order: {str(e)}"
            raise Tool.ExecutionError(error_message)
