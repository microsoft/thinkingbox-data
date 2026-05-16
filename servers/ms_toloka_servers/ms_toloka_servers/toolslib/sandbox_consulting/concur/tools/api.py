# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for SAP Concur Travel & Expense API (master tool)."""

from enum import Enum
from typing import Any, Dict, Optional, Type

from ms_toloka_servers.toolslib.sandbox_consulting.concur.models import (
    ExpenseReport,
    FlightClass,
    OverrideReason,
    TravelRequest,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field


class ConcurAction(str, Enum):
    """Concur API action enumeration."""

    GET_EXPENSE_REPORT = "get_expense_report"
    OVERRIDE_EXPENSE_REJECTION = "override_expense_rejection"
    GET_TRAVEL_BOOKING = "get_travel_booking"


class ConcurApiInput(BaseModel):
    """Input for concur_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    action: ConcurAction = Field(
        ...,
        description="Action to perform",
        examples=["get_expense_report"],
    )
    expense_report_id: Optional[str] = Field(
        None,
        description="Expense report ID (required for get_expense_report, override_expense_rejection)",
        examples=["EXP-0012345"],
    )
    override_reason: Optional[OverrideReason] = Field(
        None,
        description="Reason for override (required for override_expense_rejection)",
        examples=["justified_exception"],
    )
    approver_email: Optional[str] = Field(
        None,
        description="Approver email address (required for override_expense_rejection)",
        examples=["manager@msg.com"],
    )
    booking_id: Optional[str] = Field(
        None,
        description="Travel booking ID (required for get_travel_booking)",
        examples=["TRV-1000001"],
    )


class ExpenseReportOutput(BaseModel):
    """Expense report output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    id: str = Field(..., description="Expense report ID")
    employee_email: str = Field(..., description="Employee email address")
    amount: int = Field(..., description="Expense amount in dollars")
    category: str = Field(..., description="Expense category")
    trip_location_city: Optional[str] = Field(None, description="Trip location city")
    trip_location_state: Optional[str] = Field(None, description="Trip location state")
    expense_date: str = Field(..., description="Expense date")
    receipt_status: str = Field(..., description="Receipt status")
    rejection_reason: Optional[str] = Field(
        None, description="Rejection reason if rejected"
    )
    override_approved: bool = Field(..., description="Whether override was approved")
    override_approved_by: Optional[str] = Field(
        None, description="Email of person who approved override"
    )
    override_reason: Optional[str] = Field(
        None, description="Reason for override approval"
    )


class TravelBookingOutput(BaseModel):
    """Travel booking output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    id: str = Field(..., description="Travel booking ID")
    employee_email: str = Field(..., description="Employee email address")
    destination: str = Field(..., description="Travel destination")
    departure_date: str = Field(..., description="Departure date")
    return_date: str = Field(..., description="Return date")
    flight_class: str = Field(..., description="Flight class")
    hotel_rate_per_night: Optional[int] = Field(
        None, description="Hotel rate per night in dollars"
    )


class ConcurApiOutput(BaseModel):
    """Output for concur_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    expense_report: Optional[ExpenseReportOutput] = Field(
        None,
        description="Expense report record from expense_reports table (for action=get_expense_report)",
    )
    success: Optional[bool] = Field(
        None,
        description="Indicates if override was successful (for action=override_expense_rejection)",
    )
    travel_booking: Optional[TravelBookingOutput] = Field(
        None,
        description="Travel booking record from travel_requests table (for action=get_travel_booking)",
    )


class ConcurApiTool(Tool):
    """Master tool implementation for SAP Concur Travel & Expense API."""

    @property
    def name(self) -> str:
        return "api"

    @property
    def description(self) -> str:
        return (
            "Manage travel and expense reporting. Retrieves expense reports and overrides expense "
            "rejections. Use action parameter to specify the operation:\n\n"
            "- action='get_expense_report': Fetches expense report details including employee_email, "
            "amount, category, trip_location_city, trip_location_state, expense_date, receipt_status, "
            "rejection_reason, override_approved, override_approved_by, and override_reason. REQUIRES: "
            "expense_report_id. Returns expense_report object from expense_reports table.\n\n"
            "- action='override_expense_rejection': Approves a previously rejected expense report. "
            "REQUIRES: expense_report_id, override_reason (enum: justified_exception, system_error, "
            "receipt_exception), approver_email. Returns success boolean.\n\n"
            "- action='get_travel_booking': Fetches travel booking details including employee_email, "
            "destination, departure_date, return_date, flight_class, and hotel_rate_per_night. REQUIRES: "
            "booking_id. Returns travel_booking object from travel_requests table.\n\n"
            "Use get_expense_report to retrieve expense details including rejection_reason for validation "
            "before approving overrides. Use override_expense_rejection to approve flagged reports with "
            "proper override_reason enum value."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(ConcurApiInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(ConcurApiOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return ConcurApiInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ConcurApiOutput

    async def run(
        self, db: InMemoryDatabase, request: ConcurApiInput
    ) -> ConcurApiOutput:
        """Execute Concur API action."""
        try:
            if request.action == ConcurAction.GET_EXPENSE_REPORT:
                return await self._get_expense_report(db, request)
            elif request.action == ConcurAction.OVERRIDE_EXPENSE_REJECTION:
                return await self._override_expense_rejection(db, request)
            elif request.action == ConcurAction.GET_TRAVEL_BOOKING:
                return await self._get_travel_booking(db, request)
            else:
                raise Tool.ExecutionError(f"Invalid action: {request.action}")

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to execute Concur API action: {str(e)}"
            raise Tool.ExecutionError(error_message)

    async def _get_expense_report(
        self, db: InMemoryDatabase, request: ConcurApiInput
    ) -> ConcurApiOutput:
        """Get expense report by ID."""
        if not request.expense_report_id:
            raise Tool.ExecutionError("Missing required parameter: expense_report_id")

        # Get expense report by ID
        expense_report = db.get_by_id(ExpenseReport, request.expense_report_id)

        # If no report found, raise 404 error
        if not expense_report:
            raise Tool.ExecutionError(
                f"Expense report not found: {request.expense_report_id}"
            )

        # Return expense report data
        expense_report_output = ExpenseReportOutput(
            id=expense_report.id,
            employee_email=expense_report.employee_email,
            amount=expense_report.amount,
            category=expense_report.category.value,
            trip_location_city=expense_report.trip_location_city,
            trip_location_state=expense_report.trip_location_state,
            expense_date=expense_report.expense_date.isoformat(),
            receipt_status=expense_report.receipt_status.value,
            rejection_reason=expense_report.rejection_reason,
            override_approved=expense_report.override_approved,
            override_approved_by=expense_report.override_approved_by,
            override_reason=(
                expense_report.override_reason.value
                if expense_report.override_reason
                else None
            ),
        )

        return ConcurApiOutput(expense_report=expense_report_output)

    async def _override_expense_rejection(
        self, db: InMemoryDatabase, request: ConcurApiInput
    ) -> ConcurApiOutput:
        """Override expense rejection."""
        if not request.expense_report_id:
            raise Tool.ExecutionError("Missing required parameter: expense_report_id")
        if not request.override_reason:
            raise Tool.ExecutionError("Missing required parameter: override_reason")
        if not request.approver_email:
            raise Tool.ExecutionError("Missing required parameter: approver_email")

        # Get expense report by ID
        expense_report = db.get_by_id(ExpenseReport, request.expense_report_id)

        # If no report found, raise 404 error
        if not expense_report:
            raise Tool.ExecutionError(
                f"Expense report not found: {request.expense_report_id}"
            )

        # Update expense report with override approval
        # DO NOT clear rejection_reason field - keep it as is
        expense_report.override_approved = True
        expense_report.override_approved_by = request.approver_email
        expense_report.override_reason = request.override_reason

        # Update in database
        db.update(expense_report)

        return ConcurApiOutput(success=True)

    async def _get_travel_booking(
        self, db: InMemoryDatabase, request: ConcurApiInput
    ) -> ConcurApiOutput:
        """Get travel booking by ID."""
        if not request.booking_id:
            raise Tool.ExecutionError("Missing required parameter: booking_id")

        # Get travel booking by ID
        travel_booking = db.get_by_id(TravelRequest, request.booking_id)

        # If no booking found, raise 404 error
        if not travel_booking:
            raise Tool.ExecutionError(f"Travel booking not found: {request.booking_id}")

        # Return travel booking data
        travel_booking_output = TravelBookingOutput(
            id=travel_booking.id,
            employee_email=travel_booking.employee_email,
            destination=travel_booking.destination,
            departure_date=travel_booking.departure_date.isoformat(),
            return_date=travel_booking.return_date.isoformat(),
            flight_class=travel_booking.flight_class.value,
            hotel_rate_per_night=travel_booking.hotel_rate_per_night,
        )

        return ConcurApiOutput(travel_booking=travel_booking_output)
