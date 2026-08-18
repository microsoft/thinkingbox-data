# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for Security API - Verify Incident Tool."""

from datetime import timedelta

import pytest
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
    SecurityIncident,
    Severity,
)
from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.tools.security_api_verify_incident import (
    FIXED_CURRENT_TIME,
    SecurityVerifyIncidentInput,
    SecurityVerifyIncidentTool,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
)


@pytest.mark.anyio
async def test_verify_incident_returns_active_incidents(db: InMemoryDatabase):
    """Test that active incidents are returned."""
    tool = SecurityVerifyIncidentTool()
    request = SecurityVerifyIncidentInput()

    result = await tool.run(db, request)

    # Should return at least some active incidents from initial data
    assert len(result.incidents) > 0

    # All returned incidents should either be active or recently closed
    for incident in result.incidents:
        if incident.is_active:
            assert incident.closed_at is None
        else:
            # If not active, should have been closed recently
            assert incident.closed_at is not None


@pytest.mark.anyio
async def test_verify_incident_excludes_status_field(db: InMemoryDatabase):
    """Test that the status field is not included in the output."""
    tool = SecurityVerifyIncidentTool()
    request = SecurityVerifyIncidentInput()

    result = await tool.run(db, request)

    # Verify that returned incident records don't have status field
    assert len(result.incidents) > 0
    for incident in result.incidents:
        # Check that status field is not in the dict representation
        incident_dict = incident.model_dump()
        assert "status" not in incident_dict
        # Verify that is_active field IS included
        assert "is_active" in incident_dict


@pytest.mark.anyio
async def test_verify_incident_includes_recently_closed(db: InMemoryDatabase):
    """Test that recently closed incidents (within 24 hours) are included."""
    tool = SecurityVerifyIncidentTool()

    # Add a recently closed incident
    recent_closed = SecurityIncident(
        id="SEC-99999991",
        employee_id="WD-294817",
        severity=Severity.SEV2,
        incident_type="test_incident",
        description="Test recently closed incident",
        status="closed",
        is_active=False,
        reported_at=FIXED_CURRENT_TIME - timedelta(hours=20),
        reported_by="test_user",
        resolved_at=FIXED_CURRENT_TIME - timedelta(hours=2),  # Closed 2 hours ago
        resolution_notes="Test resolution",
    )
    db.create(recent_closed)

    request = SecurityVerifyIncidentInput()
    result = await tool.run(db, request)

    # Should include the recently closed incident
    incident_ids = [inc.incident_id for inc in result.incidents]
    assert "SEC-99999991" in incident_ids

    # Verify the incident details
    test_incident = next(
        inc for inc in result.incidents if inc.incident_id == "SEC-99999991"
    )
    assert test_incident.is_active is False
    assert test_incident.closed_at is not None


@pytest.mark.anyio
async def test_verify_incident_excludes_old_closed_incidents(db: InMemoryDatabase):
    """Test that incidents closed more than 24 hours ago are excluded."""
    tool = SecurityVerifyIncidentTool()

    # Add an old closed incident (more than 24 hours ago)
    old_closed = SecurityIncident(
        id="SEC-99999992",
        employee_id="WD-294817",
        severity=Severity.SEV3,
        incident_type="test_incident",
        description="Test old closed incident",
        status="closed",
        is_active=False,
        reported_at=FIXED_CURRENT_TIME - timedelta(hours=72),
        reported_by="test_user",
        resolved_at=FIXED_CURRENT_TIME - timedelta(hours=30),  # Closed 30 hours ago
        resolution_notes="Test resolution",
    )
    db.create(old_closed)

    request = SecurityVerifyIncidentInput()
    result = await tool.run(db, request)

    # Should NOT include the old closed incident
    incident_ids = [inc.incident_id for inc in result.incidents]
    assert "SEC-99999992" not in incident_ids


@pytest.mark.anyio
async def test_verify_incident_uses_is_active_field(db: InMemoryDatabase):
    """Test that the query uses is_active field from DB, not status."""
    tool = SecurityVerifyIncidentTool()

    # Add an active incident
    active_incident = SecurityIncident(
        id="SEC-99999993",
        employee_id="WD-573926",
        severity=Severity.SEV1,
        incident_type="test_active",
        description="Test active incident",
        status="open",
        is_active=True,
        reported_at=FIXED_CURRENT_TIME - timedelta(hours=5),
        reported_by="test_user",
        resolved_at=None,
        resolution_notes=None,
    )
    db.create(active_incident)

    request = SecurityVerifyIncidentInput()
    result = await tool.run(db, request)

    # Should include the active incident
    incident_ids = [inc.incident_id for inc in result.incidents]
    assert "SEC-99999993" in incident_ids

    # Verify the incident is marked as active
    test_incident = next(
        inc for inc in result.incidents if inc.incident_id == "SEC-99999993"
    )
    assert test_incident.is_active is True


@pytest.mark.anyio
async def test_verify_incident_returns_sorted_by_started_at_desc(db: InMemoryDatabase):
    """Test that incidents are sorted by started_at in descending order (most recent first)."""
    tool = SecurityVerifyIncidentTool()

    # Add multiple active incidents with different start times
    incident1 = SecurityIncident(
        id="SEC-99999994",
        employee_id="WD-681453",
        severity=Severity.SEV2,
        incident_type="test_1",
        description="Test incident 1",
        status="open",
        is_active=True,
        reported_at=FIXED_CURRENT_TIME - timedelta(hours=10),
        reported_by="test_user",
        resolved_at=None,
        resolution_notes=None,
    )

    incident2 = SecurityIncident(
        id="SEC-99999995",
        employee_id="WD-847291",
        severity=Severity.SEV1,
        incident_type="test_2",
        description="Test incident 2",
        status="open",
        is_active=True,
        reported_at=FIXED_CURRENT_TIME - timedelta(hours=2),  # More recent
        reported_by="test_user",
        resolved_at=None,
        resolution_notes=None,
    )

    db.create(incident1)
    db.create(incident2)

    request = SecurityVerifyIncidentInput()
    result = await tool.run(db, request)

    # Find our test incidents in the result
    test_incidents = [
        inc
        for inc in result.incidents
        if inc.incident_id in ["SEC-99999994", "SEC-99999995"]
    ]
    assert len(test_incidents) == 2

    # The more recent incident (incident2) should appear before the older one (incident1)
    idx1 = next(
        i for i, inc in enumerate(result.incidents) if inc.incident_id == "SEC-99999994"
    )
    idx2 = next(
        i for i, inc in enumerate(result.incidents) if inc.incident_id == "SEC-99999995"
    )
    assert idx2 < idx1  # incident2 should have a smaller index (appear earlier)
