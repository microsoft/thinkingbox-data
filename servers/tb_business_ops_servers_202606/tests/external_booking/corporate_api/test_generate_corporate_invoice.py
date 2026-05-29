# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pathlib

import pytest
from tb_business_ops_servers_202606.toolslib.external_booking.corporate_api.tools.generate_corporate_invoice import (
    GenerateCorporateInvoiceTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.fixture
def tool():
    return GenerateCorporateInvoiceTool()


@pytest.mark.anyio
async def test_generate_invoice_success(tool, db):
    request = {
        "booking_reference": "BKG-00012349",
        "corporate_account_id": "CRP-00012345",
    }

    result = await tool.run_with_validation(db, request)

    assert isinstance(result, dict)

    assert "invoice_id" in result
    assert "invoice_url" in result
    assert "payment_terms" in result

    assert result["payment_terms"] == "Net 60"

    assert result["invoice_url"] == (
        "https://staybridge.com/corporate-invoices/" "CRP-00012345-BKG-00012349.pdf"
    )

    # Verify deterministic invoice_id generation
    assert result["invoice_id"] == "INV-00012349-00012345"


@pytest.mark.anyio
async def test_generate_invoice_account_mismatch(tool, db):
    request = {
        "booking_reference": "BKG-00012345",
        "corporate_account_id": "CRP-00099999",
    }

    with pytest.raises(tool.ExecutionError, match="not associated"):
        await tool.run_with_validation(db, request)


@pytest.mark.anyio
async def test_generate_invoice_booking_not_found(tool, db):
    request = {
        "booking_reference": "BKG-DOESNT-EXIST",
        "corporate_account_id": "CRP-00012345",
    }

    with pytest.raises(tool.ExecutionError, match="Booking"):
        await tool.run_with_validation(db, request)


@pytest.mark.anyio
async def test_generate_invoice_deterministic(tool, db):
    """Test that invoice_id generation is deterministic."""
    request = {
        "booking_reference": "BKG-00012349",
        "corporate_account_id": "CRP-00012345",
    }

    # Generate invoice twice with same parameters
    result1 = await tool.run_with_validation(db, request)
    result2 = await tool.run_with_validation(db, request)

    # Should generate the same invoice_id both times
    assert result1["invoice_id"] == result2["invoice_id"]
    assert result1["invoice_id"] == "INV-00012349-00012345"
