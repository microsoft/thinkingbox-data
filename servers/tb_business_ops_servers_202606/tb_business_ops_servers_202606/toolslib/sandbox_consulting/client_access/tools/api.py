# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for Client Access Management API (master tool)."""

from enum import Enum
from typing import Any, Dict, List, Optional, Type

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.client_access.models import (
    AccessType,
    ClearanceRecord,
    ClearanceStatus,
    ClientSystemAccess,
    NdaRecord,
    NdaStatus,
    VpnAccess,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.degreed.models import (
    TrainingEnrollment,
)
from tb_business_ops_servers_202606.toolslib.sandbox_consulting.salesforce_crm.models import Client
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field


class ClientAccessApiAction(str, Enum):
    """Client Access API action enumeration."""

    PROVISION_VPN = "provision_vpn"
    CHECK_VPN_ACCESS = "check_vpn_access"
    REVOKE_VPN = "revoke_vpn"
    PROVISION_CLIENT_SYSTEM = "provision_client_system"
    CHECK_CLIENT_REQUIREMENTS = "check_client_requirements"
    GET_EMPLOYEE_PREREQUISITES = "get_employee_prerequisites"


class ClientAccessApiInput(BaseModel):
    """Input for client_access_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    action: ClientAccessApiAction = Field(
        ...,
        description="Action to perform",
        examples=["provision_vpn"],
    )
    email: Optional[str] = Field(
        None,
        description="Employee email (required for provision_vpn, check_vpn_access, revoke_vpn, provision_client_system, get_employee_prerequisites)",
        examples=["user@msg.com"],
    )
    client_id: Optional[str] = Field(
        None,
        description="Client ID (optional for provision_vpn, revoke_vpn; required for provision_client_system, check_client_requirements, get_employee_prerequisites)",
        examples=["CLT-0012345"],
    )
    system_name: Optional[str] = Field(
        None,
        description="System or application name (required for provision_client_system)",
        examples=["Client Salesforce"],
    )
    access_type: Optional[AccessType] = Field(
        None,
        description="Access type (required for provision_client_system)",
        examples=["read_only"],
    )


class VpnAccessOutput(BaseModel):
    """VPN access output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    id: str = Field(..., description="VPN access ID")
    employee_email: str = Field(..., description="Employee email")
    client_id: Optional[str] = Field(
        None, description="Client ID for client-specific VPN"
    )
    revoked_at: Optional[str] = Field(None, description="Revocation date")


class ClientRequirementsOutput(BaseModel):
    """Client requirements output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    clearance_level: str = Field(..., description="Required clearance level")
    requires_nda: bool = Field(..., description="Whether NDA is required")
    required_training_courses: List[str] = Field(
        default_factory=list, description="Array of required training course IDs"
    )


class ClientAccessApiOutput(BaseModel):
    """Output for client_access_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    success: Optional[bool] = Field(
        None,
        description="Indicates if operation was successful (for provision_vpn, revoke_vpn, provision_client_system)",
    )
    vpn_access: Optional[List[VpnAccessOutput]] = Field(
        None,
        description="Array of VPN access records (for action=check_vpn_access)",
    )
    requirements: Optional[ClientRequirementsOutput] = Field(
        None,
        description="Client requirements (for action=check_client_requirements)",
    )
    clearance_status: Optional[str] = Field(
        None,
        description="Employee clearance status (for action=get_employee_prerequisites)",
    )
    nda_status: Optional[str] = Field(
        None,
        description="Employee NDA status (for action=get_employee_prerequisites)",
    )
    completed_training_courses: Optional[List[str]] = Field(
        None,
        description="Array of completed training course IDs (for action=get_employee_prerequisites)",
    )


class ClientAccessApiTool(Tool):
    """Master tool implementation for Client Access Management API."""

    @property
    def name(self) -> str:
        return "api"

    @property
    def description(self) -> str:
        return (
            "Manage VPN access and client system provisioning. Provisions VPN access, checks VPN "
            "entitlements, revokes access, provisions client system access, checks client security "
            "requirements, and retrieves employee prerequisites. Use action parameter to specify the operation:\n\n"
            "- action='provision_vpn': Grants VPN access to an employee. REQUIRES: email. OPTIONAL: "
            "client_id (for client-specific VPN). Returns success boolean.\n\n"
            "- action='check_vpn_access': Retrieves current VPN entitlements for an employee. REQUIRES: email. "
            "Returns vpn_access array from vpn_access table where revoked_at is null.\n\n"
            "- action='revoke_vpn': Removes VPN access from an employee. REQUIRES: email. OPTIONAL: client_id "
            "(to revoke specific client VPN). Returns success boolean.\n\n"
            "- action='provision_client_system': Grants access to a specific client system or application. "
            "REQUIRES: email, client_id, system_name, access_type (full_access, read_only, contributor, admin). "
            "Returns success boolean.\n\n"
            "- action='check_client_requirements': Retrieves security and compliance requirements for a client. "
            "REQUIRES: client_id. Returns requirements object with clearance_level, requires_nda boolean, and "
            "required_training_courses array from clients table.\n\n"
            "- action='get_employee_prerequisites': Retrieves employee's current prerequisite status for client "
            "access. REQUIRES: email, client_id. Returns clearance_status enum (cleared, in_progress, not_initiated), "
            "nda_status enum (signed, not_signed, sent_for_signature), and completed_training_courses array.\n\n"
            "Always check employee prerequisites using get_employee_prerequisites before provisioning client access. "
            "Use check_client_requirements to retrieve security requirements from client record."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(ClientAccessApiInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(ClientAccessApiOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return ClientAccessApiInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return ClientAccessApiOutput

    async def run(
        self, db: InMemoryDatabase, request: ClientAccessApiInput
    ) -> ClientAccessApiOutput:
        """Execute Client Access API action."""
        try:
            if request.action == ClientAccessApiAction.PROVISION_VPN:
                return await self._provision_vpn(db, request)
            elif request.action == ClientAccessApiAction.CHECK_VPN_ACCESS:
                return await self._check_vpn_access(db, request)
            elif request.action == ClientAccessApiAction.REVOKE_VPN:
                return await self._revoke_vpn(db, request)
            elif request.action == ClientAccessApiAction.PROVISION_CLIENT_SYSTEM:
                return await self._provision_client_system(db, request)
            elif request.action == ClientAccessApiAction.CHECK_CLIENT_REQUIREMENTS:
                return await self._check_client_requirements(db, request)
            elif request.action == ClientAccessApiAction.GET_EMPLOYEE_PREREQUISITES:
                return await self._get_employee_prerequisites(db, request)
            else:
                raise Tool.ExecutionError(f"Invalid action: {request.action}")

        except Tool.ExecutionError:
            raise
        except Exception as e:
            error_message = f"Failed to execute Client Access API action: {str(e)}"
            raise Tool.ExecutionError(error_message)

    async def _provision_vpn(
        self, db: InMemoryDatabase, request: ClientAccessApiInput
    ) -> ClientAccessApiOutput:
        """Provision VPN access for an employee."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")

        # Generate VPN access ID
        existing_vpn = db.get_all(VpnAccess)
        PREFIX_FOR_NEW_IDS = "VPN-2"
        count = 0
        existing_ids = {vpn.id for vpn in existing_vpn}

        while True:
            new_id = f"{PREFIX_FOR_NEW_IDS}-{count:06d}"
            if new_id not in existing_ids:
                break
            count += 1

        # Create VPN access record
        new_vpn = VpnAccess(
            id=new_id,
            employee_email=request.email,
            client_id=request.client_id,
            revoked_at=None,
        )
        db.create(new_vpn)

        return ClientAccessApiOutput(success=True)

    async def _check_vpn_access(
        self, db: InMemoryDatabase, request: ClientAccessApiInput
    ) -> ClientAccessApiOutput:
        """Retrieve current VPN entitlements for an employee."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")

        # Get all VPN access records
        all_vpn = db.get_all(VpnAccess)

        # Filter active VPN access for employee (revoked_at is null)
        active_vpn = [
            VpnAccessOutput(
                id=vpn.id,
                employee_email=vpn.employee_email,
                client_id=vpn.client_id,
                revoked_at=vpn.revoked_at.isoformat() if vpn.revoked_at else None,
            )
            for vpn in all_vpn
            if vpn.employee_email == request.email and vpn.revoked_at is None
        ]

        return ClientAccessApiOutput(vpn_access=active_vpn)

    async def _revoke_vpn(
        self, db: InMemoryDatabase, request: ClientAccessApiInput
    ) -> ClientAccessApiOutput:
        """Revoke VPN access from an employee."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")

        # Get all VPN access records
        all_vpn = db.get_all(VpnAccess)

        # Find matching VPN access records to revoke
        from datetime import datetime, timezone

        # Use fixed date for repeatability
        fixed_revoked_date = datetime(2025, 10, 1, 0, 0, 0, tzinfo=timezone.utc)

        revoked_count = 0
        for vpn in all_vpn:
            # Match by email and optionally by client_id
            if vpn.employee_email == request.email and vpn.revoked_at is None:
                # If client_id is specified, only revoke that specific VPN
                if request.client_id is None or vpn.client_id == request.client_id:
                    vpn.revoked_at = fixed_revoked_date
                    db.update(vpn)
                    revoked_count += 1
                    # If client_id was specified, stop after first match
                    if request.client_id is not None:
                        break

        return ClientAccessApiOutput(success=True)

    async def _provision_client_system(
        self, db: InMemoryDatabase, request: ClientAccessApiInput
    ) -> ClientAccessApiOutput:
        """Provision access to a client system."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")
        if not request.client_id:
            raise Tool.ExecutionError("Missing required parameter: client_id")
        if not request.system_name:
            raise Tool.ExecutionError("Missing required parameter: system_name")
        if not request.access_type:
            raise Tool.ExecutionError("Missing required parameter: access_type")

        # Generate access ID
        existing_access = db.get_all(ClientSystemAccess)
        PREFIX_FOR_NEW_IDS = "CSA-2"
        count = 0
        existing_ids = {access.id for access in existing_access}

        while True:
            new_id = f"{PREFIX_FOR_NEW_IDS}-{count:06d}"
            if new_id not in existing_ids:
                break
            count += 1

        # Create client system access record
        new_access = ClientSystemAccess(
            id=new_id,
            employee_email=request.email,
            client_id=request.client_id,
            system_name=request.system_name,
            access_type=request.access_type,
            revoked_at=None,
        )
        db.create(new_access)

        return ClientAccessApiOutput(success=True)

    async def _check_client_requirements(
        self, db: InMemoryDatabase, request: ClientAccessApiInput
    ) -> ClientAccessApiOutput:
        """Retrieve security and compliance requirements for a client."""
        if not request.client_id:
            raise Tool.ExecutionError("Missing required parameter: client_id")

        # Get client by ID
        client = db.get_by_id(Client, request.client_id)

        if not client:
            raise Tool.ExecutionError(f"Client not found: {request.client_id}")

        # Return client requirements
        requirements = ClientRequirementsOutput(
            clearance_level=client.clearance_level.value,
            requires_nda=client.requires_nda,
            required_training_courses=client.required_training_courses,
        )

        return ClientAccessApiOutput(requirements=requirements)

    async def _get_employee_prerequisites(
        self, db: InMemoryDatabase, request: ClientAccessApiInput
    ) -> ClientAccessApiOutput:
        """Retrieve employee's prerequisite status for client access."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")
        if not request.client_id:
            raise Tool.ExecutionError("Missing required parameter: client_id")

        # Get clearance status
        all_clearances = db.get_all(ClearanceRecord)
        clearance_record = next(
            (c for c in all_clearances if c.employee_email == request.email), None
        )

        if clearance_record:
            clearance_status = clearance_record.status.value
        else:
            clearance_status = ClearanceStatus.NOT_INITIATED.value

        # Get NDA status
        all_ndas = db.get_all(NdaRecord)
        nda_record = next(
            (
                n
                for n in all_ndas
                if n.employee_email == request.email
                and n.client_id == request.client_id
            ),
            None,
        )

        if nda_record:
            nda_status = nda_record.status.value
        else:
            nda_status = NdaStatus.NOT_SIGNED.value

        # Get completed training courses
        all_enrollments = db.get_all(TrainingEnrollment)
        completed_courses = [
            enrollment.course_id
            for enrollment in all_enrollments
            if enrollment.employee_email == request.email
            and enrollment.completion_date is not None
        ]

        return ClientAccessApiOutput(
            clearance_status=clearance_status,
            nda_status=nda_status,
            completed_training_courses=completed_courses,
        )
