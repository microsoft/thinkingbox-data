#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
MCP Server for Airline Domain - Tau-bench Implementation

This server provides Model Context Protocol (MCP) tools that fully implement
the tau-bench airline environment with all features and tool capabilities.
"""

import json
import logging
import os
import traceback
from typing import Annotated, Any, Dict, List, Literal, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from pydantic_core import to_jsonable_python

from thinkingbox_tools.toolslib.airline_tau_bench_system import (
    AirlineTauBenchSystem,
    AirlineTauBenchSystemError,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class FlightDetail(BaseModel):
    """Flight information for booking"""

    flight_number: str = Field(description="Flight number (e.g., 'HAT001')")
    date: str = Field(
        description="Flight date in YYYY-MM-DD format (e.g., '2024-05-20')"
    )


class PassengerInfo(BaseModel):
    """Passenger information for booking"""

    first_name: str = Field(description="Passenger's first name")
    last_name: str = Field(description="Passenger's last name")
    dob: str = Field(
        description="Date of birth in YYYY-MM-DD format (e.g., '1990-01-01')"
    )


class PaymentMethod(BaseModel):
    """Payment method details"""

    payment_id: str = Field(
        description="Payment method ID (e.g., 'credit_card_1234', 'certificate_5678')"
    )
    amount: float = Field(description="Amount to charge to this payment method")


app = FastMCP("airline_tau_bench")
db = AirlineTauBenchSystem()


class SuccessResponse(BaseModel):
    status: Literal["ok"]


def error_response(exc) -> str:
    if isinstance(exc, AirlineTauBenchSystemError):
        return "Error!\n" + str(exc)
    traceback.print_exc()
    return "Error!"


def success_response(**kwargs) -> str:
    obj = {
        "status": "ok",
        **to_jsonable_python(kwargs),
    }
    return json.dumps(obj)


def load_json(path: str):
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.tool(name="__reserved__init")
async def initialize(config: dict) -> str:
    """Initialize the airline tau-bench system with configuration data."""
    # The config passed here should be the airline portion of the world_state
    # if it's a string then it's a pointer to a json file
    if isinstance(config["flights"], str):
        config["flights"] = load_json(config["flights"])
    if isinstance(config["reservations"], str):
        config["reservations"] = load_json(config["reservations"])
    if isinstance(config["users"], str):
        config["users"] = load_json(config["users"])
    db.configure_data(config)
    return json.dumps({})


@app.tool(name="__reserved__geteffects")
async def geteffects() -> str:
    """Get the current state from the airline tau-bench system."""
    obj = {
        "reservations": db.reservations,
        "users": db.users,
    }
    return json.dumps(to_jsonable_python(obj))


@app.tool(
    name="search_direct_flight",
    description="Search for direct flights between two airports on a specific date",
)
async def search_direct_flight(
    origin: Annotated[
        str, Field(description="Origin airport code (3 letters, e.g., 'JFK')")
    ],
    destination: Annotated[
        str, Field(description="Destination airport code (3 letters, e.g., 'LAX')")
    ],
    date: Annotated[str, Field(description="Flight date in YYYY-MM-DD format")],
) -> str:
    """Search for direct flights between two airports on a specific date

    Args:
        origin: Origin airport code (3 letters, e.g., 'JFK')
        destination: Destination airport code (3 letters, e.g., 'LAX')
        date: Flight date in YYYY-MM-DD format
    """
    try:
        logger.info(
            "Starting a search for direct flights from %s to %s on %s",
            origin,
            destination,
            date,
        )
        flights = db.search_direct_flight(origin, destination, date)
        logger.info("Found %d direct flights", len(flights))
        return success_response(flights=flights)
    except Exception as e:
        return error_response(e)


@app.tool(
    name="search_onestop_flight",
    description="Search for one-stop connecting flights between two airports on a specific date",
)
async def search_onestop_flight(
    origin: Annotated[
        str, Field(description="Origin airport code (3 letters, e.g., 'JFK')")
    ],
    destination: Annotated[
        str, Field(description="Destination airport code (3 letters, e.g., 'LAX')")
    ],
    date: Annotated[str, Field(description="Flight date in YYYY-MM-DD format")],
) -> str:
    """Search for one-stop flights between two airports on a specific date

    Args:
        origin: Origin airport code (3 letters, e.g., 'JFK')
        destination: Destination airport code (3 letters, e.g., 'LAX')
        date: Flight date in YYYY-MM-DD format
    """
    try:
        logger.info(
            "Starting a search for one-stop flights from %s to %s on %s",
            origin,
            destination,
            date,
        )
        flights = db.search_onestop_flight(origin, destination, date)
        logger.info("Found %d one-stop flights", len(flights))
        return success_response(flights=flights)
    except Exception as e:
        return error_response(e)


@app.tool(
    name="get_user_details",
    description="Get user profile details including payment methods and reservations by user ID",
)
async def get_user_details(
    user_id: Annotated[str, Field(description="Customer's user ID to look up")],
) -> str:
    """Get user profile details by user ID

    Args:
        user_id: User ID to look up
    """
    try:
        logger.info("Retrieving user details for user ID: %s", user_id)
        user = db.get_user_details(user_id)
        logger.info("User details retrieved successfully for user ID: %s", user_id)
        return success_response(user=user)
    except Exception as e:
        return error_response(e)


@app.tool(
    name="get_reservation_details",
    description="Get reservation details including flights, passengers, and payment information by reservation ID",
)
async def get_reservation_details(
    reservation_id: Annotated[str, Field(description="Reservation ID to look up")],
) -> str:
    """Get reservation details by reservation ID

    Args:
        reservation_id: Reservation ID to look up
    """
    try:
        logger.info(
            "Retrieving reservation details for reservation ID: %s", reservation_id
        )
        reservation = db.get_reservation_details(reservation_id)
        return success_response(reservation=reservation)
    except Exception as e:
        return error_response(e)


@app.tool(
    name="book_reservation",
    description="Book a new flight reservation with specified flights, passengers, and payment methods",
)
async def book_reservation(
    user_id: Annotated[
        str, Field(description="User ID of the person making the reservation")
    ],
    origin: Annotated[
        str, Field(description="Origin airport code (3 letters, e.g., 'JFK')")
    ],
    destination: Annotated[
        str, Field(description="Destination airport code (3 letters, e.g., 'LAX')")
    ],
    flight_type: Annotated[
        str, Field(description="Type of flight booking (one_way, round_trip)")
    ],
    cabin: Annotated[
        str, Field(description="Cabin class (basic_economy, economy, business)")
    ],
    flights: Annotated[
        List[FlightDetail],
        Field(description="List of flight details for the booking"),
    ],
    passengers: Annotated[
        List[PassengerInfo],
        Field(description="List of passenger information for the booking"),
    ],
    payment_methods: Annotated[
        List[PaymentMethod],
        Field(description="List of payment methods with amounts for the booking"),
    ],
    total_baggages: Annotated[
        int, Field(description="Total number of baggage items (default: 0)")
    ] = 0,
    nonfree_baggages: Annotated[
        int,
        Field(
            description="Number of non-free baggage items that incur fees (default: 0)"
        ),
    ] = 0,
    insurance: Annotated[
        str, Field(description="Insurance option (yes, no, default: no)")
    ] = "no",
) -> str:
    """Book a new flight reservation

    Args:
        user_id: User ID of the person making the reservation
        origin: Origin airport code (3 letters, e.g., 'JFK')
        destination: Destination airport code (3 letters, e.g., 'LAX')
        flight_type: Flight type (one_way, round_trip)
        cabin: Cabin class (basic_economy, economy, business)
        flights: List of FlightDetail objects with flight_number and date
        passengers: List of PassengerInfo objects with first_name, last_name, and dob
        payment_methods: List of PaymentMethod objects with payment_id and amount
        total_baggages: Total number of baggage items (default: 0)
        nonfree_baggages: Number of non-free baggage items (default: 0)
        insurance: Insurance option (yes, no, default: no)
    """
    try:
        logger.info(
            "Booking reservation for user ID: %s from %s to %s with flight type %s and cabin %s",
            user_id,
            origin,
            destination,
            flight_type,
            cabin,
        )
        logger.info("Flights: %s", flights)
        logger.info("Passengers: %s", passengers)
        logger.info("Payment methods: %s", payment_methods)
        result = db.book_reservation(
            user_id=user_id,
            origin=origin,
            destination=destination,
            flight_type=flight_type,
            cabin=cabin,
            flights=[flight.model_dump() for flight in flights],
            passengers=[passenger.model_dump() for passenger in passengers],
            payment_methods=[payment.model_dump() for payment in payment_methods],
            total_baggages=total_baggages,
            nonfree_baggages=nonfree_baggages,
            insurance=insurance,
        )
        logger.info(
            "Reservation booked successfully with ID: %s", result["reservation_id"]
        )
        return success_response(
            reservation_id=result["reservation_id"], total_price=result["total_price"]
        )
    except Exception as e:
        return error_response(e)


@app.tool(
    name="cancel_reservation",
    description="Cancel an existing flight reservation and process refunds according to airline policy",
)
async def cancel_reservation(
    reservation_id: Annotated[str, Field(description="Reservation ID to cancel")],
    reason: Annotated[
        str,
        Field(
            description="Reason for cancellation (change_of_plan, airline_cancelled_flight, or other)"
        ),
    ] = "change_of_plan",
) -> str:
    """Cancel an existing reservation

    Args:
        reservation_id: Reservation ID to cancel
        reason: Reason for cancellation (change_of_plan, airline_cancelled_flight, or other)
    """
    try:
        logger.info(
            "Cancelling reservation ID: %s for reason: %s", reservation_id, reason
        )
        result = db.cancel_reservation(reservation_id, reason)
        logger.info(
            "Reservation cancelled successfully with ID: %s", result["reservation_id"]
        )
        return success_response(
            reservation_id=result["reservation_id"],
            status=result["status"],
            refund_amount=result.get("refund_amount", 0),
            refund_method=result.get("refund_method", ""),
            processing_time=result.get("processing_time", ""),
        )
    except Exception as e:
        return error_response(e)


@app.tool(
    name="update_reservation_passengers",
    description="Update passenger information for an existing reservation",
)
async def update_reservation_passengers(
    reservation_id: Annotated[str, Field(description="Reservation ID to update")],
    passengers: Annotated[
        List[PassengerInfo],
        Field(description="Updated passenger information for the reservation"),
    ],
) -> str:
    """Update passenger information for a reservation

    Args:
        reservation_id: Reservation ID to update
        passengers: List of PassengerInfo objects with updated passenger information
    """
    try:
        logger.info("Updating passengers for reservation ID: %s", reservation_id)
        result = db.update_reservation_passengers(
            reservation_id, [passenger.model_dump() for passenger in passengers]
        )
        logger.info(
            "Passengers updated successfully for reservation ID: %s",
            result["reservation_id"],
        )
        return success_response(
            reservation_id=result["reservation_id"],
            passengers=result["passengers"],
            status=result["status"],
        )
    except Exception as e:
        return error_response(e)


@app.tool(
    name="update_reservation_flights",
    description="Update flight details for an existing reservation including cabin class and flight changes",
)
async def update_reservation_flights(
    reservation_id: Annotated[str, Field(description="Reservation ID to update")],
    cabin: Annotated[
        str, Field(description="Updated cabin class (basic_economy, economy, business)")
    ],
    flights: Annotated[
        List[FlightDetail],
        Field(description="Updated flight information for the reservation"),
    ],
    payment_id: Annotated[
        str, Field(description="Payment method ID for handling any price differences")
    ],
) -> str:
    """Update flight details for a reservation

    Args:
        reservation_id: Reservation ID to update
        cabin: Updated cabin class (basic_economy, economy, business)
        flights: List of FlightDetail objects with updated flight information
        payment_id: Payment method ID for handling any price differences
    """
    try:
        logger.info(
            "Updating flights for reservation ID: %s with cabin: %s and payment ID: %s",
            reservation_id,
            cabin,
            payment_id,
        )
        result = db.update_reservation_flights(
            reservation_id,
            cabin,
            [flight.model_dump() for flight in flights],
            payment_id,
        )
        logger.info(
            "Flights updated successfully for reservation ID: %s",
            result["reservation_id"],
        )
        return success_response(
            reservation_id=result["reservation_id"],
            flights=result["flights"],
            cabin=result["cabin"],
            status=result["status"],
            price_difference=result.get("price_difference", 0),
        )
    except Exception as e:
        return error_response(e)


@app.tool(
    name="update_reservation_baggages",
    description="Update baggage information and fees for an existing reservation",
)
async def update_reservation_baggages(
    reservation_id: Annotated[str, Field(description="Reservation ID to update")],
    total_baggages: Annotated[int, Field(description="Total number of baggage items")],
    nonfree_baggages: Annotated[
        int, Field(description="Number of non-free baggage items that incur fees")
    ],
    payment_id: Annotated[str, Field(description="Payment method ID for baggage fees")],
) -> str:
    """Update baggage information for a reservation

    Args:
        reservation_id: Reservation ID
        total_baggages: Total number of baggage items
        nonfree_baggages: Number of non-free baggage items
        payment_id: Payment method ID for baggage fees
    """
    try:
        result = db.update_reservation_baggages(
            reservation_id, total_baggages, nonfree_baggages, payment_id
        )
        return success_response(
            reservation_id=result["reservation_id"],
            total_baggages=result["total_baggages"],
            nonfree_baggages=result["nonfree_baggages"],
            status=result["status"],
            baggage_fee=result.get("baggage_fee", 0),
        )
    except Exception as e:
        return error_response(e)


@app.tool(
    name="list_all_airports",
    description="List all available airports in the airline system",
)
async def list_all_airports() -> str:
    """List all available airports"""
    try:
        airports = db.list_all_airports()
        return success_response(airports=airports)
    except Exception as e:
        return error_response(e)


@app.tool(
    name="calculate",
    description="Perform basic mathematical calculations for pricing, totals, and other numeric operations",
)
async def calculate(
    expression: Annotated[
        str,
        Field(description="Mathematical expression to evaluate (e.g., '2 + 3 * 4')"),
    ],
) -> str:
    """Perform basic mathematical calculations

    Args:
        expression: Mathematical expression to evaluate (e.g., '2 + 3 * 4')
    """
    try:
        result = db.calculate(expression)
        return success_response(result=result)
    except Exception as e:
        return error_response(e)


@app.tool(
    name="send_certificate",
    description="Send a compensation certificate to a customer for flight issues or delays",
)
async def send_certificate(
    user_id: Annotated[str, Field(description="User ID to send certificate to")],
    reason: Annotated[
        str,
        Field(
            description="Reason for certificate (cancelled_flight, delayed_flight, or other)"
        ),
    ],
    reservation_id: Annotated[str, Field(description="Associated reservation ID")],
    amount: Annotated[
        float, Field(description="Certificate amount (auto-calculated if not provided)")
    ] = 0,
) -> str:
    """Send a certificate as compensation for flight issues

    Args:
        user_id: User ID to send certificate to
        reason: Reason for certificate (cancelled_flight, delayed_flight, or other)
        reservation_id: Associated reservation ID
        amount: Certificate amount (auto-calculated if not provided)
    """
    try:
        result = db.send_certificate(user_id, reason, reservation_id, amount)
        return success_response(
            certificate_id=result["certificate_id"],
            amount=result["amount"],
            reason=result["reason"],
            user_id=result["user_id"],
            status=result["status"],
        )
    except Exception as e:
        return error_response(e)


@app.tool(
    name="transfer_to_human_agents",
    description="Transfer the conversation to human agents for complex issues that cannot be resolved automatically",
)
async def transfer_to_human_agents(
    summary: Annotated[
        str, Field(description="Summary of the issue requiring human intervention")
    ],
) -> str:
    """Transfer the conversation to human agents

    Args:
        summary: Summary of the issue requiring human intervention
    """
    try:
        result = db.transfer_to_human_agents(summary)
        return success_response(
            transfer_id=result["transfer_id"],
            summary=result["summary"],
            status=result["status"],
        )
    except Exception as e:
        return error_response(e)


@app.tool(
    name="think",
    description="Internal reasoning tool for the agent to process information and plan actions",
)
async def think(
    thought: Annotated[str, Field(description="The agent's internal thought process")],
) -> str:
    """Internal thinking tool for reasoning

    Args:
        thought: The agent's internal thought process
    """
    try:
        result = db.think(thought)
        return success_response(thought=result["thought"], status=result["status"])
    except Exception as e:
        return error_response(e)


@app.tool(
    name="check_price_quote",
    description="Get a price quote for booking a new reservation or changing an existing one without making actual changes",
)
async def check_price_quote(
    user_id: Annotated[str, Field(description="User ID (e.g., 'john_doe_1234')")],
    origin: Annotated[str, Field(description="Origin airport code (e.g., 'JFK')")],
    destination: Annotated[
        str, Field(description="Destination airport code (e.g., 'LAX')")
    ],
    flight_type: Annotated[
        Literal["one_way", "round_trip"], Field(description="Type of flight")
    ],
    cabin: Annotated[
        Literal["basic_economy", "economy", "business"],
        Field(description="Cabin class"),
    ],
    flights: Annotated[
        List[FlightDetail], Field(description="List of flights to include in quote")
    ],
    passengers: Annotated[List[PassengerInfo], Field(description="List of passengers")],
    total_baggages: Annotated[
        int, Field(description="Total number of checked bags", ge=0)
    ] = 0,
    nonfree_baggages: Annotated[
        int, Field(description="Number of bags that incur fees", ge=0)
    ] = 0,
    insurance: Annotated[
        Literal["yes", "no"], Field(description="Travel insurance")
    ] = "no",
    reservation_id: Annotated[
        Optional[str], Field(description="Existing reservation ID for change quote")
    ] = None,
) -> str:
    """Get a price quote for booking or changing flights

    This tool provides pricing information without making any actual changes to the system.
    Use this to help customers understand costs before confirming bookings or changes.

    Args:
        user_id: User ID making the booking/change
        origin: Origin airport code
        destination: Destination airport code
        flight_type: Type of flight (one_way or round_trip)
        cabin: Cabin class (basic_economy, economy, or business)
        flights: List of flights to include in the quote
        passengers: List of passengers
        total_baggages: Total number of checked bags
        nonfree_baggages: Number of bags that incur fees
        insurance: Whether to include travel insurance
        reservation_id: If provided, calculates change costs from existing reservation
    """
    try:
        flights_data = [flight.model_dump() for flight in flights]
        passengers_data = [passenger.model_dump() for passenger in passengers]

        result = db.check_price_quote(
            user_id=user_id,
            origin=origin,
            destination=destination,
            flight_type=flight_type,
            cabin=cabin,
            flights=flights_data,
            passengers=passengers_data,
            total_baggages=total_baggages,
            nonfree_baggages=nonfree_baggages,
            insurance=insurance,
            reservation_id=reservation_id,
        )
        return success_response(**result)
    except Exception as e:
        return error_response(e)


@app.tool(
    name="configure_data",
    description="Configure the airline system data including flights, reservations, and users",
)
async def configure_data(
    data_config: Annotated[
        Dict[str, Any],
        Field(
            description="Complete data configuration with flights, reservations, and users"
        ),
    ],
) -> str:
    """Configure the airline data (flights, reservations, users)

    Args:
        data_config: Complete data configuration with flights, reservations, and users
    """
    try:
        result = db.configure_data(data_config)
        return success_response(status=result["status"])
    except Exception as e:
        return error_response(e)


@app.tool(
    name="check_refund_amount",
    description="Calculate the refund amount for a reservation if it were to be cancelled",
)
async def check_refund_amount(
    reservation_id: Annotated[
        str, Field(description="Reservation ID to check refund for")
    ],
    reason: Annotated[
        str,
        Field(
            description="Reason for potential cancellation (change_of_plan, airline_cancelled_flight, or other)"
        ),
    ],
) -> str:
    """Check potential refund amount for a reservation without actually cancelling it

    Args:
        reservation_id: Reservation ID to check refund for
        reason: Reason for potential cancellation (change_of_plan, airline_cancelled_flight, or other)
    """
    try:
        result = db.check_refund_amount(reservation_id, reason)

        logger.info(
            "Refund check completed for reservation %s: $%.2f",
            reservation_id,
            result["refund_amount"],
        )

        return success_response(**result)
    except Exception as e:
        return error_response(e)


if __name__ == "__main__":
    app.run(transport="stdio")
