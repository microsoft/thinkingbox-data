# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Hardware Procurement - Create Order Tool."""

from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
    DeviceType,
    Employee,
    ProcurementOrder,
    ProcurementOrderStatus,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    get_schema_without_refs,
)
from pydantic import BaseModel, ConfigDict, Field

FIXED_CURRENT_TIME = datetime(2025, 12, 18, 10, 0, 0, tzinfo=timezone.utc)


class HardwareProcurementCreateOrderInput(BaseModel):
    """Input model for hardware procurement create order."""

    model_config = ConfigDict(extra="forbid")

    device_type: DeviceType = Field(
        ..., description="Device type to order", examples=["laptop_premium"]
    )
    device_model: str = Field(
        ..., description="Device model", examples=["MacBook Pro 14"]
    )
    quantity: int = Field(..., description="Quantity to order", examples=[1])
    expected_delivery_date: str = Field(
        ...,
        description="Expected delivery date based on lead times in YYYY-MM-DD format",
        examples=["2025-12-28"],
    )
    ship_to_location: str = Field(
        ...,
        description="Shipping address",
        examples=["123 Main St, San Francisco, CA 94102"],
    )
    requester_email: str = Field(
        ..., description="Requester employee email", examples=["john.smith@vdb.com"]
    )
    ticket_id: Optional[str] = Field(
        None, description="Associated ticket ID", examples=["TCK-00012345"]
    )


class HardwareProcurementCreateOrderOutput(BaseModel):
    """Output model for hardware procurement create order."""

    model_config = ConfigDict(extra="forbid")

    order_id: str = Field(
        ..., description="Procurement order ID (format: HW-ORDER-#######)"
    )
    status: str = Field(..., description="Initial order status (pending)")


class HardwareProcurementCreateOrderTool(Tool):
    """Tool for creating hardware procurement orders."""

    @property
    def name(self) -> str:
        return "hardware_procurement_api_create_order"

    @property
    def description(self) -> str:
        return "Create a hardware procurement order. Places a hardware order with the vendor when inventory is not available. Returns an order ID for tracking and estimated delivery date."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(HardwareProcurementCreateOrderInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(HardwareProcurementCreateOrderOutput)

    @property
    def request_model(self) -> type[BaseModel]:
        return HardwareProcurementCreateOrderInput

    @property
    def output_model(self) -> type[BaseModel]:
        return HardwareProcurementCreateOrderOutput

    async def run(
        self, db: InMemoryDatabase, request: HardwareProcurementCreateOrderInput
    ) -> HardwareProcurementCreateOrderOutput:
        """Create a hardware procurement order."""
        # Validate employee exists
        all_employees = db.get_all(Employee)
        employees = [e for e in all_employees if e.email == request.requester_email]

        if not employees:
            raise Tool.ExecutionError(f"Requester not found: {request.requester_email}")

        employee = employees[0]

        # Generate new order ID
        all_existing = db.get_all(ProcurementOrder)
        next_id = len(all_existing) + 1
        order_id = f"HW-ORDER-{next_id:07d}"

        # Parse expected delivery date as date-only (YYYY-MM-DD)
        try:
            expected_delivery = date.fromisoformat(request.expected_delivery_date[:10])
        except ValueError:
            raise Tool.ExecutionError(
                f"Invalid expected_delivery_date format: {request.expected_delivery_date}. Expected YYYY-MM-DD format."
            )

        # Create new procurement order (created_at is now optional)
        new_order = ProcurementOrder(
            id=order_id,
            device_type=request.device_type.value,
            device_model=request.device_model,
            quantity=request.quantity,
            ship_to_location=request.ship_to_location,
            requester_id=employee.id,
            ticket_id=request.ticket_id,
            status=ProcurementOrderStatus.PENDING,
            created_at=None,
            expected_delivery_date=expected_delivery,
        )

        db.create(new_order)

        return HardwareProcurementCreateOrderOutput(order_id=order_id, status="pending")
