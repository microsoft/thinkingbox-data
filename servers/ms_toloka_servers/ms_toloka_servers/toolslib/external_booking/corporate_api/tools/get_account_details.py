# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Type

from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ..models import CorporateAccount


class GetAccountDetailsInput(BaseModel):
    corporate_account_id: str = Field(
        ..., description="Corporate account ID.", examples=["CRP-00012345"]
    )


class GetAccountDetailsOutput(BaseModel):
    account_data: CorporateAccount


class GetAccountDetailsTool(Tool):

    @property
    def name(self) -> str:
        return "get_account_details"

    @property
    def description(self) -> str:
        return (
            "Retrieve corporate account details and entitlements. "
            "Fetches complete corporate account information including tier, status, credit limits, and payment terms. "
            "Essential for applying corporate-specific policies and determining booking entitlements."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GetAccountDetailsInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GetAccountDetailsOutput

    async def run(self, db: InMemoryDatabase, request: GetAccountDetailsInput):

        if not request.corporate_account_id.startswith("CRP-"):
            raise self.ExecutionError("Invalid corporate_account_id parameter.")

        accounts = db.get_all(CorporateAccount)
        account = next(
            (
                a
                for a in accounts
                if a.corporate_account_id == request.corporate_account_id
            ),
            None,
        )

        if not account:
            raise self.ExecutionError("Corporate account not found.")

        return GetAccountDetailsOutput(account_data=account)
