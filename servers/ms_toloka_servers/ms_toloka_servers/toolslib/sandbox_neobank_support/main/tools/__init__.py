# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tools package for Sandbox Neobank Support."""

# Workday HR API
from .approval_api_check_status import CheckStatusTool

# Approval Workflow API
from .approval_api_create_request import CreateRequestTool
from .approver_lookup_api_get_contact_details import GetContactDetailsTool

# Approver Lookup API
from .approver_lookup_api_get_security_contact import GetApproverContactTool
from .asset_management_api_assign_device import AssignDeviceTool
from .asset_management_api_check_inventory import CheckInventoryTool
from .asset_management_api_get_device_details import GetDeviceDetailsTool

# Asset Management API
from .asset_management_api_get_employee_devices import GetEmployeeDevicesTool
from .asset_management_api_retire_device import RetireDeviceTool

# Email Notification API
from .email_notification_api_send_notification import (
    EmailNotificationSendNotificationTool,
)

# Hardware Procurement API
from .hardware_procurement_api_create_order import HardwareProcurementCreateOrderTool
from .license_management_api_allocate_license import LicenseAllocateTool
from .license_management_api_check_availability import LicenseCheckAvailabilityTool

# License Management API
from .license_management_api_check_license_type import LicenseCheckTypeTool
from .okta_api_add_to_group import OktaAddToGroupTool
from .okta_api_check_access import OktaCheckAccessTool
from .okta_api_get_user_groups import OktaGetUserGroupsTool

# Okta Access Management API
from .okta_api_provision_access import OktaProvisionAccessTool
from .okta_api_revoke_access import OktaRevokeAccessTool

# Okta Security Operations API
from .okta_security_api_execute_action import OktaSecurityExecuteActionTool

# Security Incident Management API
from .security_api_verify_incident import SecurityVerifyIncidentTool
from .workday_api_get_employee import WorkdayGetEmployeeTool
from .workday_api_get_manager_chain import WorkdayGetManagerChainTool
from .workday_api_get_org_structure import WorkdayGetOrgStructureTool

__all__ = [
    # Workday HR
    "WorkdayGetEmployeeTool",
    "WorkdayGetManagerChainTool",
    "WorkdayGetOrgStructureTool",
    # Okta Access Management
    "OktaProvisionAccessTool",
    "OktaCheckAccessTool",
    "OktaRevokeAccessTool",
    "OktaGetUserGroupsTool",
    "OktaAddToGroupTool",
    # Okta Security Operations
    "OktaSecurityExecuteActionTool",
    # Security Incident Management
    "SecurityVerifyIncidentTool",
    # Approver Lookup
    "GetApproverContactTool",
    "GetContactDetailsTool",
    # License Management
    "LicenseCheckTypeTool",
    "LicenseCheckAvailabilityTool",
    "LicenseAllocateTool",
    # Asset Management
    "GetEmployeeDevicesTool",
    "GetDeviceDetailsTool",
    "CheckInventoryTool",
    "AssignDeviceTool",
    "RetireDeviceTool",
    # Hardware Procurement
    "HardwareProcurementCreateOrderTool",
    # Approval Workflow
    "CreateRequestTool",
    "CheckStatusTool",
    # Email Notification
    "EmailNotificationSendNotificationTool",
]
