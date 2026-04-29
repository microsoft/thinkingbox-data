# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for degreed_api master tool."""

from datetime import datetime

import pytest
from ms_toloka_servers.toolslib.sandbox_consulting.degreed.models import (
    Certification,
    TrainingCategory,
    TrainingCourse,
    TrainingEnrollment,
)
from ms_toloka_servers.toolslib.sandbox_consulting.degreed.tools.api import (
    DegreedApiTool,
)
from ms_toloka_servers.toolslib.sandbox_consulting.salesforce_crm.models import (
    ClearanceLevel,
    Client,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


class TestDegreedApi:
    @pytest.fixture
    def test_db(self):
        """Create a test database with training courses, enrollments, and certifications."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {
            "training_courses": TrainingCourse,
            "training_enrollments": TrainingEnrollment,
            "certifications": Certification,
            "clients": Client,
        }
        db._model_cls_to_stem = {
            TrainingCourse: "training_courses",
            TrainingEnrollment: "training_enrollments",
            Certification: "certifications",
            Client: "clients",
        }

        # Create test courses
        course1 = TrainingCourse(
            id="CRS-1000001",
            title="Python Programming Fundamentals",
            cost=0,
            training_category=TrainingCategory.MUST_HAVE,
            max_seats=None,
            start_date=None,
            end_date=None,
            prerequisites=[],
        )

        course2 = TrainingCourse(
            id="CRS-1000002",
            title="Advanced Data Analytics with Python",
            cost=500,
            training_category=TrainingCategory.NICE_TO_HAVE,
            max_seats=20,
            start_date=datetime(2025, 2, 15, 9, 0, 0),
            end_date=datetime(2025, 2, 17, 17, 0, 0),
            prerequisites=["CRS-1000001"],
        )

        course3 = TrainingCourse(
            id="CRS-1000003",
            title="HIPAA Compliance Training",
            cost=0,
            training_category=TrainingCategory.MUST_HAVE,
            max_seats=None,
            start_date=None,
            end_date=None,
            prerequisites=[],
        )

        course4 = TrainingCourse(
            id="CRS-1000004",
            title="AWS Summit 2025",
            cost=2500,
            training_category=TrainingCategory.CONFERENCE,
            max_seats=5,
            start_date=datetime(2025, 5, 10, 8, 0, 0),
            end_date=datetime(2025, 5, 12, 18, 0, 0),
            prerequisites=[],
        )

        # Create test enrollments
        enrollment1 = TrainingEnrollment(
            id="ENR-1000001",
            employee_email="jane.doe@msg.com",
            course_id="CRS-1000001",
            completion_date=datetime(2024, 11, 15),
        )

        enrollment2 = TrainingEnrollment(
            id="ENR-1000002",
            employee_email="jane.doe@msg.com",
            course_id="CRS-1000003",
            completion_date=datetime(2024, 10, 20),
        )

        enrollment3 = TrainingEnrollment(
            id="ENR-1000003",
            employee_email="john.smith@msg.com",
            course_id="CRS-1000002",
            completion_date=None,
        )

        enrollment4 = TrainingEnrollment(
            id="ENR-1000004",
            employee_email="bob.wilson@msg.com",
            course_id="CRS-1000004",
            completion_date=None,
        )

        # Create test certifications
        cert1 = Certification(
            id="CERT-1000001",
            employee_email="jane.doe@msg.com",
            certification_name="HIPAA",
            issued_date=datetime(2024, 11, 1),
            expiry_date=datetime(2025, 11, 1),
        )

        cert2 = Certification(
            id="CERT-1000002",
            employee_email="jane.doe@msg.com",
            certification_name="Python Professional",
            issued_date=datetime(2024, 11, 20),
            expiry_date=None,
        )

        cert3 = Certification(
            id="CERT-1000003",
            employee_email="john.smith@msg.com",
            certification_name="AWS Certified Solutions Architect",
            issued_date=datetime(2024, 6, 15),
            expiry_date=datetime(2027, 6, 15),
        )

        # Create test client
        client1 = Client(
            id="CLT-0012345",
            name="Healthcare Corp",
            requires_nda=True,
            clearance_level=ClearanceLevel.STANDARD,
            required_training_courses=["CRS-1000003", "CRS-1000001"],
        )

        db._store = {
            TrainingCourse: [course1, course2, course3, course4],
            TrainingEnrollment: [enrollment1, enrollment2, enrollment3, enrollment4],
            Certification: [cert1, cert2, cert3],
            Client: [client1],
        }
        return db

    @pytest.fixture
    def degreed_tool(self):
        """Create an instance of the Degreed API tool."""
        return DegreedApiTool()

    # Tests for search_courses action
    @pytest.mark.anyio
    async def test_search_courses_success(self, degreed_tool, test_db):
        """Test successful course search by keyword."""
        # Arrange
        request_data = {"action": "search_courses", "keyword": "Python"}

        # Act
        result = await degreed_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("courses") is not None
        courses = result["courses"]
        assert len(courses) == 2
        assert all("Python" in course["title"] for course in courses)

    @pytest.mark.anyio
    async def test_search_courses_with_category(self, degreed_tool, test_db):
        """Test course search with category filter."""
        # Arrange
        request_data = {
            "action": "search_courses",
            "keyword": "Python",
            "category": "must_have",
        }

        # Act
        result = await degreed_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("courses") is not None
        courses = result["courses"]
        assert len(courses) == 1
        assert courses[0]["title"] == "Python Programming Fundamentals"
        assert courses[0]["training_category"] == "must_have"

    @pytest.mark.anyio
    async def test_search_courses_no_results(self, degreed_tool, test_db):
        """Test course search with no matching results."""
        # Arrange
        request_data = {"action": "search_courses", "keyword": "NonExistentCourse"}

        # Act
        result = await degreed_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("courses") is not None
        assert len(result["courses"]) == 0

    @pytest.mark.anyio
    async def test_search_courses_missing_keyword(self, degreed_tool, test_db):
        """Test search without keyword raises error."""
        # Arrange
        request_data = {"action": "search_courses"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: keyword"
        ):
            await degreed_tool.run_with_validation(test_db, request_data)

    # Tests for get_course_details action
    @pytest.mark.anyio
    async def test_get_course_details_success(self, degreed_tool, test_db):
        """Test successful retrieval of course details."""
        # Arrange
        request_data = {"action": "get_course_details", "course_id": "CRS-1000002"}

        # Act
        result = await degreed_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("course_data") is not None
        course = result["course_data"]
        assert course["id"] == "CRS-1000002"
        assert course["title"] == "Advanced Data Analytics with Python"
        assert course["cost"] == 500
        assert course["training_category"] == "nice_to_have"
        assert course["max_seats"] == 20
        assert course["prerequisites"] == ["CRS-1000001"]

    @pytest.mark.anyio
    async def test_get_course_details_not_found(self, degreed_tool, test_db):
        """Test course details for non-existent course."""
        # Arrange
        request_data = {"action": "get_course_details", "course_id": "CRS-9999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Course not found"):
            await degreed_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_course_details_missing_course_id(self, degreed_tool, test_db):
        """Test get course details without course_id raises error."""
        # Arrange
        request_data = {"action": "get_course_details"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: course_id"
        ):
            await degreed_tool.run_with_validation(test_db, request_data)

    # Tests for check_enrollment action
    @pytest.mark.anyio
    async def test_check_enrollment_unlimited_capacity(self, degreed_tool, test_db):
        """Test check enrollment for course with unlimited capacity."""
        # Arrange
        request_data = {"action": "check_enrollment", "course_id": "CRS-1000001"}

        # Act
        result = await degreed_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("available_seats") == 99999

    @pytest.mark.anyio
    async def test_check_enrollment_with_capacity(self, degreed_tool, test_db):
        """Test check enrollment for course with limited capacity."""
        # Arrange
        request_data = {"action": "check_enrollment", "course_id": "CRS-1000002"}

        # Act
        result = await degreed_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["available_seats"] == 19  # max_seats=20, 1 active enrollment

    @pytest.mark.anyio
    async def test_check_enrollment_full_course(self, degreed_tool, test_db):
        """Test check enrollment for course with limited seats."""
        # Arrange
        request_data = {"action": "check_enrollment", "course_id": "CRS-1000004"}

        # Act
        result = await degreed_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["available_seats"] == 4  # max_seats=5, 1 active enrollment

    @pytest.mark.anyio
    async def test_check_enrollment_missing_course_id(self, degreed_tool, test_db):
        """Test check enrollment without course_id raises error."""
        # Arrange
        request_data = {"action": "check_enrollment"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: course_id"
        ):
            await degreed_tool.run_with_validation(test_db, request_data)

    # Tests for enroll_employee action
    @pytest.mark.anyio
    async def test_enroll_employee_success(self, degreed_tool, test_db):
        """Test successful employee enrollment."""
        # Arrange
        request_data = {
            "action": "enroll_employee",
            "email": "new.user@msg.com",
            "course_id": "CRS-1000001",
        }

        # Act
        result = await degreed_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["success"] is True

        # Verify enrollment was created
        enrollments = test_db.get_all(TrainingEnrollment)
        new_enrollment = [
            e for e in enrollments if e.employee_email == "new.user@msg.com"
        ]
        assert len(new_enrollment) == 1
        assert new_enrollment[0].course_id == "CRS-1000001"
        assert new_enrollment[0].completion_date is None

    @pytest.mark.anyio
    async def test_enroll_employee_course_not_found(self, degreed_tool, test_db):
        """Test enrollment with non-existent course."""
        # Arrange
        request_data = {
            "action": "enroll_employee",
            "email": "user@msg.com",
            "course_id": "CRS-9999999",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Course not found"):
            await degreed_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_enroll_employee_missing_email(self, degreed_tool, test_db):
        """Test enrollment without email raises error."""
        # Arrange
        request_data = {"action": "enroll_employee", "course_id": "CRS-1000001"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await degreed_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_enroll_employee_missing_course_id(self, degreed_tool, test_db):
        """Test enrollment without course_id raises error."""
        # Arrange
        request_data = {"action": "enroll_employee", "email": "user@msg.com"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: course_id"
        ):
            await degreed_tool.run_with_validation(test_db, request_data)

    # Tests for get_training_history action
    @pytest.mark.anyio
    async def test_get_training_history_success(self, degreed_tool, test_db):
        """Test successful retrieval of training history."""
        # Arrange
        request_data = {"action": "get_training_history", "email": "jane.doe@msg.com"}

        # Act
        result = await degreed_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("completed_trainings") is not None
        assert result.get("certifications") is not None

        # Check completed trainings
        completed = result["completed_trainings"]
        assert len(completed) == 2
        course_ids = [t["course_id"] for t in completed]
        assert "CRS-1000001" in course_ids
        assert "CRS-1000003" in course_ids

        # Check certifications
        certs = result["certifications"]
        assert len(certs) == 2
        cert_names = [c["certification_name"] for c in certs]
        assert "HIPAA" in cert_names
        assert "Python Professional" in cert_names

    @pytest.mark.anyio
    async def test_get_training_history_empty(self, degreed_tool, test_db):
        """Test training history for employee with no history."""
        # Arrange
        request_data = {"action": "get_training_history", "email": "nobody@msg.com"}

        # Act
        result = await degreed_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("completed_trainings") is not None
        assert len(result["completed_trainings"]) == 0
        assert result.get("certifications") is not None
        assert len(result["certifications"]) == 0

    @pytest.mark.anyio
    async def test_get_training_history_missing_email(self, degreed_tool, test_db):
        """Test get training history without email raises error."""
        # Arrange
        request_data = {"action": "get_training_history"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await degreed_tool.run_with_validation(test_db, request_data)

    # Tests for check_certification_status action
    @pytest.mark.anyio
    async def test_check_certification_status_has_cert(self, degreed_tool, test_db):
        """Test checking certification status when employee has certification."""
        # Arrange
        request_data = {
            "action": "check_certification_status",
            "email": "jane.doe@msg.com",
            "certification_name": "HIPAA",
        }

        # Act
        result = await degreed_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["has_certification"] is True

    @pytest.mark.anyio
    async def test_check_certification_status_case_insensitive(
        self, degreed_tool, test_db
    ):
        """Test certification check is case-insensitive."""
        # Arrange
        request_data = {
            "action": "check_certification_status",
            "email": "jane.doe@msg.com",
            "certification_name": "hipaa",
        }

        # Act
        result = await degreed_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["has_certification"] is True

    @pytest.mark.anyio
    async def test_check_certification_status_no_cert(self, degreed_tool, test_db):
        """Test checking certification when employee doesn't have it."""
        # Arrange
        request_data = {
            "action": "check_certification_status",
            "email": "jane.doe@msg.com",
            "certification_name": "AWS",
        }

        # Act
        result = await degreed_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result["has_certification"] is False

    @pytest.mark.anyio
    async def test_check_certification_status_missing_email(
        self, degreed_tool, test_db
    ):
        """Test check certification without email raises error."""
        # Arrange
        request_data = {
            "action": "check_certification_status",
            "certification_name": "HIPAA",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: email"
        ):
            await degreed_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_check_certification_status_missing_cert_name(
        self, degreed_tool, test_db
    ):
        """Test check certification without certification_name raises error."""
        # Arrange
        request_data = {
            "action": "check_certification_status",
            "email": "jane.doe@msg.com",
        }

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: certification_name"
        ):
            await degreed_tool.run_with_validation(test_db, request_data)

    # Tests for get_required_trainings action
    @pytest.mark.anyio
    async def test_get_required_trainings_success(self, degreed_tool, test_db):
        """Test successful retrieval of required trainings."""
        # Arrange
        request_data = {"action": "get_required_trainings", "client_id": "CLT-0012345"}

        # Act
        result = await degreed_tool.run_with_validation(test_db, request_data)

        # Assert
        assert result.get("required_courses") is not None
        assert len(result["required_courses"]) == 2
        assert "CRS-1000003" in result["required_courses"]
        assert "CRS-1000001" in result["required_courses"]

    @pytest.mark.anyio
    async def test_get_required_trainings_client_not_found(self, degreed_tool, test_db):
        """Test get required trainings for non-existent client."""
        # Arrange
        request_data = {"action": "get_required_trainings", "client_id": "CLT-9999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Client not found"):
            await degreed_tool.run_with_validation(test_db, request_data)

    @pytest.mark.anyio
    async def test_get_required_trainings_missing_client_id(
        self, degreed_tool, test_db
    ):
        """Test get required trainings without client_id raises error."""
        # Arrange
        request_data = {"action": "get_required_trainings"}

        # Act & Assert
        with pytest.raises(
            Tool.ExecutionError, match="Missing required parameter: client_id"
        ):
            await degreed_tool.run_with_validation(test_db, request_data)

    # Test for invalid action
    @pytest.mark.anyio
    async def test_invalid_action(self, degreed_tool, test_db):
        """Test that invalid action raises validation error."""
        # Arrange
        request_data = {"action": "invalid_action"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError, match="Input validation failed"):
            await degreed_tool.run_with_validation(test_db, request_data)
