# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Add driver tool for Policy Administration System."""

import hashlib
from typing import Optional, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import Driver, DriverStatus, Policy


class AddDriverInput(BaseModel):
    """Input model for add_driver tool."""

    policy_id: str = Field(
        ..., description="The policy identifier", examples=["POL-0012345678"]
    )
    name: str = Field(..., description="Driver's full name", examples=["John Smith Jr"])
    date_of_birth: str = Field(
        ..., description="Date of birth (YYYY-MM-DD)", examples=["1995-03-15"]
    )
    license_number: Optional[str] = Field(
        None, description="Driver's license number", examples=["D1234567"]
    )
    license_state: Optional[str] = Field(
        None, description="State that issued the license", examples=["CA"]
    )
    relationship: str = Field(
        ..., description="Relationship to policyholder", examples=["Son"]
    )
    status: DriverStatus = Field(
        ..., description="Driver's status on policy", examples=["Rated"]
    )
    effective_date: str = Field(
        ..., description="Date driver is added (YYYY-MM-DD)", examples=["2025-01-15"]
    )
    uw_pending: Optional[bool] = Field(
        False, description="Whether underwriting review is pending", examples=[False]
    )
    exclusion_form_required: Optional[bool] = Field(
        False, description="Whether exclusion form is required", examples=[False]
    )


class AddDriverOutput(BaseModel):
    """Output model for add_driver tool."""

    model_config = ConfigDict(extra="forbid")

    driver_id: str = Field(..., description="The newly created driver identifier")
    status: str = Field(..., description="The driver's status on the policy")


class AddDriverTool(Tool):
    """Tool for adding a new driver to an existing policy."""

    @property
    def name(self) -> str:
        return "add_driver"

    @property
    def description(self) -> str:
        return (
            "Creates a new driver record on the policy. Driver can be added as rated or excluded "
            "based on state rules and risk factors."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return AddDriverInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return AddDriverOutput

    async def run(
        self, db: InMemoryDatabase, request: AddDriverInput
    ) -> AddDriverOutput:
        """Add a new driver to a policy."""
        # Check if policy exists
        policy = db.get_by_id(Policy, request.policy_id)
        if policy is None:
            raise Tool.ExecutionError(f"Policy with ID '{request.policy_id}' not found")

        # Check if driver with same name and DOB already exists on this policy
        all_drivers = db.get_all(Driver)
        for d in all_drivers:
            if (
                d.policy_id == request.policy_id
                and d.name == request.name
                and d.date_of_birth == request.date_of_birth
            ):
                raise Tool.ExecutionError(
                    f"Driver with name '{request.name}' and DOB '{request.date_of_birth}' already exists on this policy"
                )

        # Generate deterministic driver ID based on policy_id, name, and date_of_birth
        id_seed = f"{request.policy_id}_{request.name}_{request.date_of_birth}"
        id_hash = hashlib.sha256(id_seed.encode()).hexdigest()[:8].upper()
        new_id = f"DRV-2-{id_hash}"

        # Check if this driver was already added (idempotency)
        existing_driver = db.get_by_id(Driver, new_id)
        if existing_driver is not None:
            return AddDriverOutput(
                driver_id=existing_driver.id, status=existing_driver.status.value
            )

        # Create new driver
        new_driver = Driver(
            id=new_id,
            policy_id=request.policy_id,
            name=request.name,
            date_of_birth=request.date_of_birth,
            license_number=request.license_number,
            license_state=request.license_state,
            relationship=request.relationship,
            status=request.status,
            effective_date=request.effective_date,
            is_named_insured=False,
            is_co_insured=False,
            uw_pending=request.uw_pending or False,
            exclusion_form_required=request.exclusion_form_required or False,
        )

        # Save to database
        db.create(new_driver)

        return AddDriverOutput(driver_id=new_id, status=request.status.value)
