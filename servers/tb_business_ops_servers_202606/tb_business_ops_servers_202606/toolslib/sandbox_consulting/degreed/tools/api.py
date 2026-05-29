# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for Degreed Learning Management API (master tool)."""

from enum import Enum
from typing import Any, Dict, List, Optional, Type

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.degreed.models import (
    Certification,
    TrainingCategory,
    TrainingCourse,
    TrainingEnrollment,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.salesforce_crm.models import Client
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field


class DegreedApiAction(str, Enum):
    """Degreed API action enumeration."""

    SEARCH_COURSES = "search_courses"
    GET_COURSE_DETAILS = "get_course_details"
    CHECK_ENROLLMENT = "check_enrollment"
    ENROLL_EMPLOYEE = "enroll_employee"
    GET_TRAINING_HISTORY = "get_training_history"
    CHECK_CERTIFICATION_STATUS = "check_certification_status"
    GET_REQUIRED_TRAININGS = "get_required_trainings"


class DegreedApiInput(BaseModel):
    """Input for degreed_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    action: DegreedApiAction = Field(
        ...,
        description="Action to perform",
        examples=["search_courses"],
    )
    keyword: Optional[str] = Field(
        None,
        description="Search keyword (required for search_courses)",
        examples=["Python"],
    )
    category: Optional[TrainingCategory] = Field(
        None,
        description="Training category filter (optional for search_courses)",
        examples=["must_have"],
    )
    course_id: Optional[str] = Field(
        None,
        description="Course ID (required for get_course_details, check_enrollment, enroll_employee)",
        examples=["CRS-0012345"],
    )
    email: Optional[str] = Field(
        None,
        description="Employee email (required for enroll_employee, get_training_history, check_certification_status)",
        examples=["user@msg.com"],
    )
    certification_name: Optional[str] = Field(
        None,
        description="Certification name (required for check_certification_status)",
        examples=["HIPAA"],
    )
    client_id: Optional[str] = Field(
        None,
        description="Client ID (required for get_required_trainings)",
        examples=["CLT-0012345"],
    )


class CourseOutput(BaseModel):
    """Course output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    id: str = Field(..., description="Course ID")
    title: str = Field(..., description="Course title")
    cost: int = Field(..., description="Course cost in USD")
    training_category: str = Field(..., description="Training category")
    max_seats: Optional[int] = Field(None, description="Maximum seats")
    start_date: Optional[str] = Field(None, description="Course start date")
    end_date: Optional[str] = Field(None, description="Course end date")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites")


class TrainingEnrollmentOutput(BaseModel):
    """Training enrollment output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    course_id: str = Field(..., description="Course ID")


class CertificationOutput(BaseModel):
    """Certification output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="Certification ID")
    employee_email: str = Field(..., description="Employee email")
    certification_name: str = Field(..., description="Certification name")
    issued_date: str = Field(..., description="Issue date")
    expiry_date: Optional[str] = Field(None, description="Expiry date")


class DegreedApiOutput(BaseModel):
    """Output for degreed_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    courses: Optional[List[CourseOutput]] = Field(
        None,
        description="Array of course records from training_courses table (for action=search_courses)",
    )
    course_data: Optional[CourseOutput] = Field(
        None,
        description="Course record from training_courses table (for action=get_course_details)",
    )
    available_seats: Optional[int] = Field(
        None,
        description="Number of available seats (for action=check_enrollment). Returns 99999 for courses with unlimited capacity.",
    )
    success: Optional[bool] = Field(
        None,
        description="Indicates if enrollment was successful (for enroll_employee)",
    )
    completed_trainings: Optional[List[TrainingEnrollmentOutput]] = Field(
        None,
        description="Array of completed training enrollment records from training_enrollments table (for action=get_training_history)",
    )
    certifications: Optional[List[CertificationOutput]] = Field(
        None,
        description="Array of all certification records from certifications table (for action=get_training_history)",
    )
    has_certification: Optional[bool] = Field(
        None,
        description="Indicates if employee has certification (for action=check_certification_status)",
    )
    required_courses: Optional[List[str]] = Field(
        None,
        description="Array of required course IDs (for action=get_required_trainings)",
    )


class DegreedApiTool(Tool):
    """Master tool implementation for Degreed Learning Management API."""

    @property
    def name(self) -> str:
        return "api"

    @property
    def description(self) -> str:
        return (
            "Access training courses, enrollment, and certification tracking. Searches training "
            "catalog, retrieves course details, checks enrollment availability, enrolls employees, "
            "retrieves training history and certifications. Use action parameter to specify the operation:\n\n"
            "- action='search_courses': Searches training catalog by keyword. REQUIRES: keyword. "
            "OPTIONAL: category (must_have, nice_to_have, conference). Returns courses array from "
            "training_courses table.\n\n"
            "- action='get_course_details': Retrieves complete course information including title, cost, "
            "training_category, max_seats, start_date, end_date, and prerequisites. REQUIRES: course_id. "
            "Returns course_data object from training_courses table.\n\n"
            "- action='check_enrollment': Checks available seat capacity for a course. REQUIRES: course_id. "
            "Returns available_seats integer. Courses with unlimited capacity return 99999 available seats.\n\n"
            "- action='enroll_employee': Enrolls an employee in a training course. REQUIRES: email, course_id. "
            "Returns success boolean. Creates record in training_enrollments table.\n\n"
            "- action='get_training_history': Retrieves completed trainings and all certifications for an "
            "employee. REQUIRES: email. Returns two separate arrays: completed_trainings[] (from "
            "training_enrollments) and certifications[] (all certifications for employee from certifications table).\n\n"
            "- action='check_certification_status': Verifies if employee has a specific certification. "
            "REQUIRES: email, certification_name. Returns has_certification boolean. Checks certifications "
            "table for employee - returns true if certification exists regardless of expiry.\n\n"
            "- action='get_required_trainings': Retrieves list of required training courses for a client. "
            "REQUIRES: client_id. Returns required_courses array of course IDs from clients.required_training_courses field.\n\n"
            "Use get_course_details to retrieve training category, cost, and dates for approval logic. Use "
            "get_training_history to check prerequisite completion before enrollment - returns separate "
            "completed_trainings and certifications arrays."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(DegreedApiInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(DegreedApiOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return DegreedApiInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return DegreedApiOutput

    async def run(
        self, db: InMemoryDatabase, request: DegreedApiInput
    ) -> DegreedApiOutput:
        """Execute Degreed API action."""
        try:
            if request.action == DegreedApiAction.SEARCH_COURSES:
                return await self._search_courses(db, request)
            elif request.action == DegreedApiAction.GET_COURSE_DETAILS:
                return await self._get_course_details(db, request)
            elif request.action == DegreedApiAction.CHECK_ENROLLMENT:
                return await self._check_enrollment(db, request)
            elif request.action == DegreedApiAction.ENROLL_EMPLOYEE:
                return await self._enroll_employee(db, request)
            elif request.action == DegreedApiAction.GET_TRAINING_HISTORY:
                return await self._get_training_history(db, request)
            elif request.action == DegreedApiAction.CHECK_CERTIFICATION_STATUS:
                return await self._check_certification_status(db, request)
            elif request.action == DegreedApiAction.GET_REQUIRED_TRAININGS:
                return await self._get_required_trainings(db, request)
            else:
                raise Tool.ExecutionError(f"Invalid action: {request.action}")

        except Tool.ExecutionError:
            raise
        except Exception as e:
            error_message = f"Failed to execute Degreed API action: {str(e)}"
            raise Tool.ExecutionError(error_message)

    async def _search_courses(
        self, db: InMemoryDatabase, request: DegreedApiInput
    ) -> DegreedApiOutput:
        """Search training catalog by keyword."""
        if not request.keyword:
            raise Tool.ExecutionError("Missing required parameter: keyword")

        # Get all courses
        all_courses = db.get_all(TrainingCourse)

        # Filter by keyword (case-insensitive contains match)
        matching_courses = [
            course
            for course in all_courses
            if request.keyword.lower() in course.title.lower()
        ]

        # Apply category filter if provided
        if request.category:
            matching_courses = [
                course
                for course in matching_courses
                if course.training_category == request.category
            ]

        # Convert to output format
        courses = [
            CourseOutput(
                id=course.id,
                title=course.title,
                cost=course.cost,
                training_category=course.training_category.value,
                max_seats=course.max_seats,
                start_date=course.start_date.isoformat() if course.start_date else None,
                end_date=course.end_date.isoformat() if course.end_date else None,
                prerequisites=course.prerequisites,
            )
            for course in matching_courses
        ]

        return DegreedApiOutput(courses=courses)

    async def _get_course_details(
        self, db: InMemoryDatabase, request: DegreedApiInput
    ) -> DegreedApiOutput:
        """Get complete course information."""
        if not request.course_id:
            raise Tool.ExecutionError("Missing required parameter: course_id")

        # Get course by ID
        course = db.get_by_id(TrainingCourse, request.course_id)

        if not course:
            raise Tool.ExecutionError(f"Course not found: {request.course_id}")

        # Convert to output format
        course_data = CourseOutput(
            id=course.id,
            title=course.title,
            cost=course.cost,
            training_category=course.training_category.value,
            max_seats=course.max_seats,
            start_date=course.start_date.isoformat() if course.start_date else None,
            end_date=course.end_date.isoformat() if course.end_date else None,
            prerequisites=course.prerequisites,
        )

        return DegreedApiOutput(course_data=course_data)

    async def _check_enrollment(
        self, db: InMemoryDatabase, request: DegreedApiInput
    ) -> DegreedApiOutput:
        """Check available seat capacity for a course."""
        if not request.course_id:
            raise Tool.ExecutionError("Missing required parameter: course_id")

        # Get course by ID
        course = db.get_by_id(TrainingCourse, request.course_id)

        if not course:
            raise Tool.ExecutionError(f"Course not found: {request.course_id}")

        # If max_seats is null, return 99999 (unlimited capacity)
        if course.max_seats is None:
            return DegreedApiOutput(available_seats=99999)

        # Get all enrollments
        all_enrollments = db.get_all(TrainingEnrollment)

        # Count active enrollments (completion_date is null)
        active_enrollments = sum(
            1
            for enrollment in all_enrollments
            if enrollment.course_id == request.course_id
            and enrollment.completion_date is None
        )

        # Calculate available seats
        available_seats = course.max_seats - active_enrollments

        return DegreedApiOutput(available_seats=available_seats)

    async def _enroll_employee(
        self, db: InMemoryDatabase, request: DegreedApiInput
    ) -> DegreedApiOutput:
        """Enroll an employee in a training course."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")
        if not request.course_id:
            raise Tool.ExecutionError("Missing required parameter: course_id")

        # Verify course exists
        course = db.get_by_id(TrainingCourse, request.course_id)
        if not course:
            raise Tool.ExecutionError(f"Course not found: {request.course_id}")

        # Generate enrollment ID
        existing_enrollments = db.get_all(TrainingEnrollment)
        PREFIX_FOR_NEW_IDS = "ENR-2"
        count = 0
        existing_ids = {enrollment.id for enrollment in existing_enrollments}

        while True:
            new_id = f"{PREFIX_FOR_NEW_IDS}-{count:06d}"
            if new_id not in existing_ids:
                break
            count += 1

        # Create enrollment
        new_enrollment = TrainingEnrollment(
            id=new_id,
            employee_email=request.email,
            course_id=request.course_id,
            completion_date=None,
        )
        db.create(new_enrollment)

        return DegreedApiOutput(success=True)

    async def _get_training_history(
        self, db: InMemoryDatabase, request: DegreedApiInput
    ) -> DegreedApiOutput:
        """Retrieve completed trainings and all certifications for an employee."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")

        # Get all enrollments
        all_enrollments = db.get_all(TrainingEnrollment)

        # Filter completed trainings for employee
        completed_trainings = [
            TrainingEnrollmentOutput(course_id=enrollment.course_id)
            for enrollment in all_enrollments
            if enrollment.employee_email == request.email
            and enrollment.completion_date is not None
        ]

        # Get all certifications for employee
        all_certifications = db.get_all(Certification)
        employee_certifications = [
            CertificationOutput(
                id=cert.id,
                employee_email=cert.employee_email,
                certification_name=cert.certification_name,
                issued_date=cert.issued_date.isoformat(),
                expiry_date=cert.expiry_date.isoformat() if cert.expiry_date else None,
            )
            for cert in all_certifications
            if cert.employee_email == request.email
        ]

        return DegreedApiOutput(
            completed_trainings=completed_trainings,
            certifications=employee_certifications,
        )

    async def _check_certification_status(
        self, db: InMemoryDatabase, request: DegreedApiInput
    ) -> DegreedApiOutput:
        """Verify if employee has a specific certification."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")
        if not request.certification_name:
            raise Tool.ExecutionError("Missing required parameter: certification_name")

        # Get all certifications
        all_certifications = db.get_all(Certification)

        # Check if employee has the certification (case-insensitive exact match)
        has_certification = any(
            cert.employee_email == request.email
            and cert.certification_name.lower() == request.certification_name.lower()
            for cert in all_certifications
        )

        return DegreedApiOutput(has_certification=has_certification)

    async def _get_required_trainings(
        self, db: InMemoryDatabase, request: DegreedApiInput
    ) -> DegreedApiOutput:
        """Retrieve list of required training courses for a client."""
        if not request.client_id:
            raise Tool.ExecutionError("Missing required parameter: client_id")

        # Get client by ID
        client = db.get_by_id(Client, request.client_id)

        if not client:
            raise Tool.ExecutionError(f"Client not found: {request.client_id}")

        # Return required training courses
        return DegreedApiOutput(required_courses=client.required_training_courses)
