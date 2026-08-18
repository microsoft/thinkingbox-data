# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Okta Security API - Execute Action Tool."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type

from tb_business_ops_servers_202606.toolslib.sandbox_neobank_support.main.models import (
    Employee,
    OktaSecurityAudit,
    OktaSecurityOperation,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    get_schema_without_refs,
)
from pydantic import BaseModel, ConfigDict, Field

FIXED_CURRENT_TIME = datetime(2025, 12, 18, 10, 0, 0, tzinfo=timezone.utc)


class OktaSecurityExecuteActionInput(BaseModel):
    """Input model for okta_security_api.execute_action."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(
        ...,
        description="Email of the employee whose account is being acted upon",
        examples=["john.smith@vdb.com"],
    )
    operation: OktaSecurityOperation = Field(
        ...,
        description="The security operation to perform",
        examples=["unlock_account"],
    )
    mfa_device_id: Optional[str] = Field(
        None,
        description="Required for add_mfa_device and remove_mfa_device operation",
        examples=["MFA-12345"],
    )
    bypass_duration_hours: Optional[int] = Field(
        None,
        description="Required for set_temporary_bypass. Maximum: 4 hours",
        examples=[4],
    )
    ticket_id: Optional[str] = Field(
        None,
        description="Zendesk ticket ID for audit trail linking",
        examples=["TCK-00012345"],
    )
    bypass_expires_at: Optional[str] = Field(
        None,
        description="Expiration timestamp for MFA bypass. Only for set_temporary_bypass operation",
        examples=["2025-12-18T14:00:00Z"],
    )


class OktaSecurityExecuteActionOutput(BaseModel):
    """Output model for okta_security_api.execute_action."""

    model_config = ConfigDict(extra="forbid")

    success: bool = Field(
        ..., description="Whether the operation completed successfully"
    )
    audit_id: str = Field(
        ...,
        description="Unique identifier for the audit record created (format: OSA-########)",
    )
    error_message: Optional[str] = Field(
        None,
        description="Error description if operation failed. Only returned when success=false",
    )


class OktaSecurityExecuteActionTool(Tool):
    """Tool for executing security operations on employee Okta accounts."""

    @property
    def name(self) -> str:
        return "okta_security_api_execute_action"

    @property
    def description(self) -> str:
        return (
            "Execute security operations on an employee's Okta account for identity verification, "
            "account management, and MFA handling. Performs security-related operations on employee "
            "Okta accounts including identity verification (via manager, assistant, SMS, or video call), "
            "account unlock, password reset, session invalidation, MFA device management, and temporary "
            "MFA bypass. All operations are audit logged. Use for password reset assistance, MFA issues, "
            "account lockouts, and security incident response."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(OktaSecurityExecuteActionInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(OktaSecurityExecuteActionOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return OktaSecurityExecuteActionInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return OktaSecurityExecuteActionOutput

    async def run(
        self, db: InMemoryDatabase, request: OktaSecurityExecuteActionInput
    ) -> OktaSecurityExecuteActionOutput:
        """Execute a security operation on an employee's Okta account."""
        try:
            # Validate employee exists
            all_employees = db.get_all(Employee)
            employees = [e for e in all_employees if e.email == request.email]

            if not employees:
                raise Tool.ExecutionError(
                    f"Employee not found in Okta directory: {request.email}"
                )

            employee = employees[0]

            # Validate operation-specific requirements
            if request.operation in [
                OktaSecurityOperation.ADD_MFA_DEVICE,
                OktaSecurityOperation.REMOVE_MFA_DEVICE,
            ]:
                if not request.mfa_device_id:
                    raise Tool.ExecutionError(
                        f"mfa_device_id is required for {request.operation.value} operation"
                    )

            if request.operation == OktaSecurityOperation.SET_TEMPORARY_BYPASS:
                if not request.bypass_duration_hours:
                    raise Tool.ExecutionError(
                        "bypass_duration_hours is required for set_temporary_bypass operation"
                    )
                if request.bypass_duration_hours > 4:
                    raise Tool.ExecutionError(
                        "bypass_duration_hours cannot exceed 4 hours"
                    )

            # Generate audit record ID
            all_audits = db.get_all(OktaSecurityAudit)
            next_id = len(all_audits) + 1
            audit_id = f"OSA-{next_id:08d}"

            # Calculate bypass expiration if applicable
            bypass_expires_at = None
            if (
                request.operation == OktaSecurityOperation.SET_TEMPORARY_BYPASS
                and request.bypass_duration_hours
            ):
                from datetime import timedelta

                bypass_expires_at = FIXED_CURRENT_TIME + timedelta(
                    hours=request.bypass_duration_hours
                )
            elif request.bypass_expires_at:
                bypass_expires_at = datetime.fromisoformat(
                    request.bypass_expires_at.replace("Z", "+00:00")
                )

            # Create audit record with operation-specific fields
            # Base fields: employee_id, operation, success, ticket_id, executed_by='system'
            audit_data = {
                "id": audit_id,
                "employee_id": employee.id,
                "operation": request.operation,
                "performed_by": "system",
                "performed_at": FIXED_CURRENT_TIME,
                "reason": f"Security operation: {request.operation.value}",
                "ticket_id": request.ticket_id,
                "verification_method": None,
                "success": True,
            }

            # Add operation-specific fields
            if request.operation == OktaSecurityOperation.SET_TEMPORARY_BYPASS:
                audit_data["bypass_duration_hours"] = request.bypass_duration_hours
                audit_data["bypass_expires_at"] = bypass_expires_at
            elif request.operation in [
                OktaSecurityOperation.ADD_MFA_DEVICE,
                OktaSecurityOperation.REMOVE_MFA_DEVICE,
            ]:
                audit_data["mfa_device_id"] = request.mfa_device_id

            audit_record = OktaSecurityAudit(**audit_data)

            db.create(audit_record)

            return OktaSecurityExecuteActionOutput(
                success=True, audit_id=audit_id, error_message=None
            )

        except Tool.ExecutionError:
            raise
        except Exception as e:
            error_message = f"Failed to execute security action: {str(e)}"
            raise Tool.ExecutionError(error_message)
