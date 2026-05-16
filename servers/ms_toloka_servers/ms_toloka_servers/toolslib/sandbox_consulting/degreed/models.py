# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Degreed Learning Management System toolset."""

from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field


class TrainingCategory(str, Enum):
    """Training category enumeration."""

    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"
    CONFERENCE = "conference"


class TrainingCourse(BaseModel):
    """Training course model."""

    table_name: ClassVar[str] = "training_courses"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique course identifier (e.g., CRS-0012345)")
    title: str = Field(..., description="Course title")
    cost: int = Field(..., description="Course cost in USD", examples=[500])
    training_category: TrainingCategory = Field(..., description="Training category")
    max_seats: Optional[int] = Field(
        None, description="Maximum number of seats (null for unlimited)"
    )
    start_date: Optional[datetime] = Field(None, description="Course start date")
    end_date: Optional[datetime] = Field(None, description="Course end date")
    prerequisites: list[str] = Field(
        default_factory=list,
        description="List of prerequisite course IDs",
        examples=[["CRS-0012345"]],
    )

    def get_id(self) -> str:
        """Return the course ID."""
        return self.id


class TrainingEnrollment(BaseModel):
    """Training enrollment model."""

    table_name: ClassVar[str] = "training_enrollments"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique enrollment identifier")
    employee_email: str = Field(..., description="Employee email address")
    course_id: str = Field(..., description="Course ID")
    completion_date: Optional[datetime] = Field(
        None, description="Date when training was completed"
    )

    def get_id(self) -> str:
        """Return the enrollment ID."""
        return self.id


class Certification(BaseModel):
    """Certification model."""

    table_name: ClassVar[str] = "certifications"

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Unique certification identifier")
    employee_email: str = Field(..., description="Employee email address")
    certification_name: str = Field(..., description="Certification name")
    issued_date: datetime = Field(..., description="Date when certification was issued")
    expiry_date: Optional[datetime] = Field(
        None, description="Certification expiry date"
    )

    def get_id(self) -> str:
        """Return the certification ID."""
        return self.id
