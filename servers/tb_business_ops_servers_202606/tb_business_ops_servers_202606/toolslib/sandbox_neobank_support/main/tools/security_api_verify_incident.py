# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Security API - Verify Incident Tool."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Type

from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
    SecurityIncident,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    get_schema_without_refs,
)
from pydantic import BaseModel, ConfigDict, Field

FIXED_CURRENT_TIME = datetime(2025, 12, 18, 10, 0, 0, tzinfo=timezone.utc)


class SecurityVerifyIncidentInput(BaseModel):
    """Input model for security_api.verify_incident."""

    model_config = ConfigDict(extra="forbid")

    # No input parameters needed - returns all active or recently closed incidents


class IncidentRecord(BaseModel):
    """Individual incident record."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    incident_id: str = Field(..., description="Incident ID")
    severity: str = Field(..., description="Incident severity (SEV1-SEV4)")
    description: str = Field(..., description="Incident description")
    started_at: str = Field(..., description="When incident started in ISO 8601 format")
    is_active: bool = Field(..., description="Whether incident is active")
    closed_at: str | None = Field(
        None, description="When incident was closed in ISO 8601 format"
    )


class SecurityVerifyIncidentOutput(BaseModel):
    """Output model for security_api.verify_incident."""

    model_config = ConfigDict(extra="forbid")

    incidents: List[IncidentRecord] = Field(
        ..., description="Array of incident records matching criteria"
    )


class SecurityVerifyIncidentTool(Tool):
    """Tool for retrieving active and recent security incidents."""

    @property
    def name(self) -> str:
        return "security_api_verify_incident"

    @property
    def description(self) -> str:
        return (
            "Retrieve active security incidents and recently closed incidents for verification. "
            "Returns an array of security incidents that are currently active or were closed within "
            "the last 24 hours. Used to verify that a security incident exists before granting emergency "
            "access or to confirm incident context for access requests. Helps ensure that incident-based "
            "access requests are tied to legitimate ongoing or recent incidents."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(SecurityVerifyIncidentInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(SecurityVerifyIncidentOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return SecurityVerifyIncidentInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return SecurityVerifyIncidentOutput

    async def run(
        self, db: InMemoryDatabase, request: SecurityVerifyIncidentInput
    ) -> SecurityVerifyIncidentOutput:
        """Retrieve active and recently closed security incidents."""
        try:
            # Get all security incidents
            all_incidents = db.get_all(SecurityIncident)

            # Calculate 24 hours ago threshold
            threshold_time = FIXED_CURRENT_TIME - timedelta(hours=24)

            # Query: WHERE is_active = true OR (is_active = false AND closed_at >= now - 24 hours)
            matching_incidents = []

            for incident in all_incidents:
                # Check if active
                if incident.is_active:
                    matching_incidents.append(incident)
                    continue

                # Check if recently closed (inactive but closed within last 24 hours)
                if not incident.is_active and incident.resolved_at:
                    # resolved_at is datetime object
                    if incident.resolved_at >= threshold_time:
                        matching_incidents.append(incident)

            # Convert to output format (without status field)
            incident_records = []
            for incident in matching_incidents:
                incident_records.append(
                    IncidentRecord(
                        incident_id=incident.id,
                        severity=incident.severity.value,
                        description=incident.description,
                        started_at=(
                            incident.reported_at.isoformat()
                            if isinstance(incident.reported_at, datetime)
                            else incident.reported_at
                        ),
                        is_active=incident.is_active,
                        closed_at=(
                            incident.resolved_at.isoformat()
                            if incident.resolved_at
                            and isinstance(incident.resolved_at, datetime)
                            else incident.resolved_at
                        ),
                    )
                )

            # Sort by started_at DESC (most recent first)
            incident_records.sort(key=lambda x: x.started_at, reverse=True)

            return SecurityVerifyIncidentOutput(incidents=incident_records)

        except Exception as e:
            error_message = f"Failed to retrieve security incidents: {str(e)}"
            raise Tool.ExecutionError(error_message)
