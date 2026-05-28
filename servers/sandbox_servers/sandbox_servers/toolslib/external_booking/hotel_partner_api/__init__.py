# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Hotel Partner API module."""

from .models import Hotel, HotelData
from .tools import EscalateToHotelTool, GetHotelInfo

__all__ = [
    "GetHotelInfo",
    "EscalateToHotelTool",
    "HotelData",
    "Hotel",
]
