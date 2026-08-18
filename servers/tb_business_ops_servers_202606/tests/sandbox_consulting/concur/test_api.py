# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for concur_api master tool."""

from datetime import datetime

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.concur.models import (
    ExpenseCategory,
    ExpenseReport,
    FlightClass,
    OverrideReason,
    ReceiptStatus,
    TravelRequest,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.concur.tools.api import ConcurApiTool
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)


class TestConcurApi:
    @pytest.fixture
    def test_db(self):
        """Create a test database with expense reports and travel requests."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "expense_reports": ExpenseReport,
            "travel_requests": TravelRequest,
        }
        db._model_cls_to_stem = {
            ExpenseReport: "expense_reports",
            TravelRequest: "travel_requests",
        }

        # Create test expense reports
        report1 = ExpenseReport(
            id="EXP-1000001",
            employee_email="john.smith@msg.com",
            amount=125,
            category=ExpenseCategory.MEALS,
            trip_location_city="New York",
            trip_location_state="NY",
            expense_date=datetime(2024, 10, 15),
            receipt_status=ReceiptStatus.ATTACHED,
            rejection_reason=None,
            override_approved=False,
            override_approved_by=None,
            override_reason=None,
        )

        report2 = ExpenseReport(
            id="EXP-1000002",
            employee_email="jane.doe@msg.com",
            amount=250,
            category=ExpenseCategory.HOTEL,
            trip_location_city="San Francisco",
            trip_location_state="CA",
            expense_date=datetime(2024, 10, 20),
            receipt_status=ReceiptStatus.MISSING,
            rejection_reason="Receipt missing - required for hotel expenses over $150",
            override_approved=False,
            override_approved_by=None,
            override_reason=None,
        )

        report3 = ExpenseReport(
            id="EXP-1000003",
            employee_email="bob.taylor@msg.com",
            amount=180,
            category=ExpenseCategory.CLIENT_ENTERTAINMENT,
            trip_location_city="Boston",
            trip_location_state="MA",
            expense_date=datetime(2024, 10, 25),
            receipt_status=ReceiptStatus.ITEMIZED,
            rejection_reason="Itemized receipt required - missing attendee list",
            override_approved=True,
            override_approved_by="sarah.johnson@msg.com",
            override_reason=OverrideReason.JUSTIFIED_EXCEPTION,
        )

        # Create test travel requests
        travel1 = TravelRequest(
            id="TRV-1000001",
            employee_email="john.smith@msg.com",
            destination="New York, NY",
            departure_date=datetime(2024, 11, 25, 8, 0, 0),
            return_date=datetime(2024, 11, 27, 18, 0, 0),
            flight_class=FlightClass.ECONOMY,
            hotel_rate_per_night=250,
        )

        travel2 = TravelRequest(
            id="TRV-1000002",
            employee_email="jane.doe@msg.com",
            destination="San Francisco, CA",
            departure_date=datetime(2024, 12, 1, 9, 30, 0),
            return_date=datetime(2024, 12, 5, 20, 0, 0),
            flight_class=FlightClass.BUSINESS,
            hotel_rate_per_night=320,
        )

        travel3 = TravelRequest(
            id="TRV-1000003",
            employee_email="alice.wilson@msg.com",
            destination="Chicago, IL",
            departure_date=datetime(2024, 11, 28, 7, 15, 0),
            return_date=datetime(2024, 11, 29, 22, 30, 0),
            flight_class=FlightClass.ECONOMY,
            hotel_rate_per_night=180,
        )

        travel4 = TravelRequest(
            id="TRV-1000004",
            employee_email="bob.taylor@msg.com",
            destination="Boston, MA",
            departure_date=datetime(2024, 12, 10, 10, 0, 0),
            return_date=datetime(2024, 12, 14, 17, 45, 0),
            flight_class=FlightClass.ECONOMY,
            hotel_rate_per_night=None,
        )

        travel5 = TravelRequest(
            id="TRV-1000005",
            employee_email="emma.garcia@msg.com",
            destination="Seattle, WA",
            departure_date=datetime(2024, 12, 3, 6, 45, 0),
            return_date=datetime(2024, 12, 8, 19, 15, 0),
            flight_class=FlightClass.FIRST,
            hotel_rate_per_night=450,
        )

        db._store = {
            ExpenseReport: [report1, report2, report3],
            TravelRequest: [travel1, travel2, travel3, travel4, travel5],
        }
        return db

    @pytest.fixture
    def concur_tool(self):
        """Create an instance of the Concur API tool."""
        return ConcurApiTool()

    # Tests for get_expense_report action
    @pytest.mark.anyio
    async def test_get_expense_report_success(self, concur_tool, test_db):
        """Test successful expense report retrieval."""
        # Arrange
        request_data = {
            "action": "get_expense_report",
            "expense_report_id": "EXP-1000001",
        }

        # Act
        result = await concur_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("expense_report") is not None
        report = result["expense_report"]
        assert report["id"] == "EXP-1000001"
        assert report["employee_email"] == "john.smith@msg.com"
        assert report["amount"] == 125
        assert report["category"] == "meals"
        assert report["trip_location_city"] == "New York"
        assert report["trip_location_state"] == "NY"
        assert report["expense_date"] == "2024-10-15T00:00:00"
        assert report["receipt_status"] == "attached"
        assert report.get("rejection_reason") is None
        assert report["override_approved"] is False
        assert report.get("override_approved_by") is None
        assert report.get("override_reason") is None

    @pytest.mark.anyio
    async def test_get_expense_report_with_rejection(self, concur_tool, test_db):
        """Test retrieval of rejected expense report."""
        # Arrange
        request_data = {
            "action": "get_expense_report",
            "expense_report_id": "EXP-1000002",
        }

        # Act
        result = await concur_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("expense_report") is not None
        report = result["expense_report"]
        assert report["id"] == "EXP-1000002"
        assert (
            report["rejection_reason"]
            == "Receipt missing - required for hotel expenses over $150"
        )
        assert report["override_approved"] is False

    @pytest.mark.anyio
    async def test_get_expense_report_with_override(self, concur_tool, test_db):
        """Test retrieval of overridden expense report."""
        # Arrange
        request_data = {
            "action": "get_expense_report",
            "expense_report_id": "EXP-1000003",
        }

        # Act
        result = await concur_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("expense_report") is not None
        report = result["expense_report"]
        assert report["id"] == "EXP-1000003"
        assert (
            report["rejection_reason"]
            == "Itemized receipt required - missing attendee list"
        )
        assert report["override_approved"] is True
        assert report["override_approved_by"] == "sarah.johnson@msg.com"
        assert report["override_reason"] == "justified_exception"

    @pytest.mark.anyio
    async def test_get_expense_report_not_found(self, concur_tool, test_db):
        """Test error when expense report not found."""
        # Arrange
        request_data = {
            "action": "get_expense_report",
            "expense_report_id": "EXP-9999999",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Expense report not found"):
            await concur_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_expense_report_missing_id(self, concur_tool, test_db):
        """Test error when expense_report_id is missing."""
        # Arrange
        request_data = {"action": "get_expense_report"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: expense_report_id"
        ):
            await concur_tool.run_with_validation(test_db, request_data)

    # Tests for override_expense_rejection action
    @pytest.mark.anyio
    async def test_override_expense_rejection_success(self, concur_tool, test_db):
        """Test successful override of expense rejection."""
        # Arrange
        request_data = {
            "action": "override_expense_rejection",
            "expense_report_id": "EXP-1000002",
            "override_reason": "justified_exception",
            "approver_email": "manager@msg.com",
        }

        # Act
        result = await concur_tool.run_with_validation(test_db, request_data)

        # Assert response
        assert result.get("success") is True

        # Assert database state - verify override was applied
        report = test_db.get_by_id(ExpenseReport, "EXP-1000002")
        assert report.override_approved is True
        assert report.override_approved_by == "manager@msg.com"
        assert report.override_reason == OverrideReason.JUSTIFIED_EXCEPTION
        # CRITICAL: Verify rejection_reason is NOT cleared
        assert (
            report.rejection_reason
            == "Receipt missing - required for hotel expenses over $150"
        )

    @pytest.mark.anyio
    async def test_override_expense_rejection_all_override_reasons(
        self, concur_tool, test_db
    ):
        """Test override with all valid override reasons."""
        override_reasons = ["justified_exception", "system_error", "receipt_exception"]

        for idx, reason in enumerate(override_reasons):
            # Create a new rejected report for each test
            report = ExpenseReport(
                id=f"EXP-TEST{idx}",
                employee_email="test@msg.com",
                amount=100,
                category=ExpenseCategory.OTHER,
                trip_location_city=None,
                trip_location_state=None,
                expense_date=datetime(2024, 11, 1),
                receipt_status=ReceiptStatus.ATTACHED,
                rejection_reason="Test rejection",
                override_approved=False,
                override_approved_by=None,
                override_reason=None,
            )
            test_db.create(report)

            # Arrange
            request_data = {
                "action": "override_expense_rejection",
                "expense_report_id": f"EXP-TEST{idx}",
                "override_reason": reason,
                "approver_email": "approver@msg.com",
            }

            # Act
            result = await concur_tool.run_with_validation(test_db, request_data)

            # Assert
            assert result.get("success") is True
            updated = test_db.get_by_id(ExpenseReport, f"EXP-TEST{idx}")
            assert updated.override_approved is True

    @pytest.mark.anyio
    async def test_override_expense_rejection_missing_expense_report_id(
        self, concur_tool, test_db
    ):
        """Test error when expense_report_id is missing."""
        # Arrange
        request_data = {
            "action": "override_expense_rejection",
            "override_reason": "justified_exception",
            "approver_email": "manager@msg.com",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: expense_report_id"
        ):
            await concur_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_override_expense_rejection_missing_override_reason(
        self, concur_tool, test_db
    ):
        """Test error when override_reason is missing."""
        # Arrange
        request_data = {
            "action": "override_expense_rejection",
            "expense_report_id": "EXP-1000002",
            "approver_email": "manager@msg.com",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: override_reason"
        ):
            await concur_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_override_expense_rejection_missing_approver_email(
        self, concur_tool, test_db
    ):
        """Test error when approver_email is missing."""
        # Arrange
        request_data = {
            "action": "override_expense_rejection",
            "expense_report_id": "EXP-1000002",
            "override_reason": "justified_exception",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: approver_email"
        ):
            await concur_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_override_expense_rejection_not_found(self, concur_tool, test_db):
        """Test error when expense report not found."""
        # Arrange
        request_data = {
            "action": "override_expense_rejection",
            "expense_report_id": "EXP-9999999",
            "override_reason": "justified_exception",
            "approver_email": "manager@msg.com",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Expense report not found"):
            await concur_tool.run_with_validation(test_db, request_data)

    # Test for invalid action
    @pytest.mark.anyio
    async def test_invalid_action(self, concur_tool, test_db):
        """Test error with invalid action."""
        # Arrange
        request_data = {"action": "invalid_action"}

        # Act & Assert
        # Pydantic validates enum before our code, so expect input validation error
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await concur_tool.run_with_validation(test_db, request_data)

    # Test for empty database
    @pytest.mark.anyio
    async def test_get_expense_report_empty_database(self, concur_tool):
        """Test get_expense_report with empty database."""
        # Arrange
        empty_db = InMemoryDatabase.__new__(InMemoryDatabase)
        empty_db._stem_to_model_cls = {"expense_reports": ExpenseReport}
        empty_db._model_cls_to_stem = {ExpenseReport: "expense_reports"}
        empty_db._store = {ExpenseReport: []}

        request_data = {
            "action": "get_expense_report",
            "expense_report_id": "EXP-1000001",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Expense report not found"):
            await concur_tool.run_with_validation(empty_db, request_data)

    # Tests for get_travel_booking action
    @pytest.mark.anyio
    async def test_get_travel_booking_success_economy(self, concur_tool, test_db):
        """Test successful travel booking retrieval with economy class."""
        # Arrange
        request_data = {"action": "get_travel_booking", "booking_id": "TRV-1000001"}

        # Act
        result = await concur_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("travel_booking") is not None
        booking = result["travel_booking"]
        assert booking["id"] == "TRV-1000001"
        assert booking["employee_email"] == "john.smith@msg.com"
        assert booking["destination"] == "New York, NY"
        assert booking["departure_date"] == "2024-11-25T08:00:00"
        assert booking["return_date"] == "2024-11-27T18:00:00"
        assert booking["flight_class"] == "economy"
        assert booking["hotel_rate_per_night"] == 250

    @pytest.mark.anyio
    async def test_get_travel_booking_success_business(self, concur_tool, test_db):
        """Test successful travel booking retrieval with business class."""
        # Arrange
        request_data = {"action": "get_travel_booking", "booking_id": "TRV-1000002"}

        # Act
        result = await concur_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("travel_booking") is not None
        booking = result["travel_booking"]
        assert booking["id"] == "TRV-1000002"
        assert booking["employee_email"] == "jane.doe@msg.com"
        assert booking["destination"] == "San Francisco, CA"
        assert booking["flight_class"] == "business"
        assert booking["hotel_rate_per_night"] == 320

    @pytest.mark.anyio
    async def test_get_travel_booking_success_first(self, concur_tool, test_db):
        """Test successful travel booking retrieval with first class."""
        # Arrange
        request_data = {"action": "get_travel_booking", "booking_id": "TRV-1000005"}

        # Act
        result = await concur_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("travel_booking") is not None
        booking = result["travel_booking"]
        assert booking["id"] == "TRV-1000005"
        assert booking["employee_email"] == "emma.garcia@msg.com"
        assert booking["destination"] == "Seattle, WA"
        assert booking["flight_class"] == "first"
        assert booking["hotel_rate_per_night"] == 450

    @pytest.mark.anyio
    async def test_get_travel_booking_without_hotel(self, concur_tool, test_db):
        """Test travel booking retrieval without hotel rate."""
        # Arrange
        request_data = {"action": "get_travel_booking", "booking_id": "TRV-1000004"}

        # Act
        result = await concur_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("travel_booking") is not None
        booking = result["travel_booking"]
        assert booking["id"] == "TRV-1000004"
        assert booking["employee_email"] == "bob.taylor@msg.com"
        assert booking["destination"] == "Boston, MA"
        assert booking["flight_class"] == "economy"
        assert booking.get("hotel_rate_per_night") is None

    @pytest.mark.anyio
    async def test_get_travel_booking_not_found(self, concur_tool, test_db):
        """Test error when travel booking not found."""
        # Arrange
        request_data = {"action": "get_travel_booking", "booking_id": "TRV-9999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Travel booking not found"):
            await concur_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_travel_booking_missing_booking_id(self, concur_tool, test_db):
        """Test error when booking_id is missing."""
        # Arrange
        request_data = {"action": "get_travel_booking"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: booking_id"
        ):
            await concur_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_travel_booking_empty_database(self, concur_tool):
        """Test get_travel_booking with empty database."""
        # Arrange
        empty_db = InMemoryDatabase.__new__(InMemoryDatabase)
        empty_db._stem_to_model_cls = {"travel_requests": TravelRequest}
        empty_db._model_cls_to_stem = {TravelRequest: "travel_requests"}
        empty_db._store = {TravelRequest: []}

        request_data = {"action": "get_travel_booking", "booking_id": "TRV-1000001"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Travel booking not found"):
            await concur_tool.run_with_validation(empty_db, request_data)

    @pytest.mark.anyio
    async def test_get_travel_booking_all_flight_classes(self, concur_tool, test_db):
        """Test travel booking retrieval with all valid flight classes."""
        flight_classes = [
            ("TRV-1000001", "economy"),
            ("TRV-1000002", "business"),
            ("TRV-1000005", "first"),
        ]

        for booking_id, expected_class in flight_classes:
            # Arrange
            request_data = {"action": "get_travel_booking", "booking_id": booking_id}

            # Act
            result = await concur_tool.run_with_validation(test_db, request_data)

            # Assert
            assert result.get("travel_booking") is not None
            booking = result["travel_booking"]
            assert booking["id"] == booking_id
            assert booking["flight_class"] == expected_class

    @pytest.mark.anyio
    async def test_get_travel_booking_output_fields(self, concur_tool, test_db):
        """Test that travel booking output contains all expected fields."""
        # Arrange
        request_data = {"action": "get_travel_booking", "booking_id": "TRV-1000001"}

        # Act
        result = await concur_tool.run_with_validation(test_db, request_data)

        # Assert - verify all required fields are present
        assert result.get("travel_booking") is not None
        booking = result["travel_booking"]
        assert "id" in booking
        assert "employee_email" in booking
        assert "destination" in booking
        assert "departure_date" in booking
        assert "return_date" in booking
        assert "flight_class" in booking
        # hotel_rate_per_night is optional, so just check if key exists
        assert "hotel_rate_per_night" in booking

    @pytest.mark.anyio
    async def test_get_travel_booking_date_format(self, concur_tool, test_db):
        """Test that dates are returned in ISO format."""
        # Arrange
        request_data = {"action": "get_travel_booking", "booking_id": "TRV-1000003"}

        # Act
        result = await concur_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("travel_booking") is not None
        booking = result["travel_booking"]
        # Check ISO format with time component
        assert "T" in booking["departure_date"]
        assert "T" in booking["return_date"]
        assert booking["departure_date"] == "2024-11-28T07:15:00"
        assert booking["return_date"] == "2024-11-29T22:30:00"
