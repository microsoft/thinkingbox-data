# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class CorporateAccountTier(str, Enum):
    ENTERPRISE = "enterprise"
    MID_MARKET = "mid_market"
    SMALL_BUSINESS = "small_business"


class AccountStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING = "pending"


class CorporateAccount(BaseModel):
    table_name: str = "corporate_accounts"

    id: str = Field(..., description="Internal system ID")
    corporate_account_id: str = Field(
        ..., description="Public corporate account identifier"
    )
    company_name: str = Field(..., description="Company name")
    account_tier: CorporateAccountTier = Field(..., description="Tier")
    account_status: AccountStatus = Field(..., description="Account status")
    contact_name: str = Field(..., description="Primary contact name")
    contact_email: str = Field(..., description="Primary contact email")
    contact_phone: str = Field(..., description="Primary contact phone")

    booking_limit: int = Field(..., description="Max allowed active bookings")
    credit_limit: Decimal = Field(..., description="Max allowed credit")
    payment_terms: str = Field(..., description="Payment terms such as 'Net 30'")

    expiration_date: Optional[datetime] = Field(None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_id(self) -> str:
        return self.id


__all__ = [
    "CorporateAccount",
    "CorporateAccountTier",
    "AccountStatus",
]
