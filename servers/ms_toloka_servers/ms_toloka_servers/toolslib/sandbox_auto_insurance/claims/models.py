# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel


class ClaimType(str, Enum):
    COLLISION_SINGLE = "Collision – Single Vehicle"
    COLLISION_MULTI = "Collision – Multi-Vehicle"
    COLLISION_HIT_RUN = "Collision – Hit and Run"
    COLLISION_PARKED = "Collision – Parked Vehicle"
    CMP_THEFT = "Comprehensive – Theft"
    CMP_VANDALISM = "Comprehensive – Vandalism"
    CMP_WEATHER = "Comprehensive – Weather"
    CMP_FIRE = "Comprehensive – Fire"
    CMP_GLASS = "Comprehensive – Glass Only"
    CMP_ANIMAL = "Comprehensive – Animal Strike"
    LIABILITY_ONLY = "Liability Only"


class ClaimStage(str, Enum):
    OPEN_INITIAL = "Open – Initial Review"
    OPEN_INVESTIGATION = "Open – Investigation"
    OPEN_REPAIR = "Open – Repair/Recovery"
    OPEN_SETTLEMENT = "Open – Settlement"
    CLOSED_PAID = "Closed – Paid"
    CLOSED_DENIED = "Closed – Denied"
    CLOSED_WITHDRAWN = "Closed – Withdrawn"


class ClaimSeverity(str, Enum):
    MINOR = "Minor"
    MODERATE = "Moderate"
    MAJOR = "Major"


class SIUFlag(str, Enum):
    NONE = "None"
    SUSPICIOUS = "Suspicious Activity Flagged"
    CONFIRMED = "Confirmed SIU Referral"


class Claim(BaseModel):
    table_name: ClassVar[str] = "claims"

    id: str
    policy_id: str
    vehicle_id: Optional[str] = None
    vehicle_vin: Optional[str] = None
    driver_id: Optional[str] = None
    date_of_loss: str
    loss_location: str
    claim_type: ClaimType
    claim_stage: ClaimStage = ClaimStage.OPEN_INITIAL
    severity: ClaimSeverity = ClaimSeverity.MODERATE
    siu_flag: SIUFlag = SIUFlag.NONE
    unlisted_driver_flag: bool = False
    has_bodily_injury: bool = False
    police_report_required: bool = False
    police_report_number: Optional[str] = None
    other_party_name: Optional[str] = None
    other_party_phone: Optional[str] = None
    other_party_insurance: Optional[str] = None
    created_date: str

    def get_id(self) -> str:
        return self.id


__all__ = [
    "ClaimType",
    "ClaimStage",
    "ClaimSeverity",
    "SIUFlag",
    "Claim",
]
