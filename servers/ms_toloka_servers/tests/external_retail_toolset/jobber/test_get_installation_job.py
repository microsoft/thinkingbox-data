# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for get_installation_job tool."""

import pytest
from ms_toloka_servers.toolslib.external_retail_toolset.jobber.models import (
    InstallationJob,
    InstallationJobStatus,
    InstallationServiceType,
)
from ms_toloka_servers.toolslib.external_retail_toolset.jobber.tools.get_installation_job import (
    GetInstallationJobTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import InMemoryDatabase, Tool


class TestGetInstallationJob:
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

        db._store = {InstallationJob: [job1, job2]}
        return db

    @pytest.fixture
    def empty_db(self):
        """Create an empty test database."""
        db = InMemoryDatabase.__new__(InMemoryDatabase)
        db._stem_to_model_cls = {"installation_job": InstallationJob}
        db._model_cls_to_stem = {InstallationJob: "installation_job"}
        db._store = {InstallationJob: []}
        return db

    @pytest.fixture
    def get_installation_job_tool(self):
        """Create an instance of GetInstallationJobTool."""
        return GetInstallationJobTool()

    @pytest.mark.anyio
    async def test_get_installation_job_by_job_id_success(
        self, get_installation_job_tool, test_db
    ):
        """Test successfully getting installation job by job_id."""
        # Arrange
        request_data = {"job_id": "JOB-10000001"}

        # Act
        result = await get_installation_job_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["job_id"] == "JOB-10000001"
        assert result["order_id"] == "ORD-10000001"
        assert result["customer_id"] == "CUS-10000001"
        assert result["service_type"] == "appliance_basic"
        assert result["status"] == "scheduled"
        assert result["service_cost"] == 129.00
        assert result["technician_id"] == "TECH-0045"

    @pytest.mark.anyio
    async def test_get_installation_job_by_order_id_success(
        self, get_installation_job_tool, test_db
    ):
        """Test successfully getting installation job by order_id."""
        # Arrange
        request_data = {"order_id": "ORD-10000002"}

        # Act
        result = await get_installation_job_tool.run_with_validation(
            test_db, request_data
        )

        # Assert
        assert result["job_id"] == "JOB-10000002"
        assert result["order_id"] == "ORD-10000002"
        assert result["service_type"] == "tv_mounting"
        assert result["status"] == "completed"
        assert result["completion_date"] is not None

    @pytest.mark.anyio
    async def test_get_installation_job_no_identifier(
        self, get_installation_job_tool, test_db
    ):
        """Test error when neither job_id nor order_id is provided."""
        # Arrange
        request_data = {}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_installation_job_tool.run_with_validation(test_db, request_data)

        assert "Either job_id or order_id must be provided" in str(error.value)

    @pytest.mark.anyio
    async def test_get_installation_job_not_found_by_job_id(
        self, get_installation_job_tool, test_db
    ):
        """Test error when installation job is not found by job_id."""
        # Arrange
        request_data = {"job_id": "JOB-99999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_installation_job_tool.run_with_validation(test_db, request_data)

        assert "Installation job not found" in str(error.value)

    @pytest.mark.anyio
    async def test_get_installation_job_not_found_by_order_id(
        self, get_installation_job_tool, test_db
    ):
        """Test error when installation job is not found by order_id."""
        # Arrange
        request_data = {"order_id": "ORD-99999999"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_installation_job_tool.run_with_validation(test_db, request_data)

        assert "Installation job not found" in str(error.value)

    @pytest.mark.anyio
    async def test_get_installation_job_empty_database(
        self, get_installation_job_tool, empty_db
    ):
        """Test getting installation job from empty database."""
        # Arrange
        request_data = {"job_id": "JOB-10000001"}

        # Act & Assert
        with pytest.raises(Tool.ExecutionError) as error:
            await get_installation_job_tool.run_with_validation(empty_db, request_data)

        assert "Installation job not found" in str(error.value)
