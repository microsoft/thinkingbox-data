# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tool implementation for IT Asset Management API (master tool)."""

from enum import Enum
from typing import Any, Dict, List, Optional, Type

from tb_business_ops_servers_202606.toolslib.sandbox_consulting.asset_management.models import (
    Device,
    DeviceAssignment,
    DeviceType,
    InventoryStatus,
    OfficeLocation,
)
from tb_business_ops_servers_202606.utils.sandbox_tools_system import (
    InMemoryDatabase,
    Tool,
    get_schema_without_refs,
)
from pydantic import BaseModel, ConfigDict, Field


class AssetManagementAction(str, Enum):
    """Asset Management API action enumeration."""

    GET_EMPLOYEE_DEVICES = "get_employee_devices"
    GET_DEVICE_DETAILS = "get_device_details"
    CHECK_INVENTORY = "check_inventory"
    RESERVE_DEVICE = "reserve_device"
    ASSIGN_DEVICE = "assign_device"
    RETIRE_DEVICE = "retire_device"


class AssetManagementApiInput(BaseModel):
    """Input for asset_management_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    action: AssetManagementAction = Field(
        ...,
        description="Action to perform",
        examples=["get_employee_devices"],
    )
    email: Optional[str] = Field(
        None,
        description="Employee email address (required for get_employee_devices, assign_device)",
        examples=["user@msg.com"],
    )
    asset_id: Optional[str] = Field(
        None,
        description="Device asset ID (required for get_device_details, assign_device, retire_device)",
        examples=["MSG00012345"],
    )
    device_type: Optional[DeviceType] = Field(
        None,
        description="Device type (required for check_inventory, reserve_device)",
        examples=["laptop"],
    )
    location: Optional[OfficeLocation] = Field(
        None,
        description="Office location (required for check_inventory, reserve_device)",
        examples=["New York"],
    )


class DeviceAssignmentOutput(BaseModel):
    """Device assignment output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    id: str = Field(..., description="Assignment ID")
    asset_id: str = Field(..., description="Device asset ID")
    employee_email: str = Field(..., description="Employee email address")
    returned_at: Optional[str] = Field(
        None, description="Date when device was returned"
    )


class DeviceDataOutput(BaseModel):
    """Device data output model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )

    id: str = Field(..., description="Asset ID")
    device_type: str = Field(..., description="Device type")
    model: str = Field(..., description="Device model")
    age_months: int = Field(..., description="Device age in months")
    inventory_status: str = Field(..., description="Inventory status")
    location: str = Field(..., description="Office location")


class AssetManagementApiOutput(BaseModel):
    """Output for asset_management_api master tool."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )

    devices: Optional[List[DeviceAssignmentOutput]] = Field(
        None,
        description="Array of device assignment records (for action=get_employee_devices)",
    )
    device_data: Optional[DeviceDataOutput] = Field(
        None,
        description="Device record from devices table (for action=get_device_details)",
    )
    available_count_by_model: Optional[Dict[str, int]] = Field(
        None,
        description="Count of available devices grouped by model (for action=check_inventory)",
    )
    reserved_asset_id: Optional[str] = Field(
        None,
        description="Asset ID of reserved device (for action=reserve_device)",
    )
    success: Optional[bool] = Field(
        None,
        description="Indicates if operation was successful (for assign_device, retire_device)",
    )


class AssetManagementApiTool(Tool):
    """Master tool implementation for IT Asset Management API."""

    @property
    def name(self) -> str:
        return "api"

    @property
    def description(self) -> str:
        return (
            "Manage hardware inventory and device assignments. Tracks devices, checks inventory "
            "availability, reserves and assigns hardware to employees. Use action parameter to "
            "specify the operation:\n\n"
            "- action='get_employee_devices': Lists all devices currently assigned to an employee. "
            "REQUIRES: email. Returns devices array with device assignment records from "
            "device_assignments table.\n\n"
            "- action='get_device_details': Retrieves detailed device information. REQUIRES: asset_id. "
            "Returns device_data object from devices table with ALL fields including id (asset_id), "
            "device_type, model, age_months, inventory_status, and location.\n\n"
            "- action='check_inventory': Checks availability of specific device type at a location. "
            "REQUIRES: device_type, location. Returns available_count_by_model dictionary mapping model "
            "names to counts of available devices (inventory_status=available).\n\n"
            "- action='reserve_device': Reserves an available device from inventory using FIFO "
            "(first-in-first-out). REQUIRES: device_type, location. Returns reserved_asset_id string. "
            "Selects first available device by lowest asset_id (FIFO ordering). Updates device "
            "inventory_status to reserved.\n\n"
            "- action='assign_device': Assigns a device to an employee. REQUIRES: email, asset_id. "
            "Returns success boolean. Creates record in device_assignments and updates device "
            "inventory_status to assigned.\n\n"
            "- action='retire_device': Marks device for return and removal from active inventory. "
            "REQUIRES: asset_id. Returns success boolean. Updates device inventory_status to retired.\n\n"
            "Always check inventory availability before promising device to user. Use get_employee_devices "
            "and get_device_details to assess current device eligibility for replacement."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(AssetManagementApiInput)

    @property
    def output_schema(self) -> Dict[str, Any]:
        return get_schema_without_refs(AssetManagementApiOutput)

    @property
    def request_model(self) -> Type[BaseModel]:
        return AssetManagementApiInput

    @property
    def output_model(self) -> Type[BaseModel]:
        return AssetManagementApiOutput

    async def run(
        self, db: InMemoryDatabase, request: AssetManagementApiInput
    ) -> AssetManagementApiOutput:
        """Execute Asset Management API action."""
        try:
            if request.action == AssetManagementAction.GET_EMPLOYEE_DEVICES:
                return await self._get_employee_devices(db, request)
            elif request.action == AssetManagementAction.GET_DEVICE_DETAILS:
                return await self._get_device_details(db, request)
            elif request.action == AssetManagementAction.CHECK_INVENTORY:
                return await self._check_inventory(db, request)
            elif request.action == AssetManagementAction.RESERVE_DEVICE:
                return await self._reserve_device(db, request)
            elif request.action == AssetManagementAction.ASSIGN_DEVICE:
                return await self._assign_device(db, request)
            elif request.action == AssetManagementAction.RETIRE_DEVICE:
                return await self._retire_device(db, request)
            else:
                raise Tool.ExecutionError(f"Invalid action: {request.action}")

        except Tool.ExecutionError:
            raise
        except Exception as e:
            error_message = f"Failed to execute Asset Management API action: {str(e)}"
            raise Tool.ExecutionError(error_message)

    async def _get_employee_devices(
        self, db: InMemoryDatabase, request: AssetManagementApiInput
    ) -> AssetManagementApiOutput:
        """Get all devices currently assigned to an employee."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")

        # Get all device assignments
        all_assignments = db.get_all(DeviceAssignment)

        # Filter assignments for the employee where returned_at is null (currently assigned)
        employee_assignments = [
            assignment
            for assignment in all_assignments
            if assignment.employee_email == request.email
            and assignment.returned_at is None
        ]

        # Convert to output format
        devices = [
            DeviceAssignmentOutput(
                id=assignment.id,
                asset_id=assignment.asset_id,
                employee_email=assignment.employee_email,
                returned_at=(
                    assignment.returned_at.isoformat()
                    if assignment.returned_at
                    else None
                ),
            )
            for assignment in employee_assignments
        ]

        return AssetManagementApiOutput(devices=devices)

    async def _get_device_details(
        self, db: InMemoryDatabase, request: AssetManagementApiInput
    ) -> AssetManagementApiOutput:
        """Get detailed device information by asset ID."""
        if not request.asset_id:
            raise Tool.ExecutionError("Missing required parameter: asset_id")

        # Get device by asset ID
        device = db.get_by_id(Device, request.asset_id)

        # If no device found, raise 404 error
        if not device:
            raise Tool.ExecutionError(f"Device not found: {request.asset_id}")

        # Return ALL device fields
        device_data = DeviceDataOutput(
            id=device.id,
            device_type=device.device_type.value,
            model=device.model,
            age_months=device.age_months,
            inventory_status=device.inventory_status.value,
            location=device.location.value,
        )

        return AssetManagementApiOutput(device_data=device_data)

    async def _check_inventory(
        self, db: InMemoryDatabase, request: AssetManagementApiInput
    ) -> AssetManagementApiOutput:
        """Check availability of specific device type at a location."""
        if not request.device_type:
            raise Tool.ExecutionError("Missing required parameter: device_type")
        if not request.location:
            raise Tool.ExecutionError("Missing required parameter: location")

        # Get all devices
        all_devices = db.get_all(Device)

        # Group available devices by model
        available_count_by_model: Dict[str, int] = {}
        for device in all_devices:
            if (
                device.device_type == request.device_type
                and device.location == request.location
                and device.inventory_status == InventoryStatus.AVAILABLE
            ):
                model = device.model
                available_count_by_model[model] = (
                    available_count_by_model.get(model, 0) + 1
                )

        return AssetManagementApiOutput(
            available_count_by_model=available_count_by_model
        )

    async def _reserve_device(
        self, db: InMemoryDatabase, request: AssetManagementApiInput
    ) -> AssetManagementApiOutput:
        """Reserve an available device using FIFO (first-in-first-out)."""
        if not request.device_type:
            raise Tool.ExecutionError("Missing required parameter: device_type")
        if not request.location:
            raise Tool.ExecutionError("Missing required parameter: location")

        # Get all devices
        all_devices = db.get_all(Device)

        # Filter available devices matching type and location
        available_devices = [
            device
            for device in all_devices
            if device.device_type == request.device_type
            and device.location == request.location
            and device.inventory_status == InventoryStatus.AVAILABLE
        ]

        # If no available devices, raise error
        if not available_devices:
            raise Tool.ExecutionError(
                f"No available {request.device_type} devices at {request.location}"
            )

        # Sort by ID (FIFO - lowest ID first) and select first one
        available_devices.sort(key=lambda d: d.id)
        device_to_reserve = available_devices[0]

        # Update device status to reserved
        device_to_reserve.inventory_status = InventoryStatus.RESERVED
        db.update(device_to_reserve)

        return AssetManagementApiOutput(reserved_asset_id=device_to_reserve.id)

    async def _assign_device(
        self, db: InMemoryDatabase, request: AssetManagementApiInput
    ) -> AssetManagementApiOutput:
        """Assign a device to an employee."""
        if not request.email:
            raise Tool.ExecutionError("Missing required parameter: email")
        if not request.asset_id:
            raise Tool.ExecutionError("Missing required parameter: asset_id")

        # Get device by asset ID
        device = db.get_by_id(Device, request.asset_id)

        # If no device found, raise 404 error
        if not device:
            raise Tool.ExecutionError(f"Device not found: {request.asset_id}")

        # Generate assignment ID
        existing_assignments = db.get_all(DeviceAssignment)
        PREFIX_FOR_NEW_IDS = "ASMT-2"
        count = 0
        existing_ids = {assignment.id for assignment in existing_assignments}

        while True:
            new_id = f"{PREFIX_FOR_NEW_IDS}-{count:06d}"
            if new_id not in existing_ids:
                break
            count += 1

        # Create device assignment
        new_assignment = DeviceAssignment(
            id=new_id,
            asset_id=request.asset_id,
            employee_email=request.email,
            returned_at=None,
        )
        db.create(new_assignment)

        # Update device status to assigned
        device.inventory_status = InventoryStatus.ASSIGNED
        db.update(device)

        return AssetManagementApiOutput(success=True)

    async def _retire_device(
        self, db: InMemoryDatabase, request: AssetManagementApiInput
    ) -> AssetManagementApiOutput:
        """Retire a device from active inventory."""
        if not request.asset_id:
            raise Tool.ExecutionError("Missing required parameter: asset_id")

        # Get device by asset ID
        device = db.get_by_id(Device, request.asset_id)

        # If no device found, raise 404 error
        if not device:
            raise Tool.ExecutionError(f"Device not found: {request.asset_id}")

        # Update device status to retired
        device.inventory_status = InventoryStatus.RETIRED
        db.update(device)

        return AssetManagementApiOutput(success=True)
