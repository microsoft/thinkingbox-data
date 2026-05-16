# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for getting installation job details."""

from typing import Any, Dict, Optional, Type

from ms_toloka_servers import InMemoryDatabase, Tool, get_schema_without_refs
from ms_toloka_servers.toolslib.external_retail_toolset.jobber.models import (
    InstallationJob,
    InstallationJobStatus,
    InstallationServiceType,
)
from pydantic import BaseModel, ConfigDict, Field


class GetInstallationJobInput(BaseModel):
    """Input for get_installation_job tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    job_id: Optional[str] = Field(
        None,
        description="Installation job identifier. Either job_id or order_id must be provided",
        examples=["JOB-00001234"],
    )
    order_id: Optional[str] = Field(
        None,
        description="Order identifier to look up associated installation. "
        "Either job_id or order_id must be provided",
        examples=["ORD-00012345"],
    )


class GetInstallationJobOutput(BaseModel):
    """Output for get_installation_job tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    job_id: str = Field(
        ..., description="Installation job identifier", examples=["JOB-00001234"]
    )
    order_id: str = Field(
        ..., description="Order identifier", examples=["ORD-00012345"]
    )
    customer_id: str = Field(
        ..., description="Customer identifier", examples=["CUS-00012345"]
    )
    service_type: InstallationServiceType = Field(
        ...,
        description="Type of installation service: appliance_basic, appliance_advanced, tv_mounting",
        examples=["appliance_basic"],
    )
    scheduled_date: str = Field(
        ...,
        description="Scheduled appointment date and time",
        examples=["2024-10-25T10:00:00Z"],
    )
    technician_id: Optional[str] = Field(
        None, description="Assigned technician identifier", examples=["TECH-0045"]
    )
    status: InstallationJobStatus = Field(
        ...,
        description="Current job status: scheduled, in_progress, completed, cancelled, issue_reported",
        examples=["scheduled"],
    )
    completion_date: Optional[str] = Field(
        None,
        description="Date when job was completed",
        examples=["2024-10-25T14:30:00Z"],
    )
    service_cost: float = Field(
        ..., description="Cost of installation service", examples=[129.00]
    )


class GetInstallationJobTool(Tool):
    """Tool implementation for retrieving installation job details."""

    @property
    def name(self) -> str:
        return "get_installation_job"

    @property
    def description(self) -> str:
        return (
            "Retrieve installation service details and status. Fetches installation "
            "job information including service type, scheduled date, technician, status, "
            "completion date."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetInstallationJobInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(GetInstallationJobOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetInstallationJobInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetInstallationJobOutput

    async def run(
        self, db: InMemoryDatabase, request: GetInstallationJobInput
    ) -> GetInstallationJobOutput:
        """Retrieve installation job by job_id or order_id."""
        try:
            # Validate that at least one identifier is provided
            if not request.job_id and not request.order_id:
                raise Tool.ExecutionError("Either job_id or order_id must be provided")

            # Get all installation jobs
            all_jobs = db.get_all(InstallationJob)

            # Find matching job
            matching_job = None
            if request.job_id:
                for job in all_jobs:
                    if job.id == request.job_id:
                        matching_job = job
                        break
            elif request.order_id:
                for job in all_jobs:
                    if job.order_id == request.order_id:
                        matching_job = job
                        break

            # If no job found, raise 404 error
            if not matching_job:
                identifier = request.job_id or request.order_id
                raise Tool.ExecutionError(f"Installation job not found: {identifier}")

            # Return installation job details
            return GetInstallationJobOutput(
                job_id=matching_job.id,
                order_id=matching_job.order_id,
                customer_id=matching_job.customer_id,
                service_type=matching_job.service_type,
                scheduled_date=matching_job.scheduled_date.isoformat(),
                technician_id=matching_job.technician_id,
                status=matching_job.status,
                completion_date=(
                    matching_job.completion_date.isoformat()
                    if matching_job.completion_date
                    else None
                ),
                service_cost=matching_job.service_cost,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to retrieve installation job: {str(e)}"
            raise Tool.ExecutionError(error_message)
