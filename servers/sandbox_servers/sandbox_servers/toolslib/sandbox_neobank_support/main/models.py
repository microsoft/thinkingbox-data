# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Data models for Sandbox Banking MCP server."""

from datetime import date, datetime
from enum import Enum
from typing import Annotated, ClassVar, List, Optional

from sandbox_servers.utils.sandbox_tools_system import UnstableField
from pydantic import BaseModel, ConfigDict, Field

# ==================== Enums ====================


class ApprovalRequestType(str, Enum):
    """Types of approval requests"""

    ACCESS_REQUEST = "access_request"
    HARDWARE_PURCHASE = "hardware_purchase"
    DATA_EXPORT = "data_export"
    LICENSE_PURCHASE = "license_purchase"
    EXCEPTION_REQUEST = "exception_request"


class ApprovalRequestStatus(str, Enum):
    """Status of approval requests"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ApprovalUrgency(str, Enum):
    """Urgency levels for approval requests"""

    STANDARD = "standard"
    URGENT = "urgent"
    CRITICAL = "critical"


class AvailabilityStatus(str, Enum):
    """Employee availability status"""

    AVAILABLE = "available"
    ON_LEAVE = "on_leave"
    UNAVAILABLE = "unavailable"


class GenericAccessLevel(str, Enum):
    """Generic access levels used across multiple systems - EXPANDED for v4"""

    NONE = "none"
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    WRITE = "write"
    ADMIN = "admin"
    MEMBER = "member"
    USER = "user"
    VIEWER = "viewer"
    EDITOR = "editor"
    ANALYST = "analyst"
    STANDARD = "standard"
    ELEVATED = "elevated"
    STANDARD_EMPLOYEE = "standard_employee"
    WRITE_NON_PII_ONLY = "write non-PII only"
    ENGINEER_PROD = "engineer_prod"


class Severity(str, Enum):
    """Security incident severity levels"""

    SEV1 = "SEV1"
    SEV2 = "SEV2"
    SEV3 = "SEV3"
    SEV4 = "SEV4"


class OktaSecurityOperation(str, Enum):
    """Okta security operations for execute_action"""

    SEND_VERIFICATION_MANAGER = "send_verification_manager"
    SEND_VERIFICATION_ASSISTANT = "send_verification_assistant"
    SEND_VERIFICATION_SMS = "send_verification_sms"
    SEND_VERIFICATION_VIDEO_CALL = "send_verification_video_call"
    UNLOCK_ACCOUNT = "unlock_account"
    FORCE_PASSWORD_RESET = "force_password_reset"
    INVALIDATE_ALL_SESSIONS = "invalidate_all_sessions"
    SET_TEMPORARY_BYPASS = "set_temporary_bypass"
    ADD_MFA_DEVICE = "add_mfa_device"
    SEND_MFA_ENROLLMENT_LINK = "send_mfa_enrollment_link"
    REMOVE_MFA_DEVICE = "remove_mfa_device"


class DataSensitivity(str, Enum):
    """Data sensitivity classifications"""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    CUSTOMER_PII = "customer_pii"
    FINANCIAL_DATA = "financial_data"
    COMPLIANCE_RESTRICTED = "compliance_restricted"


class ProcurementOrderStatus(str, Enum):
    """Status of hardware procurement orders"""

    PENDING = "pending"
    ORDERED = "ordered"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class NotificationType(str, Enum):
    """Types of email notifications"""

    ACCESS_PROVISIONED = "access_provisioned"
    ACCESS_REVOKED = "access_revoked"
    INCIDENT_ACCESS_GRANTED = "incident_access_granted"
    POST_FACTO_MANAGER_ALERT = "post_facto_manager_alert"
    BREAKING_GLASS_ALERT = "breaking_glass_alert"
    HARDWARE_ASSIGNED = "hardware_assigned"
    HARDWARE_ORDERED = "hardware_ordered"
    TICKET_UPDATE = "ticket_update"
    ESCALATION_NOTICE = "escalation_notice"


class EmailPriority(str, Enum):
    """Email priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmploymentStatus(str, Enum):
    """Employment status"""

    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    DEPARTING = "departing"
    TERMINATED = "terminated"


class Department(str, Enum):
    """Department names"""

    EXECUTIVE_LEADERSHIP = "executive_leadership"
    PRODUCT_ENGINEERING = "product_engineering"
    CUSTOMER_SUPPORT = "customer_support"
    SALES = "sales"
    MARKETING = "marketing"
    FINANCE_ACCOUNTING = "finance_accounting"
    HR = "hr"
    LEGAL = "legal"
    COMPLIANCE_RISK = "compliance_risk"
    IT_SECURITY = "it_security"
    IT_OPERATIONS = "it_operations"


class Office(str, Enum):
    """Office locations"""

    SF = "sf"
    NYC = "nyc"
    AUSTIN = "austin"
    REMOTE = "remote"


class OfficeLocation(str, Enum):
    """Office location values."""

    SF = "sf"
    NYC = "nyc"
    AUSTIN = "austin"
    REMOTE = "remote"


class LicenseType(str, Enum):
    """License type values."""

    STANDARD = "standard"
    ENTERPRISE = "enterprise"
    INDIVIDUAL = "individual"
    UNLIMITED = "unlimited"


class DeviceType(str, Enum):
    """Device type values."""

    LAPTOP_STANDARD = "laptop_standard"
    LAPTOP_PREMIUM = "laptop_premium"
    MONITOR = "monitor"
    DOCKING_STATION = "docking_station"
    HEADSET = "headset"
    KEYBOARD = "keyboard"
    MOUSE = "mouse"


class WarehouseLocation(str, Enum):
    """Warehouse location values."""

    SF = "sf"
    NYC = "nyc"
    AUSTIN = "austin"
    REMOTE_SHIP = "remote_ship"


class DeviceCondition(str, Enum):
    """Device condition values."""

    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    RETIRED = "retired"


class BIAccessGroup(str, Enum):
    """BI access group values."""

    BI_MARKETING_VIEWERS = "bi_marketing_viewers"
    BI_FINANCE_VIEWERS = "bi_finance_viewers"
    BI_EXECUTIVE = "bi_executive"
    BI_PRODUCT_ANALYTICS = "bi_product_analytics"
    BI_OPERATIONS = "bi_operations"
    BI_COMPLIANCE = "bi_compliance"


class EmailDeliveryStatus(str, Enum):
    """Email delivery status values."""

    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


# ==================== Models ====================


class Employee(BaseModel):
    """Employee model from Workday HRIS."""

    id: str = Field(..., description="Unique identifier (format: WD-######)")
    email: str = Field(..., description="Corporate email address")
    full_name: str = Field(..., description="Employee's full name")
    level: int = Field(..., description="Employee level (1-8+)")
    department: Department = Field(..., description="Department enum value")
    role: str = Field(..., description="Job title/role")
    office_location: OfficeLocation = Field(
        ..., description="Office location or remote"
    )
    start_date: str = Field(..., description="Employment start date in ISO 8601 format")
    manager_id: Optional[str] = Field(None, description="Manager's Workday ID")
    employment_status: EmploymentStatus = Field(
        default=EmploymentStatus.ACTIVE, description="Current employment status"
    )
    is_contractor: bool = Field(
        default=False, description="Whether employee is a contractor"
    )
    remote_delivery_address: Optional[str] = Field(
        None, description="For remote workers: Remote delivery address"
    )
    contract_end_date: Optional[str] = Field(
        None, description="For contractors only: Contract end date in ISO 8601 format"
    )

    def get_id(self) -> str:
        """Return the unique identifier for this employee."""
        return self.id


class OktaAppAccess(BaseModel):
    """Okta application access record."""

    id: str = Field(..., description="Unique identifier (format: OAA-########)")
    employee_id: str = Field(..., description="Employee ID reference")
    app_name: str = Field(..., description="Application name")
    access_level: GenericAccessLevel = Field(..., description="Access level")
    granted_at: Optional[str] = Field(
        None, description="Timestamp when granted in ISO 8601 format"
    )
    granted_by: str = Field(..., description="Who granted the access")
    is_active: bool = Field(default=True, description="Whether access is active")
    revoked_at: Optional[str] = Field(
        None, description="Timestamp when revoked in ISO 8601 format"
    )
    is_temporary: bool = Field(default=False, description="Whether access is temporary")
    expires_at: Optional[str] = Field(
        None, description="Expiration timestamp in ISO 8601 format"
    )

    def get_id(self) -> str:
        """Return the unique identifier for this access record."""
        return self.id


class OktaGroupMembership(BaseModel):
    """Okta group membership record."""

    id: str = Field(..., description="Unique identifier (format: OGM-########)")
    employee_id: str = Field(..., description="Employee ID reference")
    group_name: str = Field(..., description="Group name")
    added_at: Optional[str] = Field(
        None, description="Timestamp when added in ISO 8601 format"
    )
    added_by: str = Field(..., description="Who added to group")
    is_active: bool = Field(default=True, description="Whether membership is active")

    def get_id(self) -> str:
        """Return the unique identifier for this membership."""
        return self.id


class SoftwareLicense(BaseModel):
    """Software license pool inventory."""

    id: str = Field(..., description="Unique identifier (format: LIC-########)")
    software_name: str = Field(..., description="Software product name")
    license_type: LicenseType = Field(..., description="Type of license pool")
    total_licenses: Optional[int] = Field(
        None, description="Total licenses in pool (null for unlimited)"
    )
    annual_cost_per_license: Optional[int] = Field(
        None, description="Annual cost per license in USD"
    )

    def get_id(self) -> str:
        """Return the unique identifier for this license."""
        return self.id


class LicenseAllocation(BaseModel):
    """Individual license allocation to employee."""

    id: str = Field(..., description="Unique identifier (format: LAL-########)")
    license_id: str = Field(..., description="License pool ID reference")
    employee_id: str = Field(..., description="Employee ID reference")
    allocated_at: Optional[str] = Field(
        None, description="Timestamp when allocated in ISO 8601 format"
    )
    allocated_by: str = Field(..., description="Who allocated the license")
    is_active: bool = Field(default=True, description="Whether allocation is active")
    deallocated_at: Optional[str] = Field(
        None, description="Timestamp when deallocated in ISO 8601 format"
    )

    def get_id(self) -> str:
        """Return the unique identifier for this allocation."""
        return self.id


class HardwareAsset(BaseModel):
    """Hardware asset inventory record."""

    id: str = Field(..., description="Unique identifier (format: VDB-HW-#####)")
    device_type: DeviceType = Field(..., description="Type of device")
    device_model: str = Field(..., description="Model name")
    purchase_date: str = Field(
        ..., description="When device was purchased in ISO 8601 format"
    )
    warehouse_location: WarehouseLocation = Field(
        ..., description="Location of the device"
    )
    condition: DeviceCondition = Field(
        default=DeviceCondition.NEW, description="Current condition"
    )
    is_assigned: bool = Field(default=False, description="Whether device is assigned")

    def get_id(self) -> str:
        """Return the unique identifier for this asset."""
        return self.id


class AssetAssignment(BaseModel):
    """Hardware asset assignment to employee."""

    id: str = Field(..., description="Unique identifier (format: ASN-########)")
    asset_id: str = Field(..., description="Asset ID reference")
    employee_id: str = Field(..., description="Employee ID reference")
    assigned_at: Optional[str] = Field(
        None, description="Timestamp when assigned in ISO 8601 format"
    )
    assigned_by: str = Field(..., description="Who assigned the asset")
    is_active: bool = Field(default=True, description="Whether assignment is active")
    returned_at: Optional[str] = Field(
        None, description="Timestamp when returned in ISO 8601 format"
    )

    def get_id(self) -> str:
        """Return the unique identifier for this assignment."""
        return self.id


# ============================================================================
# DATABASE MODELS
# ============================================================================


class ApprovalRequest(BaseModel):
    """Approval request in the workflow system"""

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, validate_assignment=True
    )
    table_name: ClassVar[str] = "approval_requests"

    id: str = Field(..., description="Approval request ID")
    request_type: ApprovalRequestType = Field(
        ..., description="Type of approval request"
    )
    requester_id: str = Field(..., description="Requester's employee ID")
    approver_id: str = Field(..., description="Approver's employee ID")
    status: ApprovalRequestStatus = Field(..., description="Current status")
    urgency: ApprovalUrgency = Field(
        default=ApprovalUrgency.STANDARD, description="Urgency level"
    )
    details: Annotated[str, UnstableField()] = Field(
        ..., description="Details of the request"
    )
    ticket_id: Optional[str] = Field(None, description="Associated ticket ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    decided_at: Optional[datetime] = Field(None, description="Decision timestamp")
    approver_feedback: Optional[str] = Field(None, description="Feedback from approver")

    def get_id(self) -> str:
        """Return the ID of this approval request."""
        return self.id


class CustomerAccount(BaseModel):
    """Customer accounts in Core Banking system"""

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, validate_assignment=True
    )
    table_name: ClassVar[str] = "customer_accounts"

    id: str = Field(..., description="Customer ID")
    account_number: str = Field(..., description="Account number")
    account_type: str = Field(
        ..., description="Account type (checking, savings, credit_card, money_market)"
    )
    status: str = Field(..., description="Account status (active, suspended, closed)")
    balance: float = Field(..., description="Current account balance")
    currency: str = Field(default="USD", description="Account currency")
    opened_date: str = Field(
        ..., description="Date when account was opened (YYYY-MM-DD)"
    )

    def get_id(self) -> str:
        """Return the ID of this customer account."""
        return self.id


class ProcurementOrder(BaseModel):
    """Hardware procurement orders"""

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, validate_assignment=True
    )
    table_name: ClassVar[str] = "procurement_orders"

    id: str = Field(..., description="Order ID")
    device_type: DeviceType = Field(..., description="Device type ordered")
    device_model: str = Field(..., description="Device model")
    quantity: int = Field(..., description="Quantity ordered")
    ship_to_location: str = Field(..., description="Shipping address")
    requester_id: str = Field(..., description="Requester employee ID")
    ticket_id: Optional[str] = Field(None, description="Associated ticket ID")
    status: ProcurementOrderStatus = Field(
        default=ProcurementOrderStatus.PENDING, description="Order status"
    )
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    expected_delivery_date: date = Field(
        ..., description="Expected delivery date (YYYY-MM-DD)"
    )
    delivered_at: Optional[datetime] = Field(None, description="Delivery timestamp")

    def get_id(self) -> str:
        """Return the ID of this order."""
        return self.id


class EmailNotification(BaseModel):
    """Email notifications sent to employees"""

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, validate_assignment=True
    )
    table_name: ClassVar[str] = "email_notifications"

    id: str = Field(..., description="Notification ID")
    recipient_id: str = Field(..., description="Recipient employee ID")
    recipient_email: str = Field(..., description="Recipient email address")
    notification_type: NotificationType = Field(..., description="Type of notification")
    subject: Annotated[str, UnstableField()] = Field(..., description="Email subject")
    body: Annotated[str, UnstableField()] = Field(..., description="Email body")
    ticket_id: Optional[str] = Field(None, description="Associated ticket ID")
    priority: EmailPriority = Field(
        default=EmailPriority.NORMAL, description="Email priority"
    )
    cc_emails: Optional[List[str]] = Field(None, description="CC email addresses")
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp")
    delivery_status: EmailDeliveryStatus = Field(
        default=EmailDeliveryStatus.QUEUED, description="Delivery status"
    )
    delivered_at: Optional[datetime] = Field(None, description="Delivery timestamp")
    sent_by: str = Field(..., description="Who sent the notification")

    def get_id(self) -> str:
        """Return the ID of this notification."""
        return self.id


class SecurityIncident(BaseModel):
    """Security incident records"""

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, validate_assignment=True
    )
    table_name: ClassVar[str] = "security_incidents"

    id: str = Field(..., description="Incident ID (format: SEC-########)")
    employee_id: str = Field(..., description="Employee ID affected")
    severity: Severity = Field(..., description="Incident severity (SEV1-SEV4)")
    incident_type: str = Field(..., description="Type of security incident")
    description: str = Field(..., description="Incident description")
    status: str = Field(
        ..., description="Incident status (open, investigating, resolved)"
    )
    is_active: bool = Field(..., description="Whether incident is currently active")
    reported_at: datetime = Field(..., description="When incident was reported")
    reported_by: str = Field(..., description="Who reported the incident")
    resolved_at: Optional[datetime] = Field(
        None, description="When incident was resolved"
    )
    resolution_notes: Optional[str] = Field(None, description="Resolution details")

    def get_id(self) -> str:
        """Return the ID of this incident."""
        return self.id


class OktaSecurityAudit(BaseModel):
    """Audit log for Okta security operations"""

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, validate_assignment=True
    )
    table_name: ClassVar[str] = "okta_security_audit"

    id: str = Field(..., description="Audit log ID (format: OSA-########)")
    employee_id: str = Field(..., description="Employee ID affected")
    operation: OktaSecurityOperation = Field(
        ..., description="Security operation performed"
    )
    performed_by: str = Field(..., description="Who performed the operation")
    performed_at: datetime = Field(..., description="When operation was performed")
    reason: str = Field(..., description="Reason for the operation")
    ticket_id: Optional[str] = Field(None, description="Associated ticket ID")
    verification_method: Optional[str] = Field(
        None, description="Verification method used"
    )
    success: bool = Field(default=True, description="Whether operation succeeded")
    bypass_duration_hours: Optional[int] = Field(
        None, description="Duration of MFA bypass in hours (for set_temporary_bypass)"
    )
    bypass_expires_at: Optional[datetime] = Field(
        None,
        description="Expiration timestamp for MFA bypass (for set_temporary_bypass)",
    )
    mfa_device_id: Optional[str] = Field(
        None,
        description="MFA device ID (for add_mfa_device/remove_mfa_device operations)",
    )

    def get_id(self) -> str:
        """Return the ID of this audit log entry."""
        return self.id
