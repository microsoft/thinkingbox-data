# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for rescheduling installation appointments."""

from datetime import datetime
from typing import Any, Dict, Type

from sandbox_servers import InMemoryDatabase, Tool, get_schema_without_refs
from sandbox_servers.toolslib.external_retail_toolset.jobber.models import (
    InstallationJob,
    InstallationJobStatus,
    InstallationRescheduleReason,
)
from pydantic import BaseModel, ConfigDict, Field


class RescheduleInstallationInput(BaseModel):
    """Input for reschedule_installation tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    job_id: str = Field(
        ..., description="Installation job identifier", examples=["JOB-00001234"]
    )
    new_scheduled_date: datetime = Field(
        ...,
        description="New appointment date and time",
        examples=["2024-10-30T14:00:00Z"],
    )
    reschedule_reason: InstallationRescheduleReason = Field(
        ...,
        description=(
            "Reason for rescheduling: customer_request, workmanship_issue, "
            "technician_unavailable, weather_delay"
        ),
        examples=["customer_request"],
    )


class RescheduleInstallationOutput(BaseModel):
    """Output for reschedule_installation tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    job_id: str = Field(
        ..., description="Installation job identifier", examples=["JOB-00001234"]
    )
    old_scheduled_date: str = Field(
        ..., description="Previous scheduled date", examples=["2024-10-25T10:00:00Z"]
    )
    new_scheduled_date: str = Field(
        ..., description="New scheduled date", examples=["2024-10-30T14:00:00Z"]
    )
    status: InstallationJobStatus = Field(
        ..., description="Updated job status", examples=["scheduled"]
    )


class RescheduleInstallationTool(Tool):
    """Tool implementation for rescheduling installation appointments."""

    @property
    def name(self) -> str:
        return "reschedule_installation"

    @property
    def description(self) -> str:
        return (
            "Reschedule an installation appointment to a new date. Updates the "
            "scheduled date for an installation job."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(RescheduleInstallationInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(RescheduleInstallationOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return RescheduleInstallationInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return RescheduleInstallationOutput

    async def run(
        self, db: InMemoryDatabase, request: RescheduleInstallationInput
    ) -> RescheduleInstallationOutput:
        """Reschedule an installation appointment."""
        try:
            # Get all installation jobs
            all_jobs = db.get_all(InstallationJob)

            # Find matching job
            matching_job = None
            for job in all_jobs:
                if job.id == request.job_id:
                    matching_job = job
                    break

            # If no job found, raise 404 error
            if not matching_job:
                raise Tool.ExecutionError(
                    f"Installation job not found: {request.job_id}"
                )

            # Store old scheduled date
            old_scheduled_date = matching_job.scheduled_date

            # Handle workmanship issue reschedule for completed jobs
            if (
                request.reschedule_reason
                == InstallationRescheduleReason.WORKMANSHIP_ISSUE
                and matching_job.status == InstallationJobStatus.COMPLETED
            ):
                # Set status to issue_reported first, then back to scheduled
                # (simulating corrective service scheduling)
                matching_job.status = InstallationJobStatus.SCHEDULED

            # Update scheduled date
            matching_job.scheduled_date = request.new_scheduled_date

            # Update job in database
            db.update(matching_job)

            # Return result
            return RescheduleInstallationOutput(
                job_id=matching_job.id,
                old_scheduled_date=old_scheduled_date.isoformat(),
                new_scheduled_date=matching_job.scheduled_date.isoformat(),
                status=matching_job.status,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to reschedule installation: {str(e)}"
            raise Tool.ExecutionError(error_message)
