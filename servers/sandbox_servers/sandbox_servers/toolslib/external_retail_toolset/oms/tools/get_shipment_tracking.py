# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for getting shipment tracking information."""

from typing import Any, Dict, Optional, Type

from sandbox_servers import InMemoryDatabase, Tool, get_schema_without_refs
from sandbox_servers.toolslib.external_retail_toolset.oms.models import (
    CarrierTracking,
    Shipment,
    TrackingStatus,
)
from pydantic import BaseModel, ConfigDict, Field


class GetShipmentTrackingInput(BaseModel):
    """Input for get_shipment_tracking tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    order_id: str = Field(
        ...,
        description="Order identifier to look up associated shipment",
        examples=["ORD-00012345"],
    )


class GetShipmentTrackingOutput(BaseModel):
    """Output for get_shipment_tracking tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    shipment_id: str = Field(
        ..., description="Unique shipment identifier", examples=["SHP-00012345"]
    )
    order_id: str = Field(
        ..., description="Order identifier", examples=["ORD-00012345"]
    )
    carrier: str = Field(..., description="Shipping carrier name", examples=["FedEx"])
    tracking_number: str = Field(
        ..., description="Carrier tracking number", examples=["TRK-123456789012"]
    )
    ship_date: str = Field(
        ...,
        description="Date when shipment was dispatched",
        examples=["2024-10-16T08:15:00Z"],
    )
    estimated_delivery_date: str = Field(
        ..., description="Estimated delivery date", examples=["2024-10-22T17:00:00Z"]
    )
    actual_delivery_date: Optional[str] = Field(
        None,
        description="Actual delivery date (used to calculate days since delivery for return window)",
        examples=["2024-10-21T14:32:00Z"],
    )
    tracking_status: TrackingStatus = Field(
        ...,
        description=(
            "Current tracking status: pending, in_transit, delayed, delivered, "
            "exception, returned_to_sender"
        ),
        examples=["in_transit"],
    )
    current_location: Optional[str] = Field(
        None, description="Current package location", examples=["Memphis, TN"]
    )


class GetShipmentTrackingTool(Tool):
    """Tool implementation for retrieving shipment and tracking information."""

    @property
    def name(self) -> str:
        return "get_shipment_tracking"

    @property
    def description(self) -> str:
        return (
            "Retrieve shipment and tracking information for an order. Fetches shipment "
            "details including carrier, tracking number, current tracking status, location, "
            "and estimated/actual delivery dates. Used for WISMO inquiries, return window "
            "calculation, and tracking issues."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetShipmentTrackingInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetShipmentTrackingOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetShipmentTrackingInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetShipmentTrackingOutput

    async def run(
        self, db: InMemoryDatabase, request: GetShipmentTrackingInput
    ) -> GetShipmentTrackingOutput:
        """Retrieve shipment and tracking information by order_id."""
        try:
            # Get all shipments
            all_shipments = db.get_all(Shipment)

            # Find matching shipment by order_id
            matching_shipment = None
            for shipment in all_shipments:
                if shipment.order_id == request.order_id:
                    matching_shipment = shipment
                    break

            # If no shipment found, raise 404 error
            if not matching_shipment:
                raise Tool.ExecutionError(
                    f"No shipment found for order: {request.order_id} (may not be shipped yet)"
                )

            # Get carrier tracking information
            all_tracking = db.get_all(CarrierTracking)

            # Find matching tracking by tracking_number
            matching_tracking = None
            for tracking in all_tracking:
                if tracking.tracking_number == matching_shipment.tracking_number:
                    matching_tracking = tracking
                    break

            # If no tracking found, use default pending status
            if not matching_tracking:
                tracking_status = TrackingStatus.PENDING
                current_location = None
            else:
                tracking_status = matching_tracking.status
                current_location = matching_tracking.current_location

            # Return combined shipment and tracking data
            return GetShipmentTrackingOutput(
                shipment_id=matching_shipment.id,
                order_id=matching_shipment.order_id,
                carrier=matching_shipment.carrier,
                tracking_number=matching_shipment.tracking_number,
                ship_date=matching_shipment.ship_date.isoformat(),
                estimated_delivery_date=matching_shipment.estimated_delivery_date.isoformat(),
                actual_delivery_date=(
                    matching_shipment.actual_delivery_date.isoformat()
                    if matching_shipment.actual_delivery_date
                    else None
                ),
                tracking_status=tracking_status,
                current_location=current_location,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to retrieve shipment tracking: {str(e)}"
            raise Tool.ExecutionError(error_message)
