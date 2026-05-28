# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Workday HCM toolset for consulting."""

from sandbox_servers.toolslib.sandbox_consulting.workday.models import (
    ApproverAvailability,
    Employee,
    EmployeeLevel,
    OfficeLocation,
    OnboardingPhase,
)

__all__ = [
    "Employee",
    "EmployeeLevel",
    "OfficeLocation",
    "OnboardingPhase",
    "ApproverAvailability",
]
