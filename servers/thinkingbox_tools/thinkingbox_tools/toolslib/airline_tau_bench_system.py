# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

"""airline_system.py - business-logic engine for Airline Tau-Bench.

This module depends **only** on the Pydantic models & enums defined in
`airline_models.py`.  Every public method signature matches the original
monolithic code so external callers (MCP server) remain unaffected.
"""

###############################################################################
# 0. Imports - stdlib first, then third-party, then project
###############################################################################

import logging
import uuid
from collections import Counter
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)


class CabinClass(str, Enum):
    BASIC_ECONOMY = "basic_economy"
    ECONOMY = "economy"
    BUSINESS = "business"


class FlightType(str, Enum):
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"


class ReservationStatus(str, Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class MembershipTier(str, Enum):
    REGULAR = "regular"
    SILVER = "silver"
    GOLD = "gold"


class PaymentSource(str, Enum):
    CREDIT_CARD = "credit_card"
    GIFT_CARD = "gift_card"
    CERTIFICATE = "certificate"


class FlightStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    LANDED = "landed"
    CANCELLED = "cancelled"
    DELAYED = "delayed"
    FLYING = "flying"
    ON_TIME = "on time"


class CompensationReason(str, Enum):
    CANCELLED_FLIGHT = "cancelled_flight"
    DELAYED_FLIGHT = "delayed_flight"
    OTHER = "other"


# ─────────────────────────────── Core models ─────────────────────────────


class PriceInfo(BaseModel):
    basic_economy: float = Field(..., ge=0)
    economy: float = Field(..., ge=0)
    business: float = Field(..., ge=0)


class SeatAvailability(BaseModel):
    basic_economy: int = Field(..., ge=0)
    economy: int = Field(..., ge=0)
    business: int = Field(..., ge=0)


class FlightDateData(BaseModel):
    status: FlightStatus
    prices: Optional[PriceInfo] = None
    available_seats: Optional[SeatAvailability] = None

    @model_validator(mode="after")
    def _require_prices_if_available(self):
        if self.status == FlightStatus.AVAILABLE:
            if self.prices is None or self.available_seats is None:
                raise ValueError(
                    "prices and available_seats must be provided when status == 'available'"
                )
        return self


class FlightInfo(BaseModel):
    flight_number: str = Field(..., min_length=1)
    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    scheduled_departure_time: str = Field(..., pattern=r"^\d{2}:\d{2}:\d{2}$")
    scheduled_arrival_time: str = Field(..., pattern=r"^\d{2}:\d{2}:\d{2}(?:\+\d+)?$")
    dates: Dict[str, FlightDateData]

    @field_validator("origin", "destination")
    @classmethod
    def _uppercase(cls, v: str) -> str:
        if not v.isupper():
            raise ValueError("Airport codes must be uppercase (e.g. LAX)")
        return v


class PaymentMethod(BaseModel):
    source: PaymentSource
    amount: Optional[float] = Field(
        default=None,
        ge=0,
        description="Balance for gift cards & certificates; unused for credit cards",
    )
    id: str
    brand: Optional[str] = None  # only for credit cards
    last_four: Optional[str] = None  # …
    reason: Optional[str] = None  # certificate bookkeeping
    issued_at: Optional[str] = None
    reservation_id: Optional[str] = None

    # ----------------------  conditional rule  -------------------------
    @model_validator(mode="after")
    def _check_amount_for_prepaid(self):
        if self.source in {PaymentSource.GIFT_CARD, PaymentSource.CERTIFICATE}:
            if self.amount is None:
                raise ValueError("amount is required for gift cards and certificates")
        else:  # credit card
            if self.amount is not None:
                raise ValueError("credit cards should not specify amount")
        return self


class Passenger(BaseModel):
    first_name: str
    last_name: str
    dob: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")


class User(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    address: str
    date_of_birth: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    membership_level: MembershipTier = MembershipTier.REGULAR
    payment_methods: Dict[str, PaymentMethod] = Field(default_factory=dict)
    reservations: List[str] = Field(default_factory=list)
    saved_passengers: List[Passenger] = Field(default_factory=list)


class ProcessedFlight(BaseModel):
    flight_number: str
    date: str
    origin: str
    destination: str
    # scheduled_departure_time: str
    # scheduled_arrival_time: str
    price: float
    status: Optional[str] = None


class PaymentHistoryItem(BaseModel):
    payment_id: str
    amount: float


class Reservation(BaseModel):
    reservation_id: str
    user_id: str
    origin: str
    destination: str
    flight_type: FlightType
    cabin: CabinClass
    flights: List[ProcessedFlight]
    passengers: List[Passenger]
    payment_history: List[PaymentHistoryItem]
    created_at: str
    total_baggages: int
    nonfree_baggages: int
    insurance: str  # "yes" | "no"
    total_price: float | None = None
    status: ReservationStatus = ReservationStatus.CONFIRMED
    last_modified: Optional[str] = None
    cancelled_at: Optional[str] = None
    cancellation_reason: Optional[str] = None


class FlightSearchResult(BaseModel):
    flight_number: str
    origin: str
    destination: str
    scheduled_departure_time: str
    scheduled_arrival_time: str
    date: str
    status: str
    prices: PriceInfo
    available_seats: SeatAvailability


class OneStopFlightResult(BaseModel):
    type: str = "one_stop"
    connecting_airport: str
    first_flight: FlightSearchResult
    second_flight: FlightSearchResult


# ─────────────────────────────── Request DTOs ─────────────────────────────
class BookingRequest(BaseModel):
    user_id: str
    origin: str
    destination: str
    flight_type: FlightType
    cabin: CabinClass
    flights: List[Dict[str, str]]
    passengers: List[Passenger]
    payment_methods: List[Dict[str, Union[str, float]]]
    total_baggages: int = 0
    nonfree_baggages: int = 0
    insurance: str = Field("no", pattern=r"^(yes|no)$")

    @field_validator("payment_methods")
    @classmethod
    def _non_empty(cls, v):
        if not v:
            raise ValueError("At least one payment method required")
        return v


class FlightUpdateRequest(BaseModel):
    reservation_id: str
    cabin: CabinClass
    flights: List[Dict[str, str]]
    payment_id: str


class PassengerUpdateRequest(BaseModel):
    reservation_id: str
    passengers: List[Passenger]


class BaggageUpdateRequest(BaseModel):
    reservation_id: str
    total_baggages: int
    nonfree_baggages: int
    payment_id: str


class CertificateRequest(BaseModel):
    user_id: str
    reason: CompensationReason
    reservation_id: str
    amount: float


class TransferRequest(BaseModel):
    summary: str


class CalculationRequest(BaseModel):
    expression: str

    @field_validator("expression")
    @classmethod
    def _safe_chars(cls, v):
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in v):
            raise ValueError("Invalid characters in expression")
        return v


class DataConfiguration(BaseModel):
    flights: Dict[str, FlightInfo] = Field(default_factory=dict)
    reservations: Dict[str, Reservation] = Field(default_factory=dict)
    users: Dict[str, User] = Field(default_factory=dict)


###############################################################################
# 1. Business constants (duplicated here so system is self-contained)
###############################################################################

BAGGAGE_FEE = 50  # USD per extra checked bag
INSURANCE_FEE = 30  # USD per passenger

FREE_BAGS = {
    (MembershipTier.REGULAR, CabinClass.BASIC_ECONOMY): 0,
    (MembershipTier.REGULAR, CabinClass.ECONOMY): 1,
    (MembershipTier.REGULAR, CabinClass.BUSINESS): 2,
    (MembershipTier.SILVER, CabinClass.BASIC_ECONOMY): 1,
    (MembershipTier.SILVER, CabinClass.ECONOMY): 2,
    (MembershipTier.SILVER, CabinClass.BUSINESS): 3,
    (MembershipTier.GOLD, CabinClass.BASIC_ECONOMY): 2,
    (MembershipTier.GOLD, CabinClass.ECONOMY): 3,
    (MembershipTier.GOLD, CabinClass.BUSINESS): 3,
}

MAX_PASSENGERS = 5
MAX_GIFT_CARDS = 3
MAX_CERTIFICATES = 1
MAX_CREDIT_CARDS = 1

###############################################################################
# 2. Custom error - name preserved from legacy code
###############################################################################


class AirlineTauBenchSystemError(Exception):
    """Raised when a rule is violated or entity not found."""


###############################################################################
# 3. AirlineTauBenchSystem - public API identical to original
###############################################################################

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Set to DEBUG for detailed output


class AirlineTauBenchSystem:  # noqa: WPS110
    """Stateless business engine (no external DB)."""

    # ───────────────────────────────── Construction ─────────────────────────
    def __init__(self) -> None:
        self.flights: Dict[str, FlightInfo] = {}
        self.reservations: Dict[str, Reservation] = {}
        self.users: Dict[str, User] = {}

    # ────────────────────────────────── Search ──────────────────────────────
    def search_direct_flight(
        self, origin: str, destination: str, date: str
    ) -> List[FlightSearchResult]:
        """Return all direct flights for given OD & date."""

        return [
            self._to_search_result(f, date)
            for f in self.flights.values()
            if f.origin == origin
            and f.destination == destination
            and self._is_available(f, date)
        ]

    def search_onestop_flight(
        self, origin: str, destination: str, date: str
    ) -> List[OneStopFlightResult]:
        """Return all one-stop options (two segments, single connection)."""
        results: List[OneStopFlightResult] = []
        for first in self.flights.values():
            if first.origin != origin or not self._is_available(first, date):
                continue
            connector = first.destination
            for second in self.flights.values():
                if (
                    second.origin == connector
                    and second.destination == destination
                    and self._is_available(second, date)
                ):
                    results.append(
                        OneStopFlightResult(
                            connecting_airport=connector,
                            first_flight=self._to_search_result(first, date),
                            second_flight=self._to_search_result(second, date),
                        )
                    )
        return results

    # ──────────────────────────────── Getters ───────────────────────────────
    def get_user_details(self, user_id: str) -> User:  # noqa: D401
        """Return user profile or raise."""
        return self._get(self.users, user_id, "User")

    def get_reservation_details(self, reservation_id: str) -> Reservation:
        return self._get(self.reservations, reservation_id, "Reservation")

    # ───────────────────────────────── Booking ──────────────────────────────
    def book_reservation(
        self,
        user_id: str,
        origin: str,
        destination: str,
        flight_type: str,
        cabin: str,
        flights: List[Dict[str, Any]],
        passengers: List[Dict[str, Any]],
        payment_methods: List[Dict[str, Any]],
        total_baggages: int = 0,
        nonfree_baggages: int = 0,
        insurance: str = "no",
    ) -> Dict[str, Any]:
        """High-level booking façade - thin wrapper around helpers."""
        try:
            req = BookingRequest(
                user_id=user_id,
                origin=origin,
                destination=destination,
                flight_type=FlightType(flight_type),
                cabin=CabinClass(cabin),
                flights=flights,
                passengers=[Passenger(**p) for p in passengers],
                payment_methods=payment_methods,
                total_baggages=total_baggages,
                nonfree_baggages=nonfree_baggages,
                insurance=insurance,
            )
        except ValidationError as exc:  # convert to legacy error
            raise AirlineTauBenchSystemError(exc.errors()) from exc

        user = self.get_user_details(req.user_id)
        self._validate_pax(req.passengers)
        self._validate_payment_limits(req.payment_methods, user)

        segments, base_price = self._make_segments(req)
        price = base_price + self._insurance_cost(req) + self._baggage_cost(req, user)

        self._verify_payments(req.payment_methods, price)
        self._apply_payments(user, req.payment_methods)

        res_id = self._new_id("RES")
        reservation = Reservation(
            reservation_id=res_id,
            user_id=user.user_id,
            origin=req.origin,
            destination=req.destination,
            flight_type=req.flight_type,
            cabin=req.cabin,
            flights=segments,
            passengers=req.passengers,
            payment_history=[PaymentHistoryItem(**pm) for pm in req.payment_methods],
            created_at=self._now(),
            total_baggages=req.total_baggages,
            nonfree_baggages=req.nonfree_baggages,
            insurance=req.insurance,
            total_price=price,
        )
        self.reservations[res_id] = reservation
        user.reservations.append(res_id)

        return {"reservation_id": res_id, "total_price": price, "status": "confirmed"}

    # ─────────────────────────────── Cancellation ───────────────────────────
    def cancel_reservation(self, reservation_id: str, reason: str) -> Dict[str, Any]:
        res = self.get_reservation_details(reservation_id)
        if res.status == ReservationStatus.CANCELLED:
            raise AirlineTauBenchSystemError("Reservation already cancelled")

        refund = self._refund_amount(res, reason)

        # cannot cancel if partially flown. but
        # seems like we should let the agent do it and fail the test

        # restore seats
        for seg in res.flights:
            date_info = self.flights[seg.flight_number].dates[seg.date]
            # Only restore seats if available_seats is not None
            # (it can be None when flight status is not AVAILABLE)
            if date_info.available_seats is not None:
                cabin_attr = res.cabin.value
                current = getattr(date_info.available_seats, cabin_attr)
                setattr(
                    date_info.available_seats, cabin_attr, current + len(res.passengers)
                )

        res.status = ReservationStatus.CANCELLED
        res.cancelled_at = self._now()
        res.cancellation_reason = reason

        return {
            "reservation_id": reservation_id,
            "status": "cancelled",
            "refund_amount": refund,
            "refund_method": "original_payment_methods",
            "processing_time": "5-7 business days",
        }

    def check_refund_amount(
        self, reservation_id: str, reason: str = "change_of_plan"
    ) -> Dict[str, Any]:
        """Calculate the refund amount for a reservation without actually cancelling it

        Args:
            reservation_id: Reservation ID to check refund for
            reason: Reason for potential cancellation (change_of_plan, airline_cancelled_flight, or other)

        Returns:
            Dictionary containing refund information including amount, eligibility message, and reservation details
        """
        res = self.get_reservation_details(reservation_id)

        # Calculate refund amount using the internal method
        refund_amount = self._refund_amount(res, reason)

        # Determine refund eligibility message
        eligibility_message = ""
        if refund_amount == 0:
            if res.cabin == CabinClass.BASIC_ECONOMY and res.insurance == "no":
                eligibility_message = "No refund available for basic economy without insurance unless cancelled within 24 hours or airline cancellation"
            elif res.cabin == CabinClass.ECONOMY and res.insurance == "no":
                eligibility_message = "No refund available for economy without insurance unless cancelled within 24 hours or airline cancellation"
            else:
                eligibility_message = (
                    "No refund available for this reservation under current conditions"
                )
        elif refund_amount < (res.total_price or 0):
            eligibility_message = "Partial refund available for business class cancellation (80% of total price)"
        else:
            eligibility_message = "Full refund available"

        return {
            "reservation_id": reservation_id,
            "total_price": res.total_price or 0,
            "refund_amount": refund_amount,
            "refund_method": (
                "original_payment_methods" if refund_amount > 0 else "none"
            ),
            "eligibility_message": eligibility_message,
            "reason_checked": reason,
            "cabin_class": res.cabin.value,
            "insurance": res.insurance,
        }

    # ─────────────────────────── Update – passengers ────────────────────────
    def update_reservation_passengers(
        self, reservation_id: str, passengers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        res = self.get_reservation_details(reservation_id)
        if res.cabin == CabinClass.BASIC_ECONOMY:
            raise AirlineTauBenchSystemError("Basic economy tickets cannot be modified")
        if len(res.passengers) != len(passengers):
            raise AirlineTauBenchSystemError("Cannot change the number of passengers")
        pax = [Passenger(**p) for p in passengers]
        self._validate_pax(pax)
        res.passengers = pax
        res.last_modified = self._now()
        return {
            "reservation_id": reservation_id,
            "passengers": [p.model_dump() for p in pax],
            "status": "updated",
        }

    # ─────────────────────────── Update - flights ───────────────────────────
    def update_reservation_flights(
        self,
        reservation_id: str,
        cabin: str,
        flights: List[Dict[str, Any]],
        payment_id: str,
    ) -> Dict[str, Any]:
        res = self.get_reservation_details(reservation_id)
        if res.cabin == CabinClass.BASIC_ECONOMY and cabin == CabinClass.BASIC_ECONOMY:
            raise AirlineTauBenchSystemError(
                "Basic economy flights cannot be modified. Consider cabin upgrade first."
            )
        user = self.get_user_details(res.user_id)
        if payment_id not in user.payment_methods:
            raise AirlineTauBenchSystemError("Payment method not found in user profile")

        new_cabin = CabinClass(cabin)
        temp_req = BookingRequest(
            user_id=res.user_id,
            origin=res.origin,
            destination=res.destination,
            flight_type=res.flight_type,
            cabin=new_cabin,
            flights=flights,
            passengers=res.passengers,
            payment_methods=[{"payment_id": payment_id, "amount": 0.0}],  # placeholder
            total_baggages=res.total_baggages,
            nonfree_baggages=res.nonfree_baggages,
            insurance=res.insurance,
        )
        segs, new_base = self._make_segments(temp_req)
        new_price = (
            new_base
            + self._insurance_cost(temp_req)
            + self._baggage_cost(temp_req, user)
        )
        # Handle case where total_price might still be None for legacy data
        current_price = res.total_price if res.total_price is not None else 0.0
        diff = new_price - current_price
        if diff > 0:
            self._apply_payments(user, [{"payment_id": payment_id, "amount": diff}])
        res.cabin = new_cabin
        res.flights = segs
        res.total_price = new_price
        res.last_modified = self._now()
        return {
            "reservation_id": reservation_id,
            "flights": [s.model_dump() for s in segs],
            "cabin": new_cabin.value,
            "status": "updated",
            "price_difference": diff,
        }

    # ─────────────────────────── Update - baggage ───────────────────────────
    def update_reservation_baggages(
        self,
        reservation_id: str,
        total_baggages: int,
        nonfree_baggages: int,
        payment_id: str,
    ) -> Dict[str, Any]:
        res = self.get_reservation_details(reservation_id)
        if total_baggages < res.total_baggages:
            raise AirlineTauBenchSystemError(
                "Cannot remove checked bags - only additions allowed"
            )
        user = self.get_user_details(res.user_id)
        if payment_id not in user.payment_methods:
            raise AirlineTauBenchSystemError("Payment method not found")
        old_fee = BAGGAGE_FEE * res.nonfree_baggages
        new_fee = BAGGAGE_FEE * nonfree_baggages
        diff = new_fee - old_fee
        if diff > 0:
            self._apply_payments(user, [{"payment_id": payment_id, "amount": diff}])
        res.total_baggages = total_baggages
        res.nonfree_baggages = nonfree_baggages
        # Handle case where total_price might be None for legacy data
        if res.total_price is None:
            res.total_price = 0.0
        res.total_price += diff
        res.last_modified = self._now()
        return {
            "reservation_id": reservation_id,
            "total_baggages": total_baggages,
            "nonfree_baggages": nonfree_baggages,
            "status": "updated",
            "baggage_fee": diff,
        }

    # ───────────────────────────── Misc utilities ───────────────────────────
    def list_all_airports(self) -> List[str]:
        """Return a sorted list of all airport IATA codes in the system.

        Handles both fully-converted `FlightInfo` objects **and** raw dicts, so
        the method is robust even if the caller inserted flights manually
        before running `configure_data`.
        """
        logger.info("Listing all airports in the system")
        airports: set[str] = set()
        logger.info(f"Length of flights: {len(self.flights)}")
        for flight in self.flights.values():
            # Accept either model instances or plain dictionaries
            if isinstance(flight, dict):  # raw dict not yet converted
                logger.info(f"Processing raw flight data: {flight}")
                airports.update({flight.get("origin"), flight.get("destination")})
                logger.info(f"Current airports set: {airports}")
            else:  # FlightInfo
                logger.info(f"Processing FlightInfo object: {flight}")
                airports.update({flight.origin, flight.destination})
                logger.info(f"Current airports set: {airports}")
        # Filter out any Nones/empty strings, then sort
        return sorted(a for a in airports if a)

    def calculate(self, expression: str) -> float:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            raise AirlineTauBenchSystemError("Invalid characters in expression")
        return float(eval(expression))  # noqa: WPS421 - safe after validation

    def send_certificate(
        self, user_id: str, reason: str, reservation_id: str, amount: float
    ) -> Dict[str, Any]:
        user = self.get_user_details(user_id)
        res = self.get_reservation_details(reservation_id)
        eligible = (
            user.membership_level in {MembershipTier.SILVER, MembershipTier.GOLD}
            or res.insurance == "yes"
            or res.cabin == CabinClass.BUSINESS
        )
        if not eligible:
            raise AirlineTauBenchSystemError("User not eligible for compensation")
        if reason == "cancelled_flight":
            amount = 100 * len(res.passengers)
        elif reason == "delayed_flight":
            amount = 50 * len(res.passengers)
        cert_id = self._new_id("CERT")
        user.payment_methods[cert_id] = PaymentMethod(
            source=PaymentSource.CERTIFICATE,
            amount=amount,
            id=cert_id,
            reason=reason,
            issued_at=self._now(),
            reservation_id=reservation_id,
        )
        return {
            "certificate_id": cert_id,
            "amount": amount,
            "reason": reason,
            "user_id": user_id,
            "status": "issued",
        }

    def add_insurance_to_reservation(self, reservation_id: str) -> Dict[str, Any]:
        raise AirlineTauBenchSystemError(
            "Cannot add insurance after initial booking. Purchase must occur during booking."
        )

    def transfer_to_human_agents(self, summary: str) -> Dict[str, Any]:
        return {
            "transfer_id": self._new_id("TSF"),
            "summary": summary,
            "status": "transferred",
            "timestamp": self._now(),
        }

    def think(self, thought: str) -> Dict[str, Any]:
        return {"thought": thought, "status": "recorded", "timestamp": self._now()}

    def check_price_quote(
        self,
        user_id: str,
        origin: str,
        destination: str,
        flight_type: str,
        cabin: str,
        flights: List[Dict[str, Any]],
        passengers: List[Dict[str, Any]],
        total_baggages: int = 0,
        nonfree_baggages: int = 0,
        insurance: str = "no",
        reservation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a price quote for booking a new reservation or changing an existing one.

        This method calculates pricing without making any actual changes to the system.

        Args:
            user_id: The user making the booking/change
            origin: Origin airport code
            destination: Destination airport code
            flight_type: "one_way" or "round_trip"
            cabin: "basic_economy", "economy", or "business"
            flights: List of flight details with flight_number and date
            passengers: List of passenger details
            total_baggages: Total number of bags
            nonfree_baggages: Number of bags that incur fees
            insurance: "yes" or "no"
            reservation_id: If provided, calculates change fee from existing reservation

        Returns:
            Dict with price breakdown and total cost
        """
        try:
            # Validate input parameters
            req = BookingRequest(
                user_id=user_id,
                origin=origin,
                destination=destination,
                flight_type=FlightType(flight_type),
                cabin=CabinClass(cabin),
                flights=flights,
                passengers=[Passenger(**p) for p in passengers],
                payment_methods=[{"payment_id": "dummy", "amount": 0}],  # dummy payment
                total_baggages=total_baggages,
                nonfree_baggages=nonfree_baggages,
                insurance=insurance,
            )
        except ValidationError as exc:
            raise AirlineTauBenchSystemError(
                f"Invalid booking parameters: {exc}"
            ) from exc

        user = self.get_user_details(req.user_id)
        self._validate_pax(req.passengers)

        # Calculate flight base price without reserving seats
        flight_price = 0.0
        flight_details = []

        for item in req.flights:
            num, date = item["flight_number"], item["date"]
            flight = self._get(self.flights, num, "Flight")
            if date not in flight.dates:
                raise AirlineTauBenchSystemError(
                    f"Flight {num} not available on {date}"
                )

            sched = flight.dates[date]
            if sched.status != FlightStatus.AVAILABLE:
                raise AirlineTauBenchSystemError(f"Flight {num} unavailable on {date}")

            cabin_attr = req.cabin.value
            seats_left = getattr(sched.available_seats, cabin_attr)
            if seats_left < len(req.passengers):
                raise AirlineTauBenchSystemError(
                    f"Not enough {cabin_attr} seats on {num} {date}"
                )

            price_pp = getattr(sched.prices, cabin_attr)
            segment_total = price_pp * len(req.passengers)
            flight_price += segment_total

            flight_details.append(
                {
                    "flight_number": num,
                    "date": date,
                    "origin": flight.origin,
                    "destination": flight.destination,
                    "price_per_person": price_pp,
                    "segment_total": segment_total,
                }
            )

        # Calculate additional costs
        insurance_cost = self._insurance_cost(req)
        baggage_cost = self._baggage_cost(req, user)
        total_price = flight_price + insurance_cost + baggage_cost

        # If this is a change request, calculate the difference
        price_difference = 0.0
        current_price = 0.0
        if reservation_id:
            try:
                existing_res = self.get_reservation_details(reservation_id)
                current_price = (
                    existing_res.total_price if existing_res.total_price else 0.0
                )
                price_difference = total_price - current_price
            except AirlineTauBenchSystemError:
                # If reservation doesn't exist, treat as new booking
                reservation_id = None
                price_difference = total_price

        return {
            "quote_type": "change" if reservation_id else "new_booking",
            "reservation_id": reservation_id,
            "flight_details": flight_details,
            "pricing_breakdown": {
                "base_flight_price": flight_price,
                "insurance_cost": insurance_cost,
                "baggage_cost": baggage_cost,
                "total_price": total_price,
            },
            "change_details": (
                {
                    "current_price": current_price,
                    "new_price": total_price,
                    "price_difference": price_difference,
                    "additional_payment_required": max(0, price_difference),
                    "refund_amount": max(0, -price_difference),
                }
                if reservation_id
                else None
            ),
            "passenger_count": len(req.passengers),
            "cabin_class": req.cabin.value,
            "flight_type": req.flight_type.value,
            "insurance_included": req.insurance == "yes",
            "total_baggages": req.total_baggages,
            "timestamp": self._now(),
        }

    # ─────────────────────────── Data configuration ─────────────────────────
    def configure_data(self, data_config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.flights = {
                fid: self._convert_flight_data(fd)
                for fid, fd in data_config.get("flights", {}).items()
            }
        except Exception as exc:  # noqa: BLE001 - re-raise as domain error
            logging.error(f"Validation error during flight conversion: {exc}")
            raise AirlineTauBenchSystemError(f"Invalid flight data: {exc}") from exc

        try:
            self.reservations = {
                rid: self._convert_reservation_data(rd)
                for rid, rd in data_config.get("reservations", {}).items()
            }
        except Exception as exc:  # noqa: BLE001 - re-raise as domain error
            logging.error(f"Validation error during reservation conversion: {exc}")
            raise AirlineTauBenchSystemError(
                f"Invalid reservation data: {exc}"
            ) from exc
        try:
            self.users = {
                uid: self._convert_user_data(uid, ud)
                for uid, ud in data_config.get("users", {}).items()
            }
        except Exception as exc:
            logging.info(f"Validation error during user conversion: {exc}")
            raise AirlineTauBenchSystemError(f"Invalid user data: {exc}") from exc
        return {"status": "configured"}

    def get_current_data(self) -> DataConfiguration:
        return DataConfiguration(
            flights=self.flights, reservations=self.reservations, users=self.users
        )

    # ──────────────────────────── Helper methods ────────────────────────────
    # Generic
    @staticmethod
    def _now() -> str:
        # Fixed datetime: 2024-05-15 15:00:00 EST (UTC-5)
        from datetime import timedelta

        est = timezone(timedelta(hours=-5))
        fixed_time = datetime(2024, 5, 15, 15, 0, 0, tzinfo=est)
        return fixed_time.isoformat()

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def _get(mapping: Dict[str, Any], key: str, label: str):  # noqa: ANN401 - flexible
        logger.info(f"Fetching {label} with key: {key}")
        try:
            logger.info(f"Current mapping state: {mapping}")
            return mapping[key]
        except KeyError as exc:
            logger.info(f"{label} {key} not found")
            raise AirlineTauBenchSystemError(f"{label} {key} not found") from exc

    # Availability helpers
    def _is_available(self, flight: FlightInfo, date: str) -> bool:
        return (
            date in flight.dates and flight.dates[date].status == FlightStatus.AVAILABLE
        )

    @staticmethod
    def _to_search_result(f: FlightInfo, date: str) -> FlightSearchResult:
        d = f.dates[date]
        return FlightSearchResult(
            flight_number=f.flight_number,
            origin=f.origin,
            destination=f.destination,
            scheduled_departure_time=f.scheduled_departure_time,
            scheduled_arrival_time=f.scheduled_arrival_time,
            date=date,
            status=d.status.value,
            prices=d.prices,
            available_seats=d.available_seats,
        )

    # Validation helpers
    @staticmethod
    def _validate_pax(pax: List[Passenger]):
        if not (1 <= len(pax) <= MAX_PASSENGERS):
            raise AirlineTauBenchSystemError(
                f"Passengers must be between 1 and {MAX_PASSENGERS}"
            )

    def _validate_payment_limits(
        self, payments: List[Dict[str, Union[str, float]]], user: User
    ):
        counts = Counter()
        for pm in payments:
            pid = pm["payment_id"]
            if pid not in user.payment_methods:
                raise AirlineTauBenchSystemError(
                    f"Payment method {pid} not on user profile"
                )
            counts[user.payment_methods[pid].source] += 1
        if counts[PaymentSource.GIFT_CARD] > MAX_GIFT_CARDS:
            raise AirlineTauBenchSystemError("Max 3 gift cards allowed")
        if counts[PaymentSource.CERTIFICATE] > MAX_CERTIFICATES:
            raise AirlineTauBenchSystemError("Max 1 certificate allowed")
        if counts[PaymentSource.CREDIT_CARD] > MAX_CREDIT_CARDS:
            raise AirlineTauBenchSystemError("Max 1 credit card allowed")

    # Segment builder
    def _make_segments(
        self, req: BookingRequest
    ) -> Tuple[List[ProcessedFlight], float]:
        segs: List[ProcessedFlight] = []
        total = 0.0
        for item in req.flights:
            num, date = item["flight_number"], item["date"]
            flight = self._get(self.flights, num, "Flight")
            if date not in flight.dates:
                raise AirlineTauBenchSystemError(
                    f"Flight {num} not available on {date}"
                )
            sched = flight.dates[date]
            if sched.status != FlightStatus.AVAILABLE:
                raise AirlineTauBenchSystemError(f"Flight {num} unavailable on {date}")
            cabin_attr = req.cabin.value
            seats_left = getattr(sched.available_seats, cabin_attr)
            if seats_left < len(req.passengers):
                raise AirlineTauBenchSystemError(
                    f"Not enough {cabin_attr} seats on {num} {date}"
                )
            price_pp = getattr(sched.prices, cabin_attr)
            total += price_pp * len(req.passengers)
            # reserve seats
            setattr(sched.available_seats, cabin_attr, seats_left - len(req.passengers))
            segs.append(
                ProcessedFlight(
                    flight_number=num,
                    date=date,
                    origin=flight.origin,
                    destination=flight.destination,
                    scheduled_departure_time=flight.scheduled_departure_time,
                    scheduled_arrival_time=flight.scheduled_arrival_time,
                    price=price_pp,
                )
            )
        return segs, total

    @staticmethod
    def _insurance_cost(req: BookingRequest) -> int:
        return INSURANCE_FEE * len(req.passengers) if req.insurance == "yes" else 0

    def _baggage_cost(self, req: BookingRequest, user: User) -> int:
        free = FREE_BAGS[(user.membership_level, req.cabin)] * len(req.passengers)
        extra = max(0, req.total_baggages - free)
        return BAGGAGE_FEE * extra

    @staticmethod
    def _verify_payments(payments: List[Dict[str, Union[str, float]]], expected: float):
        paid = sum(p["amount"] for p in payments)
        if abs(paid - expected) > 1e-2:
            raise AirlineTauBenchSystemError(
                f"Payment total {paid} does not match expected {expected}"
            )

    def _apply_payments(self, user: User, payments: List[Dict[str, Union[str, float]]]):
        for pm in payments:
            pid, amt = pm["payment_id"], pm["amount"]
            method = user.payment_methods[pid]
            if method.source in {PaymentSource.GIFT_CARD, PaymentSource.CERTIFICATE}:
                if method.amount < amt:
                    raise AirlineTauBenchSystemError(f"Insufficient balance in {pid}")
                method.amount -= amt
                if method.source == PaymentSource.CERTIFICATE and method.amount == 0:
                    del user.payment_methods[pid]

    # Refunds
    def _refund_amount(self, res: Reservation, reason: str) -> float:
        created_datetime = datetime.fromisoformat(res.created_at)
        # Ensure the parsed datetime is timezone-aware
        if created_datetime.tzinfo is None:
            created_datetime = created_datetime.replace(tzinfo=timezone.utc)
        within24 = (
            datetime.now(timezone.utc) - created_datetime
        ).total_seconds() < 86_400

        # Handle case where total_price might be None for legacy data
        total_price = res.total_price if res.total_price is not None else 0.0

        if within24 or reason == "airline_cancelled_flight":
            return total_price
        if res.cabin == CabinClass.BUSINESS:
            return total_price * 0.8
        if (
            res.cabin in {CabinClass.ECONOMY, CabinClass.BASIC_ECONOMY}
            and res.insurance == "yes"
        ):
            return total_price
        return 0

    def _convert_flight_data(self, data: dict) -> FlightInfo:
        if not isinstance(data, dict):
            raise TypeError(f"Invalid flight data type: {type(data)}")

        return FlightInfo(
            flight_number=data["flight_number"],
            origin=data["origin"],
            destination=data["destination"],
            scheduled_departure_time=data["scheduled_departure_time_est"],
            scheduled_arrival_time=data["scheduled_arrival_time_est"],
            dates=data.get("dates"),
        )

    def _convert_reservation_data(self, data: dict) -> Reservation:
        if not isinstance(data, dict):
            raise TypeError(f"Invalid reservation data type: {type(data)}")
        reservation = Reservation(**data)
        if reservation.total_price is None and reservation.flights:
            reservation.total_price = sum(
                flight.price for flight in reservation.flights
            )
            reservation.total_price *= len(reservation.passengers)
        return reservation

    def _convert_user_data(self, uid: str, data: dict) -> User:
        if not isinstance(data, dict):
            raise TypeError(f"Invalid user data type: {type(data)}")
        a = data["address"]
        address = (
            f"{a['address1']}, {a['address2']}, {a['city']}, {a['state']} {a['zip']}"
        )
        return User(
            user_id=uid,
            first_name=data["name"]["first_name"],
            last_name=data["name"]["last_name"],
            email=data["email"],
            phone="+1-555-0123",  # Why did we add this ???
            address=address,
            date_of_birth=data["dob"],
            membership_level=data["membership"],
            payment_methods=data["payment_methods"],
            reservations=data["reservations"],
            saved_passengers=data["saved_passengers"],
        )
