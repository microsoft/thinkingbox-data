# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for policy_generate_document_link tool."""

import pytest
from ms_toloka_servers.toolslib.sandbox_auto_insurance.policy import (
    DocumentType,
    GenerateDocumentLinkTool,
    Policy,
    PolicyDocument,
    PolicyStatus,
    State,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def db_with_policy():
    """Create a database with a test policy."""
    db = InMemoryDatabase(data_dir=None)

    # Manually register models
    db._stem_to_model_cls["policies"] = Policy
    db._model_cls_to_stem[Policy] = "policies"
    db._stem_to_model_cls["policy_documents"] = PolicyDocument
    db._model_cls_to_stem[PolicyDocument] = "policy_documents"

    # Add test policy
    policy = Policy(
        id="POL-0012345678",
        customer_id="CUS-00012345",
        state=State.CA,
        status=PolicyStatus.ACTIVE,
        effective_date="2024-01-01",
        expiration_date="2024-12-31",
        renewal_date="2025-01-01",
        named_insured_id="CUS-00012345",
        automatic_extension_days=14,
        at_fault_claims_3_years=0,
        lapse_flag=False,
    )
    db.create(policy)

    return db


@pytest.mark.anyio
async def test_generate_document_link_success(db_with_policy):
    """Test successfully generating a document link."""
    tool = GenerateDocumentLinkTool()

    result = await tool.run_with_validation(
        db_with_policy,
        {
            "policy_id": "POL-0012345678",
            "document_type": "proof_of_insurance",
            "ticket_id": "123",
            "expiration_date": "2024-01-16T10:05:00Z",
        },
    )

    assert "document_id" in result
    assert result["document_id"].startswith("DOC-")
    assert "url" in result
    assert result["url"].startswith("https://portal.horizonshield.com/docs/secure/")
    assert result["expires_at"] == "2024-01-16T10:05:00Z"

    # Verify document was created in database
    documents = db_with_policy.get_all(PolicyDocument)
    assert len(documents) == 1
    assert documents[0].policy_id == "POL-0012345678"
    assert documents[0].ticket_id == "123"
    assert documents[0].document_type == DocumentType.PROOF_OF_INSURANCE
    assert documents[0].expires_at == "2024-01-16T10:05:00Z"


@pytest.mark.anyio
async def test_generate_document_link_declarations_page(db_with_policy):
    """Test generating a declarations page document link."""
    tool = GenerateDocumentLinkTool()

    result = await tool.run_with_validation(
        db_with_policy,
        {
            "policy_id": "POL-0012345678",
            "document_type": "declarations_page",
            "ticket_id": "456",
            "expiration_date": "2024-02-01T00:00:00Z",
        },
    )

    assert result["document_id"].startswith("DOC-")
    assert "url" in result

    # Verify correct document type
    documents = db_with_policy.get_all(PolicyDocument)
    assert len(documents) == 1
    assert documents[0].document_type == DocumentType.DECLARATIONS_PAGE


@pytest.mark.anyio
async def test_generate_document_link_id_card(db_with_policy):
    """Test generating an ID card document link."""
    tool = GenerateDocumentLinkTool()

    result = await tool.run_with_validation(
        db_with_policy,
        {
            "policy_id": "POL-0012345678",
            "document_type": "id_card",
            "ticket_id": "789",
            "expiration_date": "2024-03-01T12:00:00Z",
        },
    )

    assert result["document_id"].startswith("DOC-")

    # Verify correct document type
    documents = db_with_policy.get_all(PolicyDocument)
    assert len(documents) == 1
    assert documents[0].document_type == DocumentType.ID_CARD


@pytest.mark.anyio
async def test_generate_document_link_policy_not_found(db_with_policy):
    """Test generating document link for non-existent policy fails."""
    tool = GenerateDocumentLinkTool()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_policy,
            {
                "policy_id": "POL-9999999999",
                "document_type": "proof_of_insurance",
                "ticket_id": "123",
                "expiration_date": "2024-01-16T10:05:00Z",
            },
        )

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_generate_document_link_invalid_expiration_format(db_with_policy):
    """Test generating document link with invalid expiration date format fails."""
    tool = GenerateDocumentLinkTool()

    with pytest.raises(Exception) as exc_info:
        await tool.run_with_validation(
            db_with_policy,
            {
                "policy_id": "POL-0012345678",
                "document_type": "proof_of_insurance",
                "ticket_id": "123",
                "expiration_date": "invalid-date-format",  # Completely invalid format
            },
        )

    assert "invalid" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_generate_document_link_deterministic_url(db_with_policy):
    """Test that URL generation is deterministic based on input."""
    tool = GenerateDocumentLinkTool()

    result1 = await tool.run_with_validation(
        db_with_policy,
        {
            "policy_id": "POL-0012345678",
            "document_type": "proof_of_insurance",
            "ticket_id": "123",
            "expiration_date": "2024-01-16T10:05:00Z",
        },
    )

    result2 = await tool.run_with_validation(
        db_with_policy,
        {
            "policy_id": "POL-0012345678",
            "document_type": "declarations_page",
            "ticket_id": "456",
            "expiration_date": "2024-01-17T10:05:00Z",
        },
    )

    # URLs should be different for different inputs
    assert result1["url"] != result2["url"]

    # Both should be valid secure URLs
    assert result1["url"].startswith("https://portal.horizonshield.com/docs/secure/")
    assert result2["url"].startswith("https://portal.horizonshield.com/docs/secure/")

    # Document IDs should increment
    documents = db_with_policy.get_all(PolicyDocument)
    assert len(documents) == 2


@pytest.mark.anyio
async def test_generate_document_link_multiple_documents(db_with_policy):
    """Test generating multiple document links for the same policy."""
    tool = GenerateDocumentLinkTool()

    # Generate first document
    result1 = await tool.run_with_validation(
        db_with_policy,
        {
            "policy_id": "POL-0012345678",
            "document_type": "proof_of_insurance",
            "ticket_id": "100",
            "expiration_date": "2024-01-16T10:00:00Z",
        },
    )

    # Generate second document
    result2 = await tool.run_with_validation(
        db_with_policy,
        {
            "policy_id": "POL-0012345678",
            "document_type": "proof_of_insurance",
            "ticket_id": "101",
            "expiration_date": "2024-01-17T10:00:00Z",
        },
    )

    # Both should succeed with unique IDs
    assert result1["document_id"] != result2["document_id"]
    assert result1["url"] != result2["url"]

    # Verify both documents in database
    documents = db_with_policy.get_all(PolicyDocument)
    assert len(documents) == 2
