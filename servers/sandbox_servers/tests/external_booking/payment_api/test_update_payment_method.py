# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for update_payment_method tool."""

import pytest
from sandbox_servers.toolslib.external_booking.payment_api.tools.update_payment_method import (
    UpdatePaymentMethod,
)
from sandbox_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.mark.anyio
async def test_update_payment_method_success(db):
    """Test successfully updating payment method."""
    tool = UpdatePaymentMethod()

    result = await tool.run_with_validation(
        db, {"customer_id": "CUS-00000001", "new_payment_method": "card_1234567890"}
    )

    assert "success" in result
    assert result["success"] is True
    assert "payment_method_last4" in result


@pytest.mark.anyio
async def test_update_payment_method_returns_last4(db):
    """Test that last 4 digits are returned."""
    tool = UpdatePaymentMethod()

    result = await tool.run_with_validation(
        db, {"customer_id": "CUS-00000001", "new_payment_method": "card_1234567890"}
    )

    assert result["payment_method_last4"] == "7890"


@pytest.mark.anyio
async def test_update_payment_method_short_token(db):
    """Test updating with short payment token."""
    tool = UpdatePaymentMethod()

    result = await tool.run_with_validation(
        db, {"customer_id": "CUS-00000001", "new_payment_method": "tok"}
    )

    assert result["success"] is True
    # For tokens shorter than 4 chars, should return the token itself or ****
    assert result["payment_method_last4"] in ["tok", "****"]


@pytest.mark.anyio
async def test_update_payment_method_long_token(db):
    """Test updating with long payment token."""
    tool = UpdatePaymentMethod()

    result = await tool.run_with_validation(
        db,
        {"customer_id": "CUS-00000001", "new_payment_method": "tok_1234567890abcdef"},
    )

    assert result["payment_method_last4"] == "cdef"


@pytest.mark.anyio
async def test_update_payment_method_different_customers(db):
    """Test updating payment methods for different customers."""
    tool = UpdatePaymentMethod()

    result1 = await tool.run_with_validation(
        db,
        {"customer_id": "CUS-00000001", "new_payment_method": "card_1111222233334444"},
    )

    result2 = await tool.run_with_validation(
        db,
        {"customer_id": "CUS-00000002", "new_payment_method": "card_5555666677778888"},
    )

    assert result1["success"] is True
    assert result2["success"] is True
    assert result1["payment_method_last4"] == "4444"
    assert result2["payment_method_last4"] == "8888"


@pytest.mark.anyio
async def test_update_payment_method_numeric_token(db):
    """Test updating with numeric token."""
    tool = UpdatePaymentMethod()

    result = await tool.run_with_validation(
        db, {"customer_id": "CUS-00000001", "new_payment_method": "4242424242424242"}
    )

    assert result["payment_method_last4"] == "4242"


@pytest.mark.anyio
async def test_update_payment_method_alphanumeric_token(db):
    """Test updating with alphanumeric token."""
    tool = UpdatePaymentMethod()

    result = await tool.run_with_validation(
        db, {"customer_id": "CUS-00000001", "new_payment_method": "pm_abc123xyz789"}
    )

    assert result["payment_method_last4"] == "z789"


@pytest.mark.anyio
async def test_update_payment_method_customer_not_found(db):
    """Test updating payment method for non-existent customer."""
    tool = UpdatePaymentMethod()

    with pytest.raises(Tool.ExecutionError, match="Customer not found: CUS-99999999"):
        await tool.run_with_validation(
            db, {"customer_id": "CUS-99999999", "new_payment_method": "card_1234567890"}
        )
