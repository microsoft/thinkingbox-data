# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Optional, Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field


class ValidateVinInput(BaseModel):
    """Input model for VIN validation."""

    vin: str = Field(
        ...,
        description="Vehicle identification number (must be 17 characters).",
        examples=["1HGCM8263A0123456"],
    )


class VinDecodeResult(BaseModel):
    """Decoded VIN information."""

    valid: bool = Field(..., description="Whether the VIN is valid format.")
    year: Optional[int] = Field(None, description="Decoded model year.")
    make: Optional[str] = Field(None, description="Decoded manufacturer.")
    model: Optional[str] = Field(None, description="Decoded model name.")


class ValidateVinTool(Tool):
    """Validate and decode VIN format using deterministic mock logic."""

    @property
    def name(self) -> str:
        return "validate_vin"

    @property
    def description(self) -> str:
        return (
            "Validates VIN format and returns decoded vehicle information. "
            "Mock decoder: deterministic parsing based on VIN pattern."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return ValidateVinInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return VinDecodeResult

    async def run(
        self, db: InMemoryDatabase, request: ValidateVinInput
    ) -> VinDecodeResult:
        vin = request.vin.strip().upper()

        if len(vin) != 17:
            raise self.ExecutionError(
                "Invalid VIN format. VIN must be exactly 17 characters."
            )
        if not vin.isalnum():
            raise self.ExecutionError(
                "Invalid VIN format. VIN must contain only letters and numbers."
            )

        wmi = vin[:3]
        year_code = vin[9]  # Position 10 in VIN (0-indexed as position 9)
        year_map = {
            "A": 2010,
            "B": 2011,
            "C": 2012,
            "D": 2013,
            "E": 2014,
            "F": 2015,
            "G": 2016,
            "H": 2017,
            "J": 2018,
            "K": 2019,
            "L": 2020,
            "M": 2021,
            "N": 2022,
            "P": 2023,
            "R": 2024,
        }
        year = year_map.get(year_code, None)

        make_map = {
            "1HG": "Honda",
            "2HG": "Honda Canada",
            "1FA": "Ford",
            "1FT": "Ford Truck",
            "5YJ": "Tesla",
        }

        make = make_map.get(wmi, None)

        model = None
        if make == "Honda":
            model = "Accord"
        elif make == "Ford":
            model = "Focus"
        elif make == "Ford Truck":
            model = "F-150"
        elif make == "Tesla":
            model = "Model S"

        return VinDecodeResult(
            valid=True,
            year=year,
            make=make,
            model=model,
        )
