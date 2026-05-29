# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for NDA Management API (master tool)."""

from enum import Enum
from typing import Any, Dict, Optional, Type

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.client_access.models import (
    NdaRecord,
    NdaStatus,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from tb_business_ops_servers_202606.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field


class NdaApiAction(str, Enum):
    """NDA API action enumeration."""

    CHECK_STATUS = "check_status"
    SEND_FOR_SIGNATURE = "send_for_signature"


class NdaApiInput(BaseModel):
    """Input for nda_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    action: NdaApiAction = Field(
        ...,
        description="Action to perform",
        examples=["check_status"],
    )
    email: Optional[str] = Field(
        None,
        description="Employee email (required for both actions)",
        examples=["user@msg.com"],
    )
    client_id: Optional[str] = Field(
        None,
        description="Client ID (required for both actions)",
        examples=["CLT-0012345"],
    )


class NdaDataOutput(BaseModel):
    """NDA data output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    status: str = Field(..., description="NDA status")


class NdaApiOutput(BaseModel):
    """Output for nda_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    signed: Optional[bool] = Field(
        None,
        description="Indicates if NDA is signed (for action=check_status)",
    )
    nda_data: Optional[NdaDataOutput] = Field(
        None,
        description="NDA record from nda_records table (for action=check_status)",
    )
    success: Optional[bool] = Field(
        None,
        description="Indicates if NDA was sent successfully (for action=send_for_signature)",
    )


class NdaApiTool(Tool):
    """Master tool implementation for NDA Management API."""

    @property
    def name(self) -> str:
        return "api"

    @property
    def description(self) -> str:
        return (
            "Manage NDA signing and tracking. Checks NDA status and sends NDAs for signature. "
            "Use action parameter to specify the operation:\n\n"
            "- action='check_status': Checks if employee has signed NDA for a specific client. "
            "REQUIRES: email, client_id. Returns signed boolean and nda_data object from nda_records "
            "table with fields: status (not_signed, sent_for_signature, signed, expired). If no record "
            "found, returns nda_status='not_signed'.\n\n"
            "- action='send_for_signature': Sends NDA document to employee for electronic signature via "
            "DocuSign. REQUIRES: email, client_id. Returns success boolean. UPSERT on (employee_email, "
            "client_id): if exists UPDATE status=sent_for_signature, if not exists INSERT new record with "
            "status=sent_for_signature.\n\n"
            "Check NDA status before provisioning client access. Send for signature if not already sent."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(NdaApiInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(NdaApiOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return NdaApiInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return NdaApiOutput

    async def run(self, db: InMemoryDatabase, request: NdaApiInput) -> NdaApiOutput:
        """Execute NDA API action."""
        try:
            if request.action == NdaApiAction.CHECK_STATUS:
                return await self._check_status(db, request)
            elif request.action == NdaApiAction.SEND_FOR_SIGNATURE:
                return await self._send_for_signature(db, request)
            else:
                raise Tool.ExecutionError(f"Invalid action: {request.action}")

        except Tool.ExecutionError:
            raise
        except Exception as e:
            error_message = f"Failed to execute NDA API action: {str(e)}"
            raise Tool.ExecutionError(error_message)

    async def _check_status(
        self, db: InMemoryDatabase, request: NdaApiInput
    ) -> NdaApiOutput:
        """Check NDA status for an employee and client."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")
        if not request.client_id:
            raise Tool.ExecutionError("Missing required parameter: client_id")

        # Get all NDA records
        all_ndas = db.get_all(NdaRecord)

        # Find NDA record for employee and client
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
            # Record exists, return actual status
            signed = nda_record.status == NdaStatus.SIGNED
            nda_data = NdaDataOutput(status=nda_record.status.value)
            return NdaApiOutput(signed=signed, nda_data=nda_data)
        else:
            # No record found, return not_signed
            signed = False
            nda_data = NdaDataOutput(status=NdaStatus.NOT_SIGNED.value)
            return NdaApiOutput(signed=signed, nda_data=nda_data)

    async def _send_for_signature(
        self, db: InMemoryDatabase, request: NdaApiInput
    ) -> NdaApiOutput:
        """Send NDA for signature."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")
        if not request.client_id:
            raise Tool.ExecutionError("Missing required parameter: client_id")

        # Get all NDA records
        all_ndas = db.get_all(NdaRecord)

        # Find existing NDA record
        existing_record = next(
            (
                n
                for n in all_ndas
                if n.employee_email == request.email
                and n.client_id == request.client_id
            ),
            None,
        )

        if existing_record:
            # UPSERT: Update existing record
            existing_record.status = NdaStatus.SENT_FOR_SIGNATURE
            db.update(existing_record)
        else:
            # UPSERT: Insert new record
            new_record = NdaRecord(
                employee_email=request.email,
                client_id=request.client_id,
                status=NdaStatus.SENT_FOR_SIGNATURE,
            )
            db.create(new_record)

        return NdaApiOutput(success=True)
