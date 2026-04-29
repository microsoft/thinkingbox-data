#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unit tests for AirlineTauBenchSystem

This module provides comprehensive unit tests for the airline tau-bench system,
covering all major functionality including flight search, booking, cancellation,
updates, and data management.

Test Coverage:
- System initialization and configuration (3 tests)
- Flight search (direct and one-stop) (3 tests)
- User management (2 tests)
- Reservation booking (4 tests including error cases)
- Reservation cancellation and refunds (6 tests)
- Reservation updates (3 tests)
- Utility functions (4 tests)
- Compensation and certificates (2 tests)
- Price quotes (2 tests)
- System operations (3 tests)
- Cost calculations (2 tests)
- Data validation (2 tests)

Total: 36 comprehensive tests covering all major functionality and edge cases.
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest


from thinkingbox_tools.toolslib.airline_tau_bench_system import (
    AirlineTauBenchSystem,
    AirlineTauBenchSystemError,
    CabinClass,
    FlightType,
    MembershipTier,
    Passenger,
    ReservationStatus,
)

TOOLS = [
    "search_direct_flight",
    "search_onestop_flight",
    "book_reservation",
    "cancel_reservation",
    "update_reservation_flights",
    "update_reservation_passengers",
    "update_reservation_baggages",
    "get_reservation_details",
    "get_user_details",
    "send_certificate",
    "calculate",
    "list_all_airports",
    "think",
    "check_price_quote",
    "check_refund_amount",
    "transfer_to_human_agents",
]


class TestAirlineTauBenchSystem:
    """Test suite for AirlineTauBenchSystem"""

    @pytest.fixture
    def system(self):
        """Create a fresh airline system instance for each test"""
        return AirlineTauBenchSystem()

    @staticmethod
    def get_sample_flight_data():
        """Sample flight data for testing"""
        return {
            "HAT001": {
                "flight_number": "HAT001",
                "origin": "JFK",
                "destination": "LAX",
                "scheduled_departure_time_est": "08:00:00",
                "scheduled_arrival_time_est": "11:30:00",
                "dates": {
                    "2024-05-20": {
                        "status": "available",
                        "prices": {
                            "basic_economy": 200.0,
                            "economy": 300.0,
                            "business": 500.0,
                        },
                        "available_seats": {
                            "basic_economy": 50,
                            "economy": 30,
                            "business": 10,
                        },
                    }
                },
            },
            "HAT002": {
                "flight_number": "HAT002",
                "origin": "LAX",
                "destination": "JFK",
                "scheduled_departure_time_est": "14:00:00",
                "scheduled_arrival_time_est": "22:30:00",
                "dates": {
                    "2024-05-22": {
                        "status": "available",
                        "prices": {
                            "basic_economy": 250.0,
                            "economy": 350.0,
                            "business": 550.0,
                        },
                        "available_seats": {
                            "basic_economy": 40,
                            "economy": 25,
                            "business": 8,
                        },
                    }
                },
            },
        }

    @staticmethod
    def get_sample_user_data():
        """Sample user data for testing"""
        return {
            "john_doe_1234": {
                "name": {
                    "first_name": "John",
                    "last_name": "Doe",
                },
                "email": "john.doe@example.com",
                "address": {
                    "address1": "123 Main St",
                    "address2": "Suite 456",
                    "city": "New York",
                    "country": "USA",
                    "state": "NY",
                    "zip": "10085",
                },
                "dob": "1990-01-01",
                "membership": "regular",
                "payment_methods": {
                    "credit_card_1234": {
                        "source": "credit_card",
                        "id": "credit_card_1234",
                        "brand": "Visa",
                        "last_four": "1234",
                    },
                    "gift_card_5678": {
                        "source": "gift_card",
                        "amount": 500.0,
                        "id": "gift_card_5678",
                    },
                },
                "reservations": [],
                "saved_passengers": [],
            }
        }

    @pytest.fixture
    def sample_flight_data(self):
        return TestAirlineTauBenchSystem.get_sample_flight_data()

    @pytest.fixture
    def sample_user_data(self):
        return TestAirlineTauBenchSystem.get_sample_user_data()

    @pytest.fixture
    def configured_system(self, system, sample_flight_data, sample_user_data):
        """System with sample data already configured"""
        config = {
            "flights": sample_flight_data,
            "users": sample_user_data,
            "reservations": {},
        }
        system.configure_data(config)
        return system

    def test_system_initialization(self, system):
        """Test that system initializes with empty data"""
        assert len(system.flights) == 0
        assert len(system.reservations) == 0
        assert len(system.users) == 0

    def test_configure_data_success(self, system, sample_flight_data, sample_user_data):
        """Test successful data configuration"""
        config = {
            "flights": sample_flight_data,
            "users": sample_user_data,
            "reservations": {},
        }
        result = system.configure_data(config)

        assert result["status"] == "configured"
        assert len(system.flights) == 2
        assert len(system.users) == 1
        assert "HAT001" in system.flights
        assert "john_doe_1234" in system.users

    def test_configure_data_invalid_flight(self, system):
        """Test data configuration with invalid flight data"""
        invalid_config = {
            "flights": {
                "INVALID": {
                    "flight_number": "INVALID",
                    "origin": "XX",  # Invalid: too short
                    "destination": "LAX",
                    "scheduled_departure_time_est": "08:00:00",
                    "scheduled_arrival_time_est": "11:30:00",
                    "dates": {},
                }
            },
            "users": {},
            "reservations": {},
        }

        with pytest.raises(AirlineTauBenchSystemError, match="Invalid flight data"):
            system.configure_data(invalid_config)

    def test_search_direct_flight_success(self, configured_system):
        """Test successful direct flight search"""
        results = configured_system.search_direct_flight("JFK", "LAX", "2024-05-20")

        assert len(results) == 1
        assert results[0].flight_number == "HAT001"
        assert results[0].origin == "JFK"
        assert results[0].destination == "LAX"
        assert results[0].date == "2024-05-20"

    def test_search_direct_flight_no_results(self, configured_system):
        """Test direct flight search with no results"""
        results = configured_system.search_direct_flight("JFK", "LAX", "2024-05-21")
        assert len(results) == 0

    def test_search_onestop_flight(self, configured_system):
        """Test one-stop flight search"""
        # Add connecting flight for testing
        connecting_flight = {
            "HAT003": {
                "flight_number": "HAT003",
                "origin": "JFK",
                "destination": "DEN",
                "scheduled_departure_time_est": "09:00:00",
                "scheduled_arrival_time_est": "12:00:00",
                "dates": {
                    "2024-05-20": {
                        "status": "available",
                        "prices": {
                            "basic_economy": 150.0,
                            "economy": 250.0,
                            "business": 400.0,
                        },
                        "available_seats": {
                            "basic_economy": 30,
                            "economy": 20,
                            "business": 5,
                        },
                    }
                },
            },
            "HAT004": {
                "flight_number": "HAT004",
                "origin": "DEN",
                "destination": "LAX",
                "scheduled_departure_time_est": "14:00:00",
                "scheduled_arrival_time_est": "16:00:00",
                "dates": {
                    "2024-05-20": {
                        "status": "available",
                        "prices": {
                            "basic_economy": 100.0,
                            "economy": 200.0,
                            "business": 350.0,
                        },
                        "available_seats": {
                            "basic_economy": 25,
                            "economy": 15,
                            "business": 3,
                        },
                    }
                },
            },
        }

        # Add to existing flights
        for flight_id, flight_data in connecting_flight.items():
            configured_system.flights[flight_id] = (
                configured_system._convert_flight_data(flight_data)
            )

        results = configured_system.search_onestop_flight("JFK", "LAX", "2024-05-20")

        assert len(results) == 1
        assert results[0].connecting_airport == "DEN"
        assert results[0].first_flight.flight_number == "HAT003"
        assert results[0].second_flight.flight_number == "HAT004"

    def test_get_user_details_success(self, configured_system):
        """Test successful user details retrieval"""
        user = configured_system.get_user_details("john_doe_1234")

        assert user.user_id == "john_doe_1234"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.membership_level == MembershipTier.REGULAR

    def test_get_user_details_not_found(self, configured_system):
        """Test user details retrieval for non-existent user"""
        with pytest.raises(
            AirlineTauBenchSystemError, match="User nonexistent not found"
        ):
            configured_system.get_user_details("nonexistent")

    def test_book_reservation_success(self, configured_system):
        """Test successful reservation booking"""
        result = configured_system.book_reservation(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type="one_way",
            cabin="economy",
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
            ],
            payment_methods=[{"payment_id": "gift_card_5678", "amount": 300.0}],
            total_baggages=1,
            nonfree_baggages=0,
            insurance="no",
        )

        assert result["status"] == "confirmed"
        assert "reservation_id" in result
        assert result["total_price"] == 300.0

        # Check that reservation was added
        reservation_id = result["reservation_id"]
        assert reservation_id in configured_system.reservations

        # Check that user's reservations list was updated
        user = configured_system.get_user_details("john_doe_1234")
        assert reservation_id in user.reservations

    def test_book_reservation_insufficient_seats(self, configured_system):
        """Test booking with too many passengers (exceeds 5 passenger limit)"""
        # Try to book more passengers than allowed (max 5)
        passengers = [
            {"first_name": f"Passenger{i}", "last_name": "Test", "dob": "1990-01-01"}
            for i in range(6)  # More than 5 passengers allowed
        ]

        with pytest.raises(
            AirlineTauBenchSystemError, match="Passengers must be between 1 and 5"
        ):
            configured_system.book_reservation(
                user_id="john_doe_1234",
                origin="JFK",
                destination="LAX",
                flight_type="one_way",
                cabin="economy",
                flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
                passengers=passengers,
                payment_methods=[{"payment_id": "gift_card_5678", "amount": 1800.0}],
            )

    def test_book_reservation_insufficient_payment(self, configured_system):
        """Test booking with insufficient payment"""
        with pytest.raises(
            AirlineTauBenchSystemError, match="Payment total .* does not match expected"
        ):
            configured_system.book_reservation(
                user_id="john_doe_1234",
                origin="JFK",
                destination="LAX",
                flight_type="one_way",
                cabin="economy",
                flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
                passengers=[
                    {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
                ],
                payment_methods=[
                    {"payment_id": "gift_card_5678", "amount": 100.0}
                ],  # Too little
            )

    def test_cancel_reservation_success(self, configured_system):
        """Test successful reservation cancellation"""
        # First book a reservation
        result = configured_system.book_reservation(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type="one_way",
            cabin="business",  # Business class for partial refund
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
            ],
            payment_methods=[{"payment_id": "gift_card_5678", "amount": 500.0}],
        )

        reservation_id = result["reservation_id"]

        # Cancel the reservation
        cancel_result = configured_system.cancel_reservation(
            reservation_id, "change_of_plan"
        )

        assert cancel_result["status"] == "cancelled"
        assert cancel_result["reservation_id"] == reservation_id
        assert cancel_result["refund_amount"] == 400.0  # 80% of 500

        # Check that reservation status was updated
        reservation = configured_system.get_reservation_details(reservation_id)
        assert reservation.status == ReservationStatus.CANCELLED

    def test_cancel_already_cancelled_reservation(self, configured_system):
        """Test cancelling an already cancelled reservation"""
        # Book and cancel a reservation
        result = configured_system.book_reservation(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type="one_way",
            cabin="economy",
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
            ],
            payment_methods=[{"payment_id": "gift_card_5678", "amount": 300.0}],
        )

        reservation_id = result["reservation_id"]
        configured_system.cancel_reservation(reservation_id, "change_of_plan")

        # Try to cancel again
        with pytest.raises(
            AirlineTauBenchSystemError, match="Reservation already cancelled"
        ):
            configured_system.cancel_reservation(reservation_id, "change_of_plan")

    def test_check_refund_amount(self, configured_system):
        """Test refund amount calculation without cancelling"""
        # Book a business class reservation
        result = configured_system.book_reservation(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type="one_way",
            cabin="business",
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
            ],
            payment_methods=[{"payment_id": "gift_card_5678", "amount": 500.0}],
        )

        reservation_id = result["reservation_id"]

        # Check refund amount
        refund_info = configured_system.check_refund_amount(
            reservation_id, "change_of_plan"
        )

        assert refund_info["reservation_id"] == reservation_id
        assert refund_info["total_price"] == 500.0
        assert refund_info["refund_amount"] == 400.0  # 80% for business
        assert refund_info["cabin_class"] == "business"
        assert "Partial refund available" in refund_info["eligibility_message"]

    def test_check_refund_amount_within_24_hours(self, configured_system):
        """Test checking refund amount for a reservation booked 1 hour ago (within 24-hour window)"""
        # Mock the current time to be 1 hour after the fixed booking time
        fixed_booking_time = datetime(
            2024, 5, 15, 15, 0, 0, tzinfo=timezone(timedelta(hours=-5))
        )
        current_time = fixed_booking_time + timedelta(hours=1)  # 1 hour later

        with patch(
            "thinkingbox_tools.toolslib.airline_tau_bench_system.datetime"
        ) as mock_datetime:
            # Set up the mock to return our fixed times
            mock_datetime.now.return_value = current_time
            mock_datetime.fromisoformat.side_effect = datetime.fromisoformat
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            # Book a basic economy reservation without insurance
            result = configured_system.book_reservation(
                user_id="john_doe_1234",
                origin="JFK",
                destination="LAX",
                flight_type="one_way",
                cabin="basic_economy",
                flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
                passengers=[
                    {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
                ],
                payment_methods=[{"payment_id": "gift_card_5678", "amount": 200.0}],
                insurance="no",
            )

            reservation_id = result["reservation_id"]

            # Manually set the created_at time to 1 hour ago
            reservation = configured_system.get_reservation_details(reservation_id)
            reservation.created_at = fixed_booking_time.isoformat()

            # Check refund amount (should be full refund due to 24-hour window)
            refund_info = configured_system.check_refund_amount(
                reservation_id, "change_of_plan"
            )

            assert refund_info["reservation_id"] == reservation_id
            assert refund_info["total_price"] == 200.0
            assert refund_info["refund_amount"] == 200.0  # Full refund within 24 hours
            assert refund_info["cabin_class"] == "basic_economy"
            assert refund_info["insurance"] == "no"
            assert "Full refund available" in refund_info["eligibility_message"]

    def test_update_reservation_passengers_success(self, configured_system):
        """Test successful passenger update"""
        # Book a reservation
        result = configured_system.book_reservation(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type="one_way",
            cabin="economy",
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
            ],
            payment_methods=[{"payment_id": "gift_card_5678", "amount": 300.0}],
        )

        reservation_id = result["reservation_id"]

        # Update passenger info
        update_result = configured_system.update_reservation_passengers(
            reservation_id,
            [{"first_name": "Jane", "last_name": "Doe", "dob": "1985-05-15"}],
        )

        assert update_result["status"] == "updated"
        assert update_result["passengers"][0]["first_name"] == "Jane"

    def test_update_reservation_passengers_basic_economy(self, configured_system):
        """Test passenger update for basic economy (should fail)"""
        # Book a basic economy reservation
        result = configured_system.book_reservation(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type="one_way",
            cabin="basic_economy",
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
            ],
            payment_methods=[{"payment_id": "gift_card_5678", "amount": 200.0}],
        )

        reservation_id = result["reservation_id"]

        # Try to update passengers (should fail)
        with pytest.raises(
            AirlineTauBenchSystemError, match="Basic economy tickets cannot be modified"
        ):
            configured_system.update_reservation_passengers(
                reservation_id,
                [{"first_name": "Jane", "last_name": "Doe", "dob": "1985-05-15"}],
            )

    def test_update_reservation_flights_success(self, configured_system):
        """Test successful flight update"""
        # Book a reservation
        result = configured_system.book_reservation(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type="one_way",
            cabin="economy",
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
            ],
            payment_methods=[{"payment_id": "gift_card_5678", "amount": 300.0}],
        )

        reservation_id = result["reservation_id"]

        # Update to business class
        update_result = configured_system.update_reservation_flights(
            reservation_id,
            "business",
            [{"flight_number": "HAT001", "date": "2024-05-20"}],
            "gift_card_5678",
        )

        assert update_result["status"] == "updated"
        assert update_result["cabin"] == "business"
        assert update_result["price_difference"] == 200.0  # 500 - 300

    def test_list_all_airports(self, configured_system):
        """Test airport listing"""
        airports = configured_system.list_all_airports()

        assert len(airports) == 2
        assert "JFK" in airports
        assert "LAX" in airports
        assert airports == sorted(airports)  # Should be sorted

    def test_calculate_expression(self, configured_system):
        """Test mathematical calculation"""
        result = configured_system.calculate("2 + 3 * 4")
        assert result == 14.0

        result = configured_system.calculate("(10 + 5) / 3")
        assert result == 5.0

    def test_calculate_invalid_expression(self, configured_system):
        """Test calculation with invalid characters"""
        with pytest.raises(
            AirlineTauBenchSystemError, match="Invalid characters in expression"
        ):
            configured_system.calculate("2 + eval('malicious code')")

    def test_send_certificate_success(self, configured_system):
        """Test certificate sending for eligible user"""
        # Make user silver member
        user = configured_system.get_user_details("john_doe_1234")
        user.membership_level = MembershipTier.SILVER

        # Book a reservation
        result = configured_system.book_reservation(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type="one_way",
            cabin="economy",
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
            ],
            payment_methods=[{"payment_id": "gift_card_5678", "amount": 300.0}],
        )

        reservation_id = result["reservation_id"]

        # Send certificate
        cert_result = configured_system.send_certificate(
            "john_doe_1234",
            "delayed_flight",
            reservation_id,
            0,  # Amount will be auto-calculated
        )

        assert cert_result["status"] == "issued"
        assert cert_result["amount"] == 50  # 50 per passenger for delayed flight
        assert "certificate_id" in cert_result

        # Check that certificate was added to user's payment methods
        updated_user = configured_system.get_user_details("john_doe_1234")
        cert_id = cert_result["certificate_id"]
        assert cert_id in updated_user.payment_methods

    def test_send_certificate_ineligible_user(self, configured_system):
        """Test certificate sending for ineligible user"""
        # Book a basic economy reservation without insurance (ineligible)
        result = configured_system.book_reservation(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type="one_way",
            cabin="basic_economy",
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
            ],
            payment_methods=[{"payment_id": "gift_card_5678", "amount": 200.0}],
        )

        reservation_id = result["reservation_id"]

        # Try to send certificate (should fail)
        with pytest.raises(
            AirlineTauBenchSystemError, match="User not eligible for compensation"
        ):
            configured_system.send_certificate(
                "john_doe_1234", "delayed_flight", reservation_id, 0
            )

    def test_check_price_quote_new_booking(self, configured_system):
        """Test price quote for new booking"""
        quote = configured_system.check_price_quote(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type="one_way",
            cabin="economy",
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
            ],
            total_baggages=1,
            nonfree_baggages=0,
            insurance="no",
        )

        assert quote["quote_type"] == "new_booking"
        assert quote["pricing_breakdown"]["base_flight_price"] == 300.0
        assert quote["pricing_breakdown"]["insurance_cost"] == 0
        assert quote["pricing_breakdown"]["baggage_cost"] == 0
        assert quote["pricing_breakdown"]["total_price"] == 300.0

    def test_check_price_quote_with_change(self, configured_system):
        """Test price quote for reservation change"""
        # First book a reservation
        result = configured_system.book_reservation(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type="one_way",
            cabin="economy",
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
            ],
            payment_methods=[{"payment_id": "gift_card_5678", "amount": 300.0}],
        )

        reservation_id = result["reservation_id"]

        # Get quote for upgrading to business
        quote = configured_system.check_price_quote(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type="one_way",
            cabin="business",
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
            ],
            reservation_id=reservation_id,
        )

        assert quote["quote_type"] == "change"
        assert quote["change_details"]["current_price"] == 300.0
        assert quote["change_details"]["new_price"] == 500.0
        assert quote["change_details"]["price_difference"] == 200.0

    def test_fixed_datetime(self, system):
        """Test that the system uses fixed datetime"""
        # The _now() method should return a fixed datetime
        fixed_time = system._now()
        assert fixed_time == "2024-05-15T15:00:00-05:00"

    def test_transfer_to_human_agents(self, configured_system):
        """Test transfer to human agents"""
        result = configured_system.transfer_to_human_agents(
            "Complex issue requiring human intervention"
        )

        assert result["status"] == "transferred"
        assert result["summary"] == "Complex issue requiring human intervention"
        assert "transfer_id" in result
        assert "timestamp" in result

    def test_think_method(self, configured_system):
        """Test think method"""
        result = configured_system.think("Analyzing customer request")

        assert result["status"] == "recorded"
        assert result["thought"] == "Analyzing customer request"
        assert "timestamp" in result

    def test_get_current_data(self, configured_system):
        """Test getting current system data"""
        data = configured_system.get_current_data()

        assert len(data.flights) == 2
        assert len(data.users) == 1
        assert len(data.reservations) == 0

    def test_baggage_cost_calculation(self, configured_system):
        """Test baggage cost calculation for different membership levels"""
        # Test regular member with economy (1 free bag)
        user = configured_system.get_user_details("john_doe_1234")

        # Mock booking request for testing baggage calculation
        from thinkingbox_tools.toolslib.airline_tau_bench_system import BookingRequest

        req = BookingRequest(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type=FlightType.ONE_WAY,
            cabin=CabinClass.ECONOMY,
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                Passenger(first_name="John", last_name="Doe", dob="1990-01-01")
            ],
            payment_methods=[{"payment_id": "gift_card_5678", "amount": 300.0}],
            total_baggages=2,  # 2 bags total
            nonfree_baggages=1,  # 1 bag should incur fee
            insurance="no",
        )

        baggage_cost = configured_system._baggage_cost(req, user)
        assert baggage_cost == 50  # 1 extra bag * $50

    def test_insurance_cost_calculation(self, configured_system):
        """Test insurance cost calculation"""
        from thinkingbox_tools.toolslib.airline_tau_bench_system import BookingRequest

        req_with_insurance = BookingRequest(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type=FlightType.ONE_WAY,
            cabin=CabinClass.ECONOMY,
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                Passenger(first_name="John", last_name="Doe", dob="1990-01-01")
            ],
            payment_methods=[{"payment_id": "gift_card_5678", "amount": 330.0}],
            insurance="yes",
        )

        insurance_cost = configured_system._insurance_cost(req_with_insurance)
        assert insurance_cost == 30  # $30 per passenger

        req_without_insurance = BookingRequest(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type=FlightType.ONE_WAY,
            cabin=CabinClass.ECONOMY,
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                Passenger(first_name="John", last_name="Doe", dob="1990-01-01")
            ],
            payment_methods=[{"payment_id": "gift_card_5678", "amount": 300.0}],
            insurance="no",
        )

        insurance_cost = configured_system._insurance_cost(req_without_insurance)
        assert insurance_cost == 0

    def test_book_reservation_insufficient_seat_availability(self, configured_system):
        """Test booking with insufficient seat availability"""
        # Create a flight with very limited seats
        limited_flight = {
            "HAT999": {
                "flight_number": "HAT999",
                "origin": "JFK",
                "destination": "LAX",
                "scheduled_departure_time_est": "10:00:00",
                "scheduled_arrival_time_est": "13:30:00",
                "dates": {
                    "2024-05-21": {
                        "status": "available",
                        "prices": {
                            "basic_economy": 200.0,
                            "economy": 300.0,
                            "business": 500.0,
                        },
                        "available_seats": {
                            "basic_economy": 1,  # Only 1 seat available
                            "economy": 1,
                            "business": 1,
                        },
                    }
                },
            }
        }

        # Add the flight to the system
        for flight_id, flight_data in limited_flight.items():
            configured_system.flights[flight_id] = (
                configured_system._convert_flight_data(flight_data)
            )

        # Try to book 2 passengers when only 1 seat available
        passengers = [
            {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"},
            {"first_name": "Jane", "last_name": "Doe", "dob": "1985-05-15"},
        ]

        with pytest.raises(
            AirlineTauBenchSystemError,
            match="Not enough economy seats on HAT999 2024-05-21",
        ):
            configured_system.book_reservation(
                user_id="john_doe_1234",
                origin="JFK",
                destination="LAX",
                flight_type="one_way",
                cabin="economy",
                flights=[{"flight_number": "HAT999", "date": "2024-05-21"}],
                passengers=passengers,
                payment_methods=[{"payment_id": "gift_card_5678", "amount": 600.0}],
            )

    def test_cancel_reservation_within_24_hours(self, configured_system):
        """Test cancelling a reservation that was booked 1 hour ago (within 24-hour window)"""
        # Mock the current time to be 1 hour after the fixed booking time
        fixed_booking_time = datetime(
            2024, 5, 15, 15, 0, 0, tzinfo=timezone(timedelta(hours=-5))
        )
        current_time = fixed_booking_time + timedelta(hours=1)  # 1 hour later

        with patch(
            "thinkingbox_tools.toolslib.airline_tau_bench_system.datetime"
        ) as mock_datetime:
            # Set up the mock to return our fixed times
            mock_datetime.now.return_value = current_time
            mock_datetime.fromisoformat.side_effect = datetime.fromisoformat
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            # Book a basic economy reservation without insurance
            result = configured_system.book_reservation(
                user_id="john_doe_1234",
                origin="JFK",
                destination="LAX",
                flight_type="one_way",
                cabin="basic_economy",
                flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
                passengers=[
                    {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
                ],
                payment_methods=[{"payment_id": "gift_card_5678", "amount": 200.0}],
                insurance="no",
            )

            reservation_id = result["reservation_id"]

            # Manually set the created_at time to 1 hour ago
            reservation = configured_system.get_reservation_details(reservation_id)
            reservation.created_at = fixed_booking_time.isoformat()

            # Cancel the reservation (should get full refund due to 24-hour window)
            cancel_result = configured_system.cancel_reservation(
                reservation_id, "change_of_plan"
            )

            assert cancel_result["status"] == "cancelled"
            assert cancel_result["reservation_id"] == reservation_id
            assert (
                cancel_result["refund_amount"] == 200.0
            )  # Full refund within 24 hours

            # Check that reservation status was updated
            updated_reservation = configured_system.get_reservation_details(
                reservation_id
            )
            assert updated_reservation.status == ReservationStatus.CANCELLED
            assert updated_reservation.cancellation_reason == "change_of_plan"

    def test_cancel_reservation_after_24_hours(self, configured_system):
        """Test cancelling a reservation that was booked 25 hours ago (outside 24-hour window)"""
        # Mock the current time to be 25 hours after the fixed booking time
        fixed_booking_time = datetime(
            2024, 5, 15, 15, 0, 0, tzinfo=timezone(timedelta(hours=-5))
        )
        current_time = fixed_booking_time + timedelta(hours=25)  # 25 hours later

        with patch(
            "thinkingbox_tools.toolslib.airline_tau_bench_system.datetime"
        ) as mock_datetime:
            # Set up the mock to return our fixed times
            mock_datetime.now.return_value = current_time
            mock_datetime.fromisoformat.side_effect = datetime.fromisoformat
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            # Book a basic economy reservation without insurance
            result = configured_system.book_reservation(
                user_id="john_doe_1234",
                origin="JFK",
                destination="LAX",
                flight_type="one_way",
                cabin="basic_economy",
                flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
                passengers=[
                    {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
                ],
                payment_methods=[{"payment_id": "gift_card_5678", "amount": 200.0}],
                insurance="no",
            )

            reservation_id = result["reservation_id"]

            # Manually set the created_at time to 25 hours ago
            reservation = configured_system.get_reservation_details(reservation_id)
            reservation.created_at = fixed_booking_time.isoformat()

            # Cancel the reservation (should get no refund - outside 24 hours, basic economy, no insurance)
            cancel_result = configured_system.cancel_reservation(
                reservation_id, "change_of_plan"
            )

            assert cancel_result["status"] == "cancelled"
            assert cancel_result["reservation_id"] == reservation_id
            assert (
                cancel_result["refund_amount"] == 0.0
            )  # No refund outside 24 hours for basic economy without insurance

            # Check that reservation status was updated
            updated_reservation = configured_system.get_reservation_details(
                reservation_id
            )
            assert updated_reservation.status == ReservationStatus.CANCELLED
            assert updated_reservation.cancellation_reason == "change_of_plan"

    def test_flight_data_validation(self, system):
        """Test flight data model validation"""
        # Test invalid airport code (too short)
        invalid_flight = {
            "TEST001": {
                "flight_number": "TEST001",
                "origin": "XX",  # Invalid: too short
                "destination": "LAX",
                "scheduled_departure_time_est": "08:00:00",
                "scheduled_arrival_time_est": "11:30:00",
                "dates": {
                    "2024-05-20": {
                        "status": "available",
                        "prices": {
                            "basic_economy": 200.0,
                            "economy": 300.0,
                            "business": 500.0,
                        },
                        "available_seats": {
                            "basic_economy": 50,
                            "economy": 30,
                            "business": 10,
                        },
                    }
                },
            }
        }

        with pytest.raises(AirlineTauBenchSystemError, match="Invalid flight data"):
            system.configure_data(
                {"flights": invalid_flight, "users": {}, "reservations": {}}
            )

    def test_payment_method_validation(self, configured_system):
        """Test payment method validation in booking"""
        # Test booking with invalid payment method (non-existent)
        with pytest.raises(
            AirlineTauBenchSystemError, match="Payment method .* not on user profile"
        ):
            configured_system.book_reservation(
                user_id="john_doe_1234",
                origin="JFK",
                destination="LAX",
                flight_type="one_way",
                cabin="economy",
                flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
                passengers=[
                    {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
                ],
                payment_methods=[{"payment_id": "nonexistent_card", "amount": 300.0}],
            )

    def test_cancel_reservation_with_cancelled_flight(self, configured_system):
        """Test cancelling a reservation when the flight status has changed to cancelled"""
        from thinkingbox_tools.toolslib.airline_tau_bench_system import FlightStatus

        # Book a reservation first
        result = configured_system.book_reservation(
            user_id="john_doe_1234",
            origin="JFK",
            destination="LAX",
            flight_type="one_way",
            cabin="economy",
            flights=[{"flight_number": "HAT001", "date": "2024-05-20"}],
            passengers=[
                {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}
            ],
            payment_methods=[{"payment_id": "gift_card_5678", "amount": 300.0}],
        )

        reservation_id = result["reservation_id"]

        # Simulate the flight being cancelled after booking
        # This sets available_seats to None (per the model validation)
        flight_date_info = configured_system.flights["HAT001"].dates["2024-05-20"]
        flight_date_info.status = FlightStatus.CANCELLED
        flight_date_info.available_seats = None

        # Now try to cancel the reservation - should handle None available_seats gracefully
        cancel_result = configured_system.cancel_reservation(
            reservation_id, "airline_cancelled_flight"
        )

        assert cancel_result["status"] == "cancelled"
        assert cancel_result["reservation_id"] == reservation_id
        # Should get full refund since airline cancelled
        assert cancel_result["refund_amount"] == 300.0


@pytest.mark.asyncio
async def test_server_search_direct_flight(session_proxy):
    """Test successful direct flight search using the MCP server"""

    server_config = {
        "airline_tau_bench": {
            "flights": TestAirlineTauBenchSystem.get_sample_flight_data(),
            "users": TestAirlineTauBenchSystem.get_sample_user_data(),
            "reservations": {},
        },
    }

    async with session_proxy.get(server_config, TOOLS) as session:
        session: MCPProxyClient
        response = await session.call_tool(
            "search_direct_flight",
            origin="JFK",
            destination="LAX",
            date="2024-05-20",
        )
        results = json.loads(response)["flights"]

    assert len(results) == 1
    assert results[0]["flight_number"] == "HAT001"
    assert results[0]["origin"] == "JFK"
    assert results[0]["destination"] == "LAX"
    assert results[0]["date"] == "2024-05-20"


@pytest.mark.asyncio
async def test_server_loadjson_search_direct_flight(tmp_path, session_proxy):
    """Test successful direct flight search using the MCP server,
    letting the server load the database from a json file
    """

    flights_path = tmp_path / "flights.json"
    users_path = tmp_path / "users.json"
    reservations_path = tmp_path / "reservations.json"

    with open(flights_path, "w", encoding="utf-8") as f:
        json.dump(
            TestAirlineTauBenchSystem.get_sample_flight_data(),
            f,
        )
    with open(users_path, "w", encoding="utf-8") as f:
        json.dump(
            TestAirlineTauBenchSystem.get_sample_user_data(),
            f,
        )
    with open(reservations_path, "w", encoding="utf-8") as f:
        json.dump({}, f)

    server_config = {
        "airline_tau_bench": {
            "flights": str(flights_path.resolve()),
            "users": str(users_path.resolve()),
            "reservations": str(reservations_path.resolve()),
        }
    }

    async with session_proxy.get(server_config, TOOLS) as session:
        session: MCPProxyClient
        response = await session.call_tool(
            "search_direct_flight",
            origin="JFK",
            destination="LAX",
            date="2024-05-20",
        )
        results = json.loads(response)["flights"]

    assert len(results) == 1
    assert results[0]["flight_number"] == "HAT001"
    assert results[0]["origin"] == "JFK"
    assert results[0]["destination"] == "LAX"
    assert results[0]["date"] == "2024-05-20"
