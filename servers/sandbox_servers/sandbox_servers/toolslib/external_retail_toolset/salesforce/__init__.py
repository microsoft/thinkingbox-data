# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Salesforce Customer 360 (CDP) toolset for external retail."""

from .models import (
    BehavioralSegment,
    CustomerProfile,
    CustomerTier,
    MembershipRecord,
    MembershipStatus,
    PointsAdjustmentReason,
)

__all__ = [
    "BehavioralSegment",
    "CustomerProfile",
    "CustomerTier",
    "MembershipRecord",
    "MembershipStatus",
    "PointsAdjustmentReason",
]
