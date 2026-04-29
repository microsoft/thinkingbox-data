# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for reschedule_installation tool."""

import pytest
from ms_toloka_servers.toolslib.external_retail_toolset.jobber.models import (
    InstallationJob,
    InstallationJobStatus,
    InstallationServiceType,
)
from ms_toloka_servers.toolslib.external_retail_toolset.jobber.tools.reschedule_installation import (
    RescheduleInstallationTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestRescheduleInstallation:
    @pytest.fixture
    def test_db(self):
        """Create a test database with installation jobs."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"installation_job": InstallationJob}
        db._model_cls_to_stem = {InstallationJob: "installation_job"}

        # Create test installation jobs
        job1 = InstallationJob(
            id="JOB-10000001",
            order_id="ORD-10000001",
            customer_id="CUS-10000001",
            service_type=InstallationServiceType.APPLIANCE_BASIC,
            scheduled_date="2024-10-25T10:00:00Z",
            technician_id="TECH-0045",
            status=InstallationJobStatus.SCHEDULED,
            completion_date=None,
            workmanship_warranty_end=None,
            service_cost=129.00,
        )

        job2 = InstallationJob(
            id="JOB-10000002",
            order_id="ORD-10000002",
            customer_id="CUS-10000002",
            service_type=InstallationServiceType.TV_MOUNTING,
            scheduled_date="2024-10-20T14:00:00Z",
            technician_id="TECH-0023",
            status=InstallationJobStatus.COMPLETED,
            completion_date="2024-10-20T16:30:00Z",
            workmanship_warranty_end="2025-01-18T23:59:59Z",
            service_cost=99.00,
        )

        job3 = InstallationJob(
            id="JOB-10000003",
            order_id="ORD-10000003",
            customer_id="CUS-10000003",
            service_type=InstallationServiceType.APPLIANCE_ADVANCED,
            scheduled_date="2024-11-05T09:00:00Z",
            technician_id=None,
            status=InstallationJobStatus.CANCELLED,
            completion_date=None,
            workmanship_warranty_end=None,
            service_cost=249.00,
        )

        db._store = {InstallationJob: [job1, job2, job3]}
        return db

    @pytest.fixture
    def reschedule_installation_tool(self):
        """Create an instance of RescheduleInstallationTool."""
        return RescheduleInstallationTool()

    @pytest.mark.anyio
    async def test_reschedule_installation_success(
        self, reschedule_installation_tool, test_db
    ):
        """Test successfully rescheduling an installation."""
        # Arrange
        request_data = {
            "job_id": "JOB-10000001",
            "new_scheduled_date": "2024-10-30T14:00:00Z",
            "reschedule_reason": "customer_request",
        }

        # Act
        result = await reschedule_installation_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["job_id"] == "JOB-10000001"
        assert result["old_scheduled_date"] == "2024-10-25T10:00:00+00:00"
        assert result["new_scheduled_date"] == "2024-10-30T14:00:00+00:00"
        assert result["status"] == "scheduled"

        # Verify database was updated
        all_jobs = test_db.get_all(InstallationJob)
        job = next(j for j in all_jobs if j.id == "JOB-10000001")
        assert job.scheduled_date.isoformat() == "2024-10-30T14:00:00+00:00"

    @pytest.mark.anyio
    async def test_reschedule_workmanship_issue(
        self, reschedule_installation_tool, test_db
    ):
        """Test rescheduling a completed job due to workmanship issue."""
        # Arrange
        request_data = {
            "job_id": "JOB-10000002",
            "new_scheduled_date": "2024-11-15T10:00:00Z",
            "reschedule_reason": "workmanship_issue",
        }

        # Act
        result = await reschedule_installation_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["job_id"] == "JOB-10000002"
        assert result["status"] == "scheduled"

        # Verify database was updated
        all_jobs = test_db.get_all(InstallationJob)
        job = next(j for j in all_jobs if j.id == "JOB-10000002")
        assert job.status == InstallationJobStatus.SCHEDULED

    @pytest.mark.anyio
    async def test_reschedule_cancelled_job_success(
        self, reschedule_installation_tool, test_db
    ):
        """Test that rescheduling a cancelled job succeeds (policy guard removed)."""
        # Arrange
        request_data = {
            "job_id": "JOB-10000003",
            "new_scheduled_date": "2024-11-20T10:00:00Z",
            "reschedule_reason": "customer_request",
        }

        # Act
        result = await reschedule_installation_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["job_id"] == "JOB-10000003"
        assert result["new_scheduled_date"] == "2024-11-20T10:00:00+00:00"
        # Status remains cancelled since workmanship_issue logic doesn't apply
        assert result["status"] == "cancelled"

        # Verify database was updated
        all_jobs = test_db.get_all(InstallationJob)
        job = next(j for j in all_jobs if j.id == "JOB-10000003")
        assert job.scheduled_date.isoformat() == "2024-11-20T10:00:00+00:00"

    @pytest.mark.anyio
    async def test_reschedule_job_not_found(
        self, reschedule_installation_tool, test_db
    ):
        """Test error when installation job is not found."""
        # Arrange
        request_data = {
            "job_id": "JOB-99999999",
            "new_scheduled_date": "2024-11-20T10:00:00Z",
            "reschedule_reason": "customer_request",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await reschedule_installation_tool.run_with_validation(
                test_db, request_data
            )

        assert "Installation job not found" in str(error.value)
