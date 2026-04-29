# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for CRM (Customer Relationship Management) MCP server."""

from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, Field


class CustomerTier(str, Enum):
    """Customer tier values."""

    STANDARD = "Standard"
    PREFERRED = "Preferred"
    PREMIUM = "Premium"


class Customer(BaseModel):
    """Customer profile model."""

    table_name: ClassVar[str] = "customers"

    id: str = Field(
        ..., description="Unique identifier for the customer (CUS-########)"
    )
    email: str = Field(..., description="Email address of the customer")
    first_name: str = Field(..., description="Customer's first name", min_length=1)
    last_name: str = Field(..., description="Customer's last name", min_length=1)
    date_of_birth: str = Field(..., description="Customer's date of birth (YYYY-MM-DD)")
    phone: Optional[str] = Field(None, description="Customer's phone number")
    tier: CustomerTier = Field(
        default=CustomerTier.STANDARD, description="Customer service tier"
    )
    fraud_flag: bool = Field(
        default=False, description="Whether customer has been flagged for fraud"
    )
    ssn_last_4: Optional[str] = Field(
        None, description="Last 4 digits of SSN for verification"
    )
    security_question: Optional[str] = Field(
        None, description="Security question for identity verification"
    )
    security_answer: Optional[str] = Field(
        None, description="Answer to security question (case-insensitive)"
    )

    def get_id(self) -> str:
        """Return the unique identifier for this customer."""
        return self.id


class CustomerProfile(BaseModel):
    """Customer profile output model (without sensitive data)."""

    customer_id: str = Field(..., description="Customer's unique identifier")
    email: str = Field(..., description="Customer's email address")
    first_name: str = Field(..., description="Customer's first name")
    last_name: str = Field(..., description="Customer's last name")
    date_of_birth: str = Field(..., description="Customer's date of birth (YYYY-MM-DD)")
    phone: Optional[str] = Field(None, description="Customer's phone number")
    tier: str = Field(..., description="Customer tier: Standard, Preferred, or Premium")
    fraud_flag: bool = Field(..., description="Whether customer has fraud flag")
    security_question: Optional[str] = Field(
        None, description="Security question for verification (answer not returned)"
    )
    has_ssn_on_file: bool = Field(
        ..., description="Whether SSN last 4 is available for verification"
    )
