# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for Okta Security API - Execute Action Tool."""

from datetime import datetime, timedelta

import pytest
from ms_toloka_servers.toolslib.sandbox_neobank_support.main.models import (
    OktaSecurityAudit,
    OktaSecurityOperation,
)
from ms_toloka_servers.toolslib.sandbox_neobank_support.main.tools.okta_security_api_execute_action import (
    FIXED_CURRENT_TIME,
    OktaSecurityExecuteActionInput,
    OktaSecurityExecuteActionTool,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    STUB_DOMAIN,
    InMemoryDatabase,
    Tool,
    UnstableField,
)


@pytest.mark.anyio
async def test_execute_action_unlock_account(db: InMemoryDatabase):
    """Test unlocking an account."""
    tool = OktaSecurityExecuteActionTool()
    request = OktaSecurityExecuteActionInput(
        email="marcus.thompson@vdb.com",
        operation=OktaSecurityOperation.UNLOCK_ACCOUNT,
        ticket_id="TCK-00012345",
    )

    result = await tool.run(db, request)

    assert result.success is True
    assert result.audit_id.startswith("OSA-")
    assert result.error_message is None

    # Verify audit record was created with base fields only
    audit_record = db.get_by_id(OktaSecurityAudit, result.audit_id)
    assert audit_record is not None
    assert audit_record.operation == OktaSecurityOperation.UNLOCK_ACCOUNT
    assert audit_record.performed_by == "system"
    assert audit_record.success is True
    assert audit_record.ticket_id == "TCK-00012345"
    # These should be None for unlock_account operation
    assert audit_record.bypass_duration_hours is None
    assert audit_record.bypass_expires_at is None
    assert audit_record.mfa_device_id is None


@pytest.mark.anyio
async def test_execute_action_set_temporary_bypass(db: InMemoryDatabase):
    """Test setting temporary MFA bypass with bypass_duration_hours."""
    tool = OktaSecurityExecuteActionTool()
    request = OktaSecurityExecuteActionInput(
        email="maria.garcia@vdb.com",
        operation=OktaSecurityOperation.SET_TEMPORARY_BYPASS,
        bypass_duration_hours=4,
        ticket_id="TCK-00012346",
    )

    result = await tool.run(db, request)

    assert result.success is True
    assert result.audit_id.startswith("OSA-")

    # Verify audit record includes bypass-specific fields
    audit_record = db.get_by_id(OktaSecurityAudit, result.audit_id)
    assert audit_record is not None
    assert audit_record.operation == OktaSecurityOperation.SET_TEMPORARY_BYPASS
    assert audit_record.bypass_duration_hours == 4
    assert audit_record.bypass_expires_at is not None
    expected_expiry = FIXED_CURRENT_TIME + timedelta(hours=4)
    assert audit_record.bypass_expires_at == expected_expiry
    assert audit_record.mfa_device_id is None


@pytest.mark.anyio
async def test_execute_action_add_mfa_device(db: InMemoryDatabase):
    """Test adding MFA device."""
    tool = OktaSecurityExecuteActionTool()
    request = OktaSecurityExecuteActionInput(
        email="sophia.davis@vdb.com",
        operation=OktaSecurityOperation.ADD_MFA_DEVICE,
        mfa_device_id="MFA-12345",
        ticket_id="TCK-00012347",
    )

    result = await tool.run(db, request)

    assert result.success is True
    assert result.audit_id.startswith("OSA-")

    # Verify audit record includes mfa_device_id
    audit_record = db.get_by_id(OktaSecurityAudit, result.audit_id)
    assert audit_record is not None
    assert audit_record.operation == OktaSecurityOperation.ADD_MFA_DEVICE
    assert audit_record.mfa_device_id == "MFA-12345"
    assert audit_record.bypass_duration_hours is None
    assert audit_record.bypass_expires_at is None


@pytest.mark.anyio
async def test_execute_action_remove_mfa_device(db: InMemoryDatabase):
    """Test removing MFA device."""
    tool = OktaSecurityExecuteActionTool()
    request = OktaSecurityExecuteActionInput(
        email="emma.wilson@vdb.com",
        operation=OktaSecurityOperation.REMOVE_MFA_DEVICE,
        mfa_device_id="MFA-67890",
        ticket_id="TCK-00012348",
    )

    result = await tool.run(db, request)

    assert result.success is True
    assert result.audit_id.startswith("OSA-")

    # Verify audit record includes mfa_device_id
    audit_record = db.get_by_id(OktaSecurityAudit, result.audit_id)
    assert audit_record is not None
    assert audit_record.operation == OktaSecurityOperation.REMOVE_MFA_DEVICE
    assert audit_record.mfa_device_id == "MFA-67890"
    assert audit_record.bypass_duration_hours is None
    assert audit_record.bypass_expires_at is None


@pytest.mark.anyio
async def test_execute_action_force_password_reset(db: InMemoryDatabase):
    """Test forcing password reset - should only have base fields."""
    tool = OktaSecurityExecuteActionTool()
    request = OktaSecurityExecuteActionInput(
        email="alex.taylor@vdb.com",
        operation=OktaSecurityOperation.FORCE_PASSWORD_RESET,
        ticket_id="TCK-00012349",
    )

    result = await tool.run(db, request)

    assert result.success is True
    assert result.audit_id.startswith("OSA-")

    # Verify audit record has base fields only
    audit_record = db.get_by_id(OktaSecurityAudit, result.audit_id)
    assert audit_record is not None
    assert audit_record.operation == OktaSecurityOperation.FORCE_PASSWORD_RESET
    assert audit_record.bypass_duration_hours is None
    assert audit_record.bypass_expires_at is None
    assert audit_record.mfa_device_id is None


@pytest.mark.anyio
async def test_execute_action_employee_not_found(db: InMemoryDatabase):
    """Test error when employee not found."""
    tool = OktaSecurityExecuteActionTool()
    request = OktaSecurityExecuteActionInput(
        email="nonexistent@vdb.com",
        operation=OktaSecurityOperation.UNLOCK_ACCOUNT,
        ticket_id="TCK-00012350",
    )

    with pytest.raises(Tool.ExecutionError) as exc_info:
        await tool.run(db, request)

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_execute_action_add_mfa_device_missing_device_id(db: InMemoryDatabase):
    """Test error when mfa_device_id is missing for add_mfa_device."""
    tool = OktaSecurityExecuteActionTool()
    request = OktaSecurityExecuteActionInput(
        email="marcus.thompson@vdb.com",
        operation=OktaSecurityOperation.ADD_MFA_DEVICE,
        ticket_id="TCK-00012351",
    )

    with pytest.raises(Tool.ExecutionError) as exc_info:
        await tool.run(db, request)

    assert "mfa_device_id is required" in str(exc_info.value)


@pytest.mark.anyio
async def test_execute_action_set_bypass_missing_duration(db: InMemoryDatabase):
    """Test error when bypass_duration_hours is missing for set_temporary_bypass."""
    tool = OktaSecurityExecuteActionTool()
    request = OktaSecurityExecuteActionInput(
        email="marcus.thompson@vdb.com",
        operation=OktaSecurityOperation.SET_TEMPORARY_BYPASS,
        ticket_id="TCK-00012352",
    )

    with pytest.raises(Tool.ExecutionError) as exc_info:
        await tool.run(db, request)

    assert "bypass_duration_hours is required" in str(exc_info.value)


@pytest.mark.anyio
async def test_execute_action_set_bypass_exceeds_max_duration(db: InMemoryDatabase):
    """Test error when bypass_duration_hours exceeds 4 hours."""
    tool = OktaSecurityExecuteActionTool()
    request = OktaSecurityExecuteActionInput(
        email="marcus.thompson@vdb.com",
        operation=OktaSecurityOperation.SET_TEMPORARY_BYPASS,
        bypass_duration_hours=5,
        ticket_id="TCK-00012353",
    )

    with pytest.raises(Tool.ExecutionError) as exc_info:
        await tool.run(db, request)

    assert "cannot exceed 4 hours" in str(exc_info.value)
