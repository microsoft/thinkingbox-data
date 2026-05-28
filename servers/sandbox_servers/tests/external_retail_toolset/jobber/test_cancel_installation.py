# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for cancel_installation tool."""

import pytest
from sandbox_servers.toolslib.external_retail_toolset.jobber.models import (
    InstallationJob,
    InstallationJobStatus,
    InstallationServiceType,
)
from sandbox_servers.toolslib.external_retail_toolset.jobber.tools.cancel_installation import (
    CancelInstallationTool,
)
from sandbox_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestCancelInstallation:
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
            status=InstallationJobStatus.IN_PROGRESS,
            completion_date=None,
            workmanship_warranty_end=None,
            service_cost=249.00,
        )

        db._store = {InstallationJob: [job1, job2, job3]}
        return db

    @pytest.fixture
    def cancel_installation_tool(self):
        """Create an instance of CancelInstallationTool."""
        return CancelInstallationTool()

    @pytest.mark.anyio
    async def test_cancel_installation_success(self, cancel_installation_tool, test_db):
        """Test successfully cancelling an installation."""
        # Arrange
        request_data = {
            "job_id": "JOB-10000001",
            "order_id": "ORD-10000001",
            "cancellation_reason": "customer_wants_ship_only",
        }

        # Act
        result = await cancel_installation_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["job_id"] == "JOB-10000001"
        assert result["status"] == "cancelled"
        assert result["service_cost_refunded"] == 129.00

        # Verify database was updated
        all_jobs = test_db.get_all(InstallationJob)
        job = next(j for j in all_jobs if j.id == "JOB-10000001")
        assert job.status == InstallationJobStatus.CANCELLED

    @pytest.mark.anyio
    async def test_cancel_tv_mounting_installation(
        self, cancel_installation_tool, test_db
    ):
        """Test cancelling TV mounting installation has different shipping cost."""
        # Create a scheduled TV mounting job
        tv_job = InstallationJob(
            id="JOB-10000004",
            order_id="ORD-10000004",
            customer_id="CUS-10000004",
            service_type=InstallationServiceType.TV_MOUNTING,
            scheduled_date="2024-11-10T14:00:00Z",
            technician_id=None,
            status=InstallationJobStatus.SCHEDULED,
            completion_date=None,
            workmanship_warranty_end=None,
            service_cost=99.00,
        )
        test_db._store[InstallationJob].append(tv_job)

        # Arrange
        request_data = {
            "job_id": "JOB-10000004",
            "order_id": "ORD-10000004",
            "cancellation_reason": "customer_wants_ship_only",
        }

        # Act
        result = await cancel_installation_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["service_cost_refunded"] == 99.00

    @pytest.mark.anyio
    async def test_cancel_completed_installation_success(
        self, cancel_installation_tool, test_db
    ):
        """Test that cancelling a completed installation succeeds (policy guard removed)."""
        # Arrange
        request_data = {
            "job_id": "JOB-10000002",
            "order_id": "ORD-10000002",
            "cancellation_reason": "customer_wants_ship_only",
        }

        # Act
        result = await cancel_installation_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["job_id"] == "JOB-10000002"
        assert result["status"] == "cancelled"
        assert result["service_cost_refunded"] == 99.00

        # Verify database was updated
        all_jobs = test_db.get_all(InstallationJob)
        job = next(j for j in all_jobs if j.id == "JOB-10000002")
        assert job.status == InstallationJobStatus.CANCELLED

    @pytest.mark.anyio
    async def test_cancel_in_progress_installation_success(
        self, cancel_installation_tool, test_db
    ):
        """Test that cancelling an in-progress installation succeeds (policy guard removed)."""
        # Arrange
        request_data = {
            "job_id": "JOB-10000003",
            "order_id": "ORD-10000003",
            "cancellation_reason": "customer_cancelled_order",
        }

        # Act
        result = await cancel_installation_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["job_id"] == "JOB-10000003"
        assert result["status"] == "cancelled"
        assert result["service_cost_refunded"] == 249.00

        # Verify database was updated
        all_jobs = test_db.get_all(InstallationJob)
        job = next(j for j in all_jobs if j.id == "JOB-10000003")
        assert job.status == InstallationJobStatus.CANCELLED

    @pytest.mark.anyio
    async def test_cancel_installation_not_found(
        self, cancel_installation_tool, test_db
    ):
        """Test error when installation job is not found."""
        # Arrange
        request_data = {
            "job_id": "JOB-99999999",
            "order_id": "ORD-99999999",
            "cancellation_reason": "customer_wants_ship_only",
        }

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await cancel_installation_tool.run_with_validation(test_db, request_data)

        assert "Installation job not found" in str(error.value)
