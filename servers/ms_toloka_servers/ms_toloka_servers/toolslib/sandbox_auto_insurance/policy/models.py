# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Policy Administration."""

from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, Field


class PolicyStatus(str, Enum):
    """Policy status values."""

    ACTIVE = "Active"
    IN_GRACE_PERIOD = "In Grace Period"
    PENDING_CANCELLATION = "Pending Cancellation"
    CANCELLED_FOR_NON_PAYMENT = "Cancelled for Non-Payment"
    LAPSED = "Lapsed"
    NON_RENEWED = "Non-Renewed"


class CancellationReason(str, Enum):
    """Cancellation reason values."""

    USER_REQUESTED = "User Requested"
    NON_PAYMENT = "Non-Payment"
    UNDERWRITING = "Underwriting"
    FRAUD = "Fraud"


class State(str, Enum):
    """State values."""

    CA = "CA"
    TX = "TX"
    NY = "NY"
    FL = "FL"


class DriverStatus(str, Enum):
    """Driver status values."""

    RATED = "Rated"
    EXCLUDED = "Excluded"
    REMOVED = "Removed"


class VehicleStatus(str, Enum):
    """Vehicle status values."""

    ACTIVE = "Active"
    REMOVED = "Removed"


class Policy(BaseModel):
    """Auto insurance policy model."""

    table_name: ClassVar[str] = "policies"

    id: str = Field(
        ..., description="Unique identifier for the policy (POL-##########)"
    )
    customer_id: str = Field(..., description="The customer who owns this policy")
    state: State = Field(..., description="State where policy is issued")
    status: PolicyStatus = Field(
        default=PolicyStatus.ACTIVE, description="Current policy status"
    )
    effective_date: str = Field(..., description="Policy effective date (YYYY-MM-DD)")
    expiration_date: str = Field(..., description="Policy expiration date (YYYY-MM-DD)")
    renewal_date: str = Field(..., description="Next renewal date (YYYY-MM-DD)")
    cancellation_date: Optional[str] = Field(
        None, description="Scheduled or actual cancellation date if applicable"
    )
    cancellation_reason: Optional[CancellationReason] = Field(
        None, description="Reason for cancellation if applicable"
    )
    named_insured_id: str = Field(..., description="Customer ID of the named insured")
    co_insured_id: Optional[str] = Field(
        None, description="Customer ID of the co-insured if any"
    )
    automatic_extension_days: int = Field(
        default=14, description="Days of automatic coverage for newly acquired vehicles"
    )
    at_fault_claims_3_years: int = Field(
        default=0, description="Number of at-fault claims in last 3 years"
    )
    lapse_flag: bool = Field(
        default=False, description="Whether policy has had a coverage lapse"
    )
    lapse_start: Optional[str] = Field(None, description="Start date of coverage lapse")
    lapse_end: Optional[str] = Field(None, description="End date of coverage lapse")

    def get_id(self) -> str:
        """Return the unique identifier for this policy."""
        return self.id


class Vehicle(BaseModel):
    """Vehicle on policy model."""

    table_name: ClassVar[str] = "vehicles"

    id: str = Field(..., description="Unique identifier for the vehicle (VEH-########)")
    policy_id: str = Field(..., description="The policy this vehicle belongs to")
    vin: str = Field(..., description="Vehicle Identification Number (17 characters)")
    year: int = Field(..., description="Model year")
    make: str = Field(..., description="Vehicle manufacturer")
    model: str = Field(..., description="Vehicle model")
    status: VehicleStatus = Field(
        default=VehicleStatus.ACTIVE, description="Active or Removed"
    )
    effective_date: str = Field(
        ..., description="Date vehicle coverage became effective"
    )
    removal_date: Optional[str] = Field(
        None, description="Date vehicle was removed from policy"
    )
    date_added_to_policy: str = Field(
        ..., description="Original date added to this policy"
    )
    collision_coverage: bool = Field(
        default=True, description="Whether collision coverage is active"
    )
    comprehensive_coverage: bool = Field(
        default=True, description="Whether comprehensive coverage is active"
    )
    rental_coverage: bool = Field(
        default=False, description="Whether rental car coverage is active"
    )
    uw_pending: bool = Field(
        default=False, description="Whether underwriting review is pending"
    )

    def get_id(self) -> str:
        """Return the unique identifier for this vehicle."""
        return self.id


class Driver(BaseModel):
    """Driver on policy model."""

    table_name: ClassVar[str] = "drivers"

    id: str = Field(..., description="Unique identifier for the driver (DRV-########)")
    policy_id: str = Field(..., description="The policy this driver belongs to")
    customer_id: Optional[str] = Field(
        None, description="Customer ID if driver is also a customer"
    )
    name: str = Field(..., description="Driver's full name")
    date_of_birth: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    license_number: Optional[str] = Field(None, description="Driver's license number")
    license_state: Optional[str] = Field(
        None, description="State that issued the license"
    )
    relationship: str = Field(
        ...,
        description="Relationship to policyholder (Self, Spouse, Son, Daughter, etc)",
    )
    status: DriverStatus = Field(
        default=DriverStatus.RATED, description="Driver status on policy"
    )
    effective_date: str = Field(..., description="Date driver was added to policy")
    removal_date: Optional[str] = Field(
        None, description="Date driver was removed from policy"
    )
    is_named_insured: bool = Field(
        default=False, description="Whether driver is the named insured"
    )
    is_co_insured: bool = Field(
        default=False, description="Whether driver is the co-insured"
    )
    uw_pending: bool = Field(
        default=False, description="Whether underwriting review is pending"
    )
    exclusion_form_required: bool = Field(
        default=False, description="Whether exclusion form is required"
    )

    def get_id(self) -> str:
        """Return the unique identifier for this driver."""
        return self.id


class DocumentType(str, Enum):
    """Policy document type values."""

    PROOF_OF_INSURANCE = "proof_of_insurance"
    DECLARATIONS_PAGE = "declarations_page"
    ID_CARD = "id_card"


class PolicyDocument(BaseModel):
    """Policy document generation record model."""

    table_name: ClassVar[str] = "policy_documents"

    id: str = Field(
        ..., description="Unique identifier for the document record (DOC-######)"
    )
    policy_id: str = Field(..., description="The policy this document belongs to")
    ticket_id: str = Field(
        ..., description="The Zendesk ticket ID associated with this request"
    )
    document_type: DocumentType = Field(..., description="Type of document generated")
    url: str = Field(..., description="Secure URL to access the document")
    created_at: str = Field(
        ..., description="Timestamp when link was created (ISO 8601 format)"
    )
    expires_at: str = Field(
        ..., description="Timestamp when link expires (ISO 8601 format)"
    )

    def get_id(self) -> str:
        """Return the unique identifier for this policy document."""
        return self.id
