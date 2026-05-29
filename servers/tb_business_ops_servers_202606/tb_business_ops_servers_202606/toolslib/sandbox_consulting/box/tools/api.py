# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for Box Document Management API (master tool)."""

from enum import Enum
from typing import Any, Dict, Optional, Type

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.box.models import (
    ConfidentialityLevel,
    Folder,
    FolderAccessLog,
    PermissionLevel,
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


class BoxAction(str, Enum):
    """Box API action enumeration."""

    GET_FOLDER_DETAILS = "get_folder_details"
    GRANT_FOLDER_ACCESS = "grant_folder_access"


class BoxApiInput(BaseModel):
    """Input for box_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    action: BoxAction = Field(
        ...,
        description="Action to perform",
        examples=["get_folder_details"],
    )
    folder_id: Optional[str] = Field(
        None,
        description="Folder ID (required for get_folder_details, grant_folder_access)",
        examples=["FLD-0012345"],
    )
    email: Optional[str] = Field(
        None,
        description="Employee email address (required for grant_folder_access)",
        examples=["user@msg.com"],
    )
    permission_level: Optional[PermissionLevel] = Field(
        None,
        description="Permission level to grant (required for grant_folder_access)",
        examples=["viewer"],
    )


class FolderDataOutput(BaseModel):
    """Folder data output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    id: str = Field(..., description="Folder ID")
    folder_name: str = Field(..., description="Folder name")
    confidentiality_level: str = Field(..., description="Confidentiality level")
    owner_email: str = Field(..., description="Folder owner email address")
    client_id: Optional[str] = Field(None, description="Client ID if client folder")
    engagement_code: Optional[str] = Field(
        None, description="Engagement code if engagement-specific"
    )


class BoxApiOutput(BaseModel):
    """Output for box_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    folder_data: Optional[FolderDataOutput] = Field(
        None,
        description="Folder record from folders table (for action=get_folder_details)",
    )
    success: Optional[bool] = Field(
        None,
        description="Indicates if access was granted successfully (for action=grant_folder_access)",
    )


class BoxApiTool(Tool):
    """Master tool implementation for Box Document Management API."""

    @property
    def name(self) -> str:
        return "api"

    @property
    def description(self) -> str:
        return (
            "Manage document folder access. Retrieves folder details and grants folder access to employees. "
            "Use action parameter to specify the operation:\n\n"
            "- action='get_folder_details': Retrieves folder information and metadata. REQUIRES: folder_id. "
            "Returns folder_data object from folders table including folder_name, confidentiality_level "
            "(public, internal, confidential, client_confidential), owner_email, client_id (if client folder), "
            "and engagement_code (if engagement-specific).\n\n"
            "- action='grant_folder_access': Grants access to a folder with specified permission level. "
            "REQUIRES: email, folder_id, permission_level (viewer, editor, co_owner). Returns success boolean.\n\n"
            "Use get_folder_details to check confidentiality level and validate access requirements before "
            "granting access."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(BoxApiInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(BoxApiOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return BoxApiInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return BoxApiOutput

    async def run(self, db: InMemoryDatabase, request: BoxApiInput) -> BoxApiOutput:
        """Execute Box API action."""
        try:
            if request.action == BoxAction.GET_FOLDER_DETAILS:
                return await self._get_folder_details(db, request)
            elif request.action == BoxAction.GRANT_FOLDER_ACCESS:
                return await self._grant_folder_access(db, request)
            else:
                raise Tool.ExecutionError(f"Invalid action: {request.action}")

        except Tool.ExecutionError:
            # Re-raise ExecutionError exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Catch any other exceptions and convert them to ExecutionError
            error_message = f"Failed to execute Box API action: {str(e)}"
            raise Tool.ExecutionError(error_message)

    async def _get_folder_details(
        self, db: InMemoryDatabase, request: BoxApiInput
    ) -> BoxApiOutput:
        """Get folder details by folder_id."""
        if not request.folder_id:
            raise Tool.ExecutionError("Missing required parameter: folder_id")

        # Get folder by ID
        folder = db.get_by_id(Folder, request.folder_id)

        # If no folder found, raise 404 error
        if not folder:
            raise Tool.ExecutionError(f"Folder not found: {request.folder_id}")

        # Return folder data
        folder_data = FolderDataOutput(
            id=folder.id,
            folder_name=folder.folder_name,
            confidentiality_level=folder.confidentiality_level.value,
            owner_email=folder.owner_email,
            client_id=folder.client_id,
            engagement_code=folder.engagement_code,
        )

        return BoxApiOutput(folder_data=folder_data)

    async def _grant_folder_access(
        self, db: InMemoryDatabase, request: BoxApiInput
    ) -> BoxApiOutput:
        """Grant folder access to an employee."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")
        if not request.folder_id:
            raise Tool.ExecutionError("Missing required parameter: folder_id")
        if not request.permission_level:
            raise Tool.ExecutionError("Missing required parameter: permission_level")

        # Verify folder exists
        folder = db.get_by_id(Folder, request.folder_id)
        if not folder:
            raise Tool.ExecutionError(f"Folder not found: {request.folder_id}")

        # Generate new access log ID
        existing_logs = db.get_all(FolderAccessLog)
        existing_ids = {log.id for log in existing_logs}

        PREFIX_FOR_NEW_IDS = "FAL-2"
        count = 0
        while True:
            new_id = f"{PREFIX_FOR_NEW_IDS}-{count:06d}"
            if new_id not in existing_ids:
                break
            count += 1

        # Create access log entry
        access_log = FolderAccessLog(
            id=new_id,
            folder_id=request.folder_id,
            employee_email=request.email,
            permission_level=request.permission_level,
        )

        # Save to database
        db.create(access_log)

        return BoxApiOutput(success=True)
