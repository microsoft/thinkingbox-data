# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Check software license type tool."""

from typing import Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
)
from pydantic import BaseModel, ConfigDict, Field

from ..models import LicenseType, SoftwareLicense


class LicenseCheckTypeInput(BaseModel):
    """Input model for license_management_api_check_license_type tool."""

    software_name: str = Field(
        ..., description="Software product name", examples=["Tableau"]
    )


class LicenseCheckTypeOutput(BaseModel):
    """Output model for license_management_api_check_license_type tool."""

    model_config = ConfigDict(extra="forbid")

    license_type: LicenseType = Field(
        ...,
        description="Type of license pool (standard, enterprise, individual, unlimited)",
    )
    license_id: str = Field(..., description="License pool ID (format: LIC-########)")
    annual_cost_per_license: int | None = Field(
        None, description="Annual cost per license in USD (null if not applicable)"
    )


class LicenseCheckTypeTool(Tool):
    """Tool for checking the license pool type for a software product."""

    @property
    def name(self) -> str:
        return "license_management_api_check_license_type"

    @property
    def description(self) -> str:
        return (
            "Returns the license type for a software product, indicating whether it's an unlimited pool, "
            "limited pool, requires individual purchase, or is a standard enterprise license."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return LicenseCheckTypeInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return LicenseCheckTypeOutput

    async def run(
        self, db: InMemoryDatabase, request: LicenseCheckTypeInput
    ) -> LicenseCheckTypeOutput:
        """Check license type for a software product."""
        # Get all software licenses
        all_licenses = db.get_all(SoftwareLicense)

        # Find license by software name (case-insensitive match)
        matching_licenses = [
            lic
            for lic in all_licenses
            if lic.software_name.lower() == request.software_name.lower()
        ]

        if not matching_licenses:
            raise Tool.ExecutionError(
                f"Software not found in license inventory: {request.software_name}"
            )

        license_pool = matching_licenses[0]

        return LicenseCheckTypeOutput(
            license_type=license_pool.license_type,
            license_id=license_pool.id,
            annual_cost_per_license=license_pool.annual_cost_per_license,
        )
