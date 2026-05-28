# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ..models import BillingAccount


class GetArrangementHistoryInput(BaseModel):
    """Input parameters for retrieving arrangement history."""

    policy_id: str = Field(
        ...,
        description="Policy ID used to locate the associated billing account.",
        examples=["POL-0012345678"],
    )


class GetArrangementHistoryOutput(BaseModel):
    """Output containing the number of arrangements in the last 12 months."""

    arrangements_12_months: int = Field(
        ..., description="Number of arrangements granted in the last 12 months."
    )


class GetArrangementHistoryTool(Tool):
    """Retrieve the count of payment arrangements for the last 12 months."""

    @property
    def name(self) -> str:
        return "get_arrangement_history"

    @property
    def description(self) -> str:
        return (
            "Returns how many payment arrangements have been granted for the account "
            "in the rolling 12-month period."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetArrangementHistoryInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetArrangementHistoryOutput

    async def run(
        self, db: InMemoryDatabase, request: GetArrangementHistoryInput
    ) -> GetArrangementHistoryOutput:
        """Return the number of arrangements granted in the last 12 months."""

        accounts = db.get_all(BillingAccount)
        account = next((a for a in accounts if a.policy_id == request.policy_id), None)

        if not account:
            raise self.ExecutionError(
                f"No billing account found for policy_id '{request.policy_id}'."
            )

        return GetArrangementHistoryOutput(
            arrangements_12_months=account.arrangements_12_months
        )
