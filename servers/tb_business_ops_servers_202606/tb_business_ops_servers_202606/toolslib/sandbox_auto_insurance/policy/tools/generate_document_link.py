# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Generate document link tool for Policy Administration System."""

import hashlib
from datetime import datetime, timezone
from typing import Type

from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field

from ..models import DocumentType, Policy, PolicyDocument


class GenerateDocumentLinkInput(BaseModel):
    """Input model for policy_generate_document_link tool."""

    policy_id: str = Field(
        ..., description="ID of the policy.", examples=["POL-0012345678"]
    )
    document_type: DocumentType = Field(
        ...,
        description="Type of document to generate.",
        examples=["proof_of_insurance"],
    )
    ticket_id: str = Field(
        ...,
        description="The Zendesk ticket ID associated with this request for audit purposes.",
        examples=["1"],
    )
    expiration_date: str = Field(
        ...,
        description="Date and time when the link expires (ISO 8601 format).",
        examples=["2024-01-16T10:05:00Z"],
    )


class GenerateDocumentLinkOutput(BaseModel):
    """Output model for policy_generate_document_link tool."""

    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(
        ..., description="The newly created document record identifier"
    )
    url: str = Field(..., description="Secure URL to access the document")
    expires_at: str = Field(..., description="Timestamp when the link expires")


class GenerateDocumentLinkTool(Tool):
    """Tool for generating temporary, secure links for policy documents."""

    @property
    def name(self) -> str:
        return "generate_document_link"

    @property
    def description(self) -> str:
        return (
            "Generates a temporary, secure link for policy documents (e.g., Proof of Insurance) "
            "to be shared with the customer."
        )

    @property
    def request_model(self) -> Type[BaseModel]:
        return GenerateDocumentLinkInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return GenerateDocumentLinkOutput

    async def run(
        self, db: InMemoryDatabase, request: GenerateDocumentLinkInput
    ) -> GenerateDocumentLinkOutput:
        """Generate a secure document link for a policy."""
        # Check if policy exists
        policy = db.get_by_id(Policy, request.policy_id)
        if policy is None:
            raise Tool.ExecutionError(f"Policy with ID '{request.policy_id}' not found")

        # Validate expiration_date format
        try:
            datetime.fromisoformat(request.expiration_date.replace("Z", "+00:00"))
        except ValueError:
            raise Tool.ExecutionError(
                f"Invalid expiration_date format: '{request.expiration_date}'. "
                "Expected ISO 8601 format (e.g., '2024-01-16T10:05:00Z')"
            )

        # Generate deterministic secure URL based only on input parameters (without hashing for transparency)
        # This ensures the same URL is generated for the same policy_id, document_type, and ticket_id
        # Format: policyId_documentType_ticketId (readable and verifiable)
        url_suffix = (
            f"{request.policy_id}_{request.document_type.value}_{request.ticket_id}"
        )
        secure_url = f"https://portal.horizonshield.com/docs/secure/{url_suffix}"

        # Generate new document ID deterministically based on the same inputs
        # Use hash for ID to keep it reasonably short
        id_seed = f"{request.policy_id}_{request.document_type}_{request.ticket_id}"
        id_hash = hashlib.sha256(id_seed.encode()).hexdigest()[:8].upper()
        new_id = f"DOC-2-{id_hash}"

        # Check if this exact document was already generated
        existing_doc = db.get_by_id(PolicyDocument, new_id)
        if existing_doc is not None:
            # Return the existing document link instead of creating duplicate
            return GenerateDocumentLinkOutput(
                document_id=existing_doc.id,
                url=existing_doc.url,
                expires_at=existing_doc.expires_at,
            )

        # Use expiration date as created_at for determinism
        created_at = request.expiration_date

        # Create new document record
        new_document = PolicyDocument(
            id=new_id,
            policy_id=request.policy_id,
            ticket_id=request.ticket_id,
            document_type=request.document_type,
            url=secure_url,
            created_at=created_at,
            expires_at=request.expiration_date,
        )

        # Save to database
        db.create(new_document)

        return GenerateDocumentLinkOutput(
            document_id=new_id, url=secure_url, expires_at=request.expiration_date
        )
