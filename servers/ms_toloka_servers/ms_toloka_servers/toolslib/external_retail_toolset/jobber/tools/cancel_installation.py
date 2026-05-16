# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for cancelling installation appointments."""

from typing import Any, Dict, Type

from ms_toloka_servers import InMemoryDatabase, Tool, get_schema_without_refs
from ms_toloka_servers.toolslib.external_retail_toolset.jobber.models import (
    InstallationCancellationReason,
    InstallationJob,
    InstallationJobStatus,
)
from pydantic import BaseModel, ConfigDict, Field


class CancelInstallationInput(BaseModel):
    """Input for cancel_installation tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    job_id: str = Field(
        ..., description="Installation job identifier", examples=["JOB-00001234"]
    )
    order_id: str = Field(
        ..., description="Associated order identifier", examples=["ORD-00012345"]
    )
    cancellation_reason: InstallationCancellationReason = Field(
        ...,
        description=(
            "Reason for cancellation: customer_wants_ship_only, "
            "customer_cancelled_order, product_incompatible, address_inaccessible"
        ),
        examples=["customer_wants_ship_only"],
    )


class CancelInstallationOutput(BaseModel):
    """Output for cancel_installation tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    job_id: str = Field(
        ..., description="Installation job identifier", examples=["JOB-00001234"]
    )
    status: InstallationJobStatus = Field(
        ..., description="Updated job status", examples=["cancelled"]
    )
    service_cost_refunded: float = Field(
        ...,
        description="Installation service cost that will be refunded",
        examples=[129.00],
    )


class CancelInstallationTool(Tool):
    """Tool implementation for cancelling installation appointments."""

    @property
    def name(self) -> str:
        return "cancel_installation"

    @property
    def description(self) -> str:
        return (
            "Cancel a scheduled installation appointment. Cancels an installation "
            "job and updates order to remove installation service reference."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CancelInstallationInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(CancelInstallationOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return CancelInstallationInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return CancelInstallationOutput

    async def run(
        self, db: InMemoryDatabase, request: CancelInstallationInput
    ) -> CancelInstallationOutput:
        """Cancel an installation appointment."""
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

            # Store service cost for refund
            service_cost_refunded = matching_job.service_cost

            # Update job status to cancelled
            matching_job.status = InstallationJobStatus.CANCELLED
            db.update(matching_job)

            # Return result
            return CancelInstallationOutput(
                job_id=matching_job.id,
                status=matching_job.status,
                service_cost_refunded=service_cost_refunded,
            )

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to cancel installation: {str(e)}"
            raise Tool.ExecutionError(error_message)
