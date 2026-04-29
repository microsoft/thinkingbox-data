# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for Sterling BackCheck API (master tool)."""

from enum import Enum
from typing import Any, Dict, Optional, Type

from ms_toloka_servers.toolslib.sandbox_consulting.client_access.models import (
    ClearanceLevel,
    ClearanceRecord,
    ClearanceStatus,
)
from ms_toloka_servers.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    UnstableField,
    get_schema_without_refs,
    get_typesense,
)
from ms_toloka_servers.utils.typesense_helpers import TypesenseIndex
from pydantic import BaseModel, ConfigDict, Field


class BackgroundCheckApiAction(str, Enum):
    """Background Check API action enumeration."""

    GET_STATUS = "get_status"
    INITIATE = "initiate"
    GET_TIMELINE = "get_timeline"


class BackgroundCheckApiInput(BaseModel):
    """Input for background_check_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    action: BackgroundCheckApiAction = Field(
        ...,
        description="Action to perform",
        examples=["get_status"],
    )
    email: Optional[str] = Field(
        None,
        description="Employee email (required for get_status, initiate)",
        examples=["user@msg.com"],
    )
    clearance_level: Optional[ClearanceLevel] = Field(
        None,
        description="Clearance level (required for initiate, get_timeline)",
        examples=["standard"],
    )


class ClearanceDataOutput(BaseModel):
    """Clearance data output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    clearance_level: str = Field(..., description="Clearance level")
    status: str = Field(..., description="Clearance status")


class BackgroundCheckApiOutput(BaseModel):
    """Output for background_check_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    clearance_data: Optional[ClearanceDataOutput] = Field(
        None,
        description="Clearance record from clearance_records table (for action=get_status)",
    )
    success: Optional[bool] = Field(
        None,
        description="Indicates if initiation was successful (for action=initiate)",
    )
    estimated_days: Optional[int] = Field(
        None,
        description="Estimated days to completion (for action=get_timeline)",
    )


class BackgroundCheckApiTool(Tool):
    """Master tool implementation for Sterling BackCheck API."""

    @property
    def name(self) -> str:
        return "api"

    @property
    def description(self) -> str:
        return (
            "Manage background checks and security clearances. Checks clearance status, initiates "
            "background checks, and retrieves processing timelines. Use action parameter to specify "
            "the operation:\n\n"
            "- action='get_status': Retrieves current background check and clearance status for an "
            "employee. REQUIRES: email. Returns clearance_data object from clearance_records table with "
            "fields: clearance_level, status (not_initiated, in_progress, cleared, failed, expired). "
            "If no record found, returns clearance_status='not_initiated'.\n\n"
            "- action='initiate': Starts a new background check process for an employee. REQUIRES: email, "
            "clearance_level (standard or high_security). Returns success boolean. UPSERT on "
            "(employee_email, clearance_level): if exists UPDATE status=in_progress, if not exists INSERT "
            "new record.\n\n"
            "- action='get_timeline': Retrieves estimated processing time for a clearance level. REQUIRES: "
            "clearance_level. Returns estimated_days integer.\n\n"
            "Check clearance status before provisioning client access. Initiate clearance if not already "
            "in progress."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(BackgroundCheckApiInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(BackgroundCheckApiOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return BackgroundCheckApiInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return BackgroundCheckApiOutput

    async def run(
        self, db: InMemoryDatabase, request: BackgroundCheckApiInput
    ) -> BackgroundCheckApiOutput:
        """Execute Background Check API action."""
        try:
            if request.action == BackgroundCheckApiAction.GET_STATUS:
                return await self._get_status(db, request)
            elif request.action == BackgroundCheckApiAction.INITIATE:
                return await self._initiate(db, request)
            elif request.action == BackgroundCheckApiAction.GET_TIMELINE:
                return await self._get_timeline(db, request)
            else:
                raise Tool.ExecutionError(f"Invalid action: {request.action}")

        except Tool.ExecutionError:
            raise
        except Exception as e:
            error_message = f"Failed to execute Background Check API action: {str(e)}"
            raise Tool.ExecutionError(error_message)

    async def _get_status(
        self, db: InMemoryDatabase, request: BackgroundCheckApiInput
    ) -> BackgroundCheckApiOutput:
        """Get clearance status for an employee."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")

        # Get all clearance records
        all_clearances = db.get_all(ClearanceRecord)

        # Find clearance record for employee
        clearance_record = next(
            (c for c in all_clearances if c.employee_email == request.email), None
        )

        if clearance_record:
            clearance_data = ClearanceDataOutput(
                clearance_level=clearance_record.clearance_level.value,
                status=clearance_record.status.value,
            )
            return BackgroundCheckApiOutput(clearance_data=clearance_data)
        else:
            # If no record found, return not_initiated status
            clearance_data = ClearanceDataOutput(
                clearance_level=ClearanceLevel.STANDARD.value,  # Default clearance level
                status=ClearanceStatus.NOT_INITIATED.value,
            )
            return BackgroundCheckApiOutput(clearance_data=clearance_data)

    async def _initiate(
        self, db: InMemoryDatabase, request: BackgroundCheckApiInput
    ) -> BackgroundCheckApiOutput:
        """Initiate background check for an employee."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")
        if not request.clearance_level:
            raise Tool.ExecutionError("Missing required parameter: clearance_level")

        # Get all clearance records
        all_clearances = db.get_all(ClearanceRecord)

        # Find existing clearance record for employee
        existing_record = next(
            (c for c in all_clearances if c.employee_email == request.email), None
        )

        if existing_record:
            # UPSERT: Update existing record
            existing_record.clearance_level = request.clearance_level
            existing_record.status = ClearanceStatus.IN_PROGRESS
            db.update(existing_record)
        else:
            # UPSERT: Insert new record
            new_record = ClearanceRecord(
                employee_email=request.email,
                clearance_level=request.clearance_level,
                status=ClearanceStatus.IN_PROGRESS,
            )
            db.create(new_record)

        return BackgroundCheckApiOutput(success=True)

    async def _get_timeline(
        self, db: InMemoryDatabase, request: BackgroundCheckApiInput
    ) -> BackgroundCheckApiOutput:
        """Get estimated processing time for clearance level."""
        if not request.clearance_level:
            raise Tool.ExecutionError("Missing required parameter: clearance_level")

        # Return estimated days based on clearance level
        if request.clearance_level == ClearanceLevel.STANDARD:
            estimated_days = 14
        elif request.clearance_level == ClearanceLevel.HIGH_SECURITY:
            estimated_days = 28
        else:
            estimated_days = 14  # Default

        return BackgroundCheckApiOutput(estimated_days=estimated_days)
