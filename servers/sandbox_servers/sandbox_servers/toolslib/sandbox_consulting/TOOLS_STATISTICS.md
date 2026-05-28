# Tools Statistics by App

## Summary

Total Tools: 18 function names across 13 applications

## Breakdown by Application

### 1. Internal Software Catalog (2 tools)
- `software_catalog_search` - Search for software in approved catalog
- `software_catalog_get_details` - Retrieve detailed software information

### 2. Salesforce CRM (2 tools)
- `salesforce_get_engagement` - Retrieve engagement details from CRM
- `salesforce_check_employee_assignment` - Validate employee assignment to engagement

### 3. Workday HCM (1 tool)
- `workday_api` - Access employee profile data (master tool with action parameter)

### 4. Okta Identity Management (1 tool)
- `okta_provision_access` - Provision application access via SSO

### 5. Mavenlink Resource Management (1 tool)
- `mavenlink_api` - Access engagement and employee assignment data (master tool with actions: get_engagement, get_employee_assignments, validate_engagement_code)

### 6. SAP Concur Travel & Expense (1 tool)
- `concur_api` - Manage travel and expense reporting (master tool with actions: get_expense_report, override_expense_rejection)

### 7. Internal IT Asset Management System (1 tool)
- `asset_management_api` - Manage hardware inventory and device assignments (master tool with actions: get_employee_devices, get_device_details, check_inventory, reserve_device, assign_device, retire_device)

### 8. Internal License Management Platform (1 tool)
- `license_management_api` - Manage software licenses and allocations (master tool with actions: check_availability, allocate, get_cost)

### 9. Degreed Learning Management System (1 tool)
- `degreed_api` - Access training courses, enrollment, and certification tracking (master tool with actions: search_courses, get_course_details, check_enrollment, enroll_employee, get_training_history, check_certification_status, get_required_trainings)

### 10. Internal Client Access Management Platform (1 tool)
- `client_access_api` - Manage VPN access and client system provisioning (master tool with actions: provision_vpn, check_vpn_access, revoke_vpn, provision_client_system, check_client_requirements, get_employee_prerequisites)

### 11. Internal Approval Workflow System (1 tool)
- `approval_create_request` - Create approval request in workflow system

### 12. Sterling BackCheck (1 tool)
- `background_check_api` - Manage background checks and security clearances (master tool with actions: get_status, initiate, get_timeline)

### 13. Internal NDA Management System (1 tool)
- `nda_api` - Manage NDA signing and tracking (master tool with actions: check_status, send_for_signature)

### 14. Box Document Management (1 tool)
- `box_api` - Manage document folder access (master tool with actions: get_folder_details, grant_folder_access)

### 15. Internal Approver Lookup Service (1 tool)
- `approver_lookup_get_contact` - Retrieve approver contact information and availability

### 16. Internal Hardware Procurement Connector (1 tool)
- `hardware_procurement_create_order` - Place hardware order with vendor

## Master Tools vs Separate Tools

### Master Tools (10)
Tools that use action parameter to multiplex operations:
1. `workday_api` (1 action)
2. `mavenlink_api` (3 actions)
3. `concur_api` (2 actions)
4. `asset_management_api` (6 actions)
5. `license_management_api` (3 actions)
6. `degreed_api` (7 actions)
7. `client_access_api` (6 actions)
8. `background_check_api` (3 actions)
9. `nda_api` (2 actions)
10. `box_api` (2 actions)

### Separate Tools (8)
Individual function-based tools:
1. `software_catalog_search`
2. `software_catalog_get_details`
3. `salesforce_get_engagement`
4. `salesforce_check_employee_assignment`
5. `okta_provision_access`
6. `approval_create_request`
7. `approver_lookup_get_contact`
8. `hardware_procurement_create_order`

## Implementation Priority

### Phase 1: Internal Software Catalog (CURRENT)
- Simple read-only tools
- No complex dependencies
- Foundation for license management workflows

### Phase 2: Core HR & Engagement Tools
- Workday, Salesforce, Mavenlink
- Foundation for all workflows

### Phase 3: Access & Provisioning
- Okta, Client Access, NDA, Background Check
- Depends on HR data

### Phase 4: Resource Management
- Asset Management, License Management, Hardware Procurement
- Depends on approval workflows

### Phase 5: Training & Document Access
- Degreed, Box
- Support tools

### Phase 6: Approval & Expense
- Approval Workflow, Concur, Approver Lookup
- Cross-cutting concerns
