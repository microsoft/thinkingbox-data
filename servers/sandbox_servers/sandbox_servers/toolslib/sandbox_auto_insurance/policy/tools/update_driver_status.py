# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Update driver status tool for Policy Administration System."""

from typing import Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Driver, DriverStatus


class UpdateDriverStatusInput(BaseModel):
    """Input model for update_driver_status tool."""

    driver_id: str = Field(
        ..., description="The driver identifier", examples=["DRV-00012345"]
    )
    new_status: DriverStatus = Field(
        ..., description="The new status for the driver", examples=["Removed"]
    )
    effective_date: str = Field(
        ...,
        description="Date the status change becomes effective (YYYY-MM-DD)",
        examples=["2025-01-15"],
    )


class UpdateDriverStatusOutput(BaseModel):
    """Output model for update_driver_status tool."""

    model_config = ConfigDict(extra="forbid")

    driver_id: str = Field(..., description="The updated driver identifier")
    status: str = Field(..., description="The new status")


class UpdateDriverStatusTool(Tool):
    """Tool for updating the status of a driver on a policy."""

    @property
    def name(self) -> str:
        return "update_driver_status"

    @property
    def description(self) -> str:
        return "Changes a driver's status, used to remove drivers or change their exclusion status."

    @property
    def request_model(self) -> Type[BaseModel]:
        return UpdateDriverStatusInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return UpdateDriverStatusOutput

    async def run(
        self, db: InMemoryDatabase, request: UpdateDriverStatusInput
    ) -> UpdateDriverStatusOutput:
        """Update the status of a driver."""
        # Get the driver
        driver = db.get_by_id(Driver, request.driver_id)

        if driver is None:
            raise Tool.ExecutionError(f"Driver with ID '{request.driver_id}' not found")

        # Update status
        driver.status = request.new_status
        driver.effective_date = request.effective_date

        # Set removal date when driver is removed
        if request.new_status == DriverStatus.REMOVED:
            driver.removal_date = request.effective_date

        # Save changes
        db.update(driver)

        return UpdateDriverStatusOutput(driver_id=driver.id, status=driver.status.value)
