# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Optional, Type

from sandbox_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from sandbox_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, Field

from ...corporate_api.models import CorporateAccount, CorporateAccountTier


class LookupCorporateAccountIdInput(BaseModel):
    """Input model for corporate account lookups."""

    company_name: Optional[str] = Field(
        None,
        description="Company name for search (case-insensitive contains match).",
        examples=["Acme Corporation"],
    )

    customer_email: Optional[str] = Field(
        None,
        description="Customer email to extract domain for corporate match.",
        examples=["john.doe@acme.com"],
    )


class LookupCorporateAccountIdOutput(BaseModel):
    """Corporate account lookup result."""

    corporate_account_id: Optional[str] = Field(
        None, description="Corporate account ID if found."
    )

    company_name: Optional[str] = Field(
        None, description="Company name for confirmation."
    )

    account_tier: Optional[CorporateAccountTier] = Field(
        None, description="Account tier: enterprise, mid_market, or small_business."
    )


class LookupCorporateAccountIdTool(Tool):
    """Look up corporate account by company name or email domain."""

    @property
    def name(self) -> str:
        return "lookup_corporate_account_id"

    @property
    def summary(self) -> str:
        return "Look up corporate account ID from company name or customer email."

    @property
    def description(self) -> str:
        return (
            "Searches for corporate account by company name or employee email to retrieve "
            "corporate_account_id. Used when customer mentions corporate affiliation "
            "without providing account ID."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return LookupCorporateAccountIdInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return LookupCorporateAccountIdOutput

    async def run(
        self, db: InMemoryDatabase, request: LookupCorporateAccountIdInput
    ) -> LookupCorporateAccountIdOutput:

        company_name = request.company_name
        customer_email = request.customer_email

        if not company_name and not customer_email:
            raise self.ExecutionError(
                "Invalid parameters: provide company_name or customer_email."
            )

        accounts = db.get_all(CorporateAccount)

        matches = []

        if company_name:
            cn = company_name.lower()
            matches = [a for a in accounts if cn in a.company_name.lower()]

        if customer_email:
            try:
                email_domain = customer_email.split("@", 1)[1].lower()
            except Exception:
                raise self.ExecutionError("Invalid email format.")

            domain_matches = [
                a
                for a in accounts
                if a.contact_email
                and a.contact_email.split("@")[-1].lower() == email_domain
            ]

            for acc in domain_matches:
                if acc not in matches:
                    matches.append(acc)

        if not matches:
            raise self.ExecutionError("No corporate account found matching criteria.")

        acc = matches[0]

        return LookupCorporateAccountIdOutput(
            corporate_account_id=acc.corporate_account_id,
            company_name=acc.company_name,
            account_tier=acc.account_tier,
        )
