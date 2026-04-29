# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Hotel Partner API tools."""

from .escalate_to_hotel import EscalateToHotelTool
from .get_hotel_contact import GetHotelContact
from .get_hotel_info import GetHotelInfo
from .verify_availability import VerifyAvailability

__all__ = [
    "GetHotelInfo",
    "EscalateToHotelTool",
    "VerifyAvailability",
    "GetHotelContact",
]
