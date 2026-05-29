# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Workday HCM toolset for consulting."""

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.workday.models import (
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
