# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

from thinkingbox.common import Judge, TestContext
from thinkingbox.common.chat_types import Text

"""!
scenario: external_booking_v1
"""
SERVER_NAME = "external_booking_v1"


def validate_database(x: TestContext):
    result_db_hash = x.effects[SERVER_NAME]["result_db_hash"]
    golden_db_hash = x.effects[SERVER_NAME]["golden_db_hash"]

    if result_db_hash != golden_db_hash:
        diff = x.effects[SERVER_NAME].get("diff", [])
        error_msg = (
            "Database hash after test execution does not match "
            "expected golden hash\n"
        )
        error_msg += f"Result hash: {result_db_hash}\n"
        error_msg += f"Golden hash: {golden_db_hash}\n"

        if diff:
            error_msg += f"\nFound {len(diff)} difference(s):\n"
            for i, d in enumerate(diff, 1):
                error_msg += f"\n{i}. Path: {d.get('path', 'N/A')}\n"
                error_msg += f"   Type: {d.get('type', 'N/A')}\n"
                result_json = json.dumps(
                    d.get("result"), ensure_ascii=False, indent=11
                )[0:500]
                golden_json = json.dumps(
                    d.get("golden"), ensure_ascii=False, indent=11
                )[0:500]
                error_msg += f"   Result:  {result_json}\n"
                error_msg += f"   Golden:  {golden_json}\n"

        assert False, error_msg


def validate_rubrics_yesno(x: TestContext, judge: Judge):
    rubrics = x.effects[SERVER_NAME].get("rubrics_yesno", [])
    for rubric in rubrics:
        assert judge.text_yesno(x.response, rubric), f"Rubric yesno failed: {rubric}"


def test_bmd_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I have a booking for today and I need to make a change. My name is Victoria Martinez, email victoria.martinez@outlook.com, and my booking reference is BKG-33754330. I'd like to upgrade my meal plan from half board to full board. We're checking in this evening with my family. Is this possible?
    user_context: |
        You are Victoria Martinez, a VIP customer contacting StayBridge support to change your board type from half_board to full_board for your booking today. You're traveling with family (2 adults, 2 children) and checking in this evening at the Riverside Luxury Hotel in Chicago.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If the agent informs you about fees or charges for the modification, accept them and confirm you want to proceed.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-33754330
              booking_reference: BKG-33754330
              customer_id: CUS-33754330
              hotel_id: HTL-33754330
              check_in_date: "2025-10-01T18:00:00Z"
              check_out_date: "2025-10-03T11:00:00Z"
              room_type: suite
              board_type: half_board
              adults_count: 2
              children_count: 2
              booking_status: confirmed
              booking_value: '890.00'
              modification_history:
                - "2025-09-28T10:00:00Z: room_type: standard_room -> suite"
              special_requests: []
              corporate_account_id: null
              group_booking_id: null
              created_at: "2025-09-20T10:00:00Z"
              updated_at: "2025-09-28T10:00:00Z"
          crm_api_customer_profiles:
            - id: CUS-33754330
              customer_id: CUS-33754330
              email: victoria.martinez@outlook.com
              full_name: Victoria Martinez
              vip_tier: vip
              loyalty_program_status: active
              lifetime_value: '4560.75'
              total_bookings_count: 12
              preferences:
                - quiet room
                - high floor
              special_notes:
                - prefers email communication
              complaint_count: 0
              last_booking_date: "2025-09-20T10:00:00Z"
              created_at: "2024-06-15T10:00:00Z"
              updated_at: "2025-09-20T10:00:00Z"
          hotel_partner_api_hotels:
            - id: HTL-33754330
              hotel_id: HTL-33754330
              hotel_name: Riverside Luxury Hotel
              location: Chicago
              partner_tier: premium
              contact_name: Catherine Reynolds
              contact_email: creynolds@riversluxury.com
              contact_phone: +1-312-485-7290
              escalation_contact: director@riversluxury.com
              amenities:
                - pool
                - spa
                - fitness_center
                - restaurant
              supports_pets: true
              accessible_rooms_available: true
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
          zendesk_users:
            - id: USR-10000007
              name: Victoria Martinez
              email: victoria.martinez@outlook.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-312-594-8176
              verified: true
              active: true
              created_at: "2024-06-15T00:00:00Z"
              updated_at: "2024-06-15T00:00:00Z"
          zendesk_tickets:
            - id: TCK-36541458
              subject: Billing inquiry for booking BKG-33754330
              description: Customer has a question about charges on their recent booking invoice
              status: solved
              priority: normal
              type: question
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: ORG-10000002
              tags:
                - billing
                - inquiry
              created_at: "2025-09-29T13:00:00Z"
              updated_at: "2025-09-29T15:00:00Z"
              due_at: null
              booking_reference: BKG-33754330
              hotel_id: HTL-33754330
              check_in_date: "2025-10-01T18:00:00Z"
              booking_value: 890.0
              request_type_detail: billing-inquiry
              corporate_account_id: null
              group_booking_id: null
              resolution_action: information-provided
              refund_amount: null
              escalation_reason: null
          booking_api_hotel_inventory:
            - id: INV-33754001
              hotel_id: HTL-33754330
              room_type: suite
              board_type: full_board
              date: "2025-10-01T00:00:00Z"
              available_count: 2
              price_per_night: '475.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-33754002
              hotel_id: HTL-33754330
              room_type: suite
              board_type: full_board
              date: "2025-10-02T00:00:00Z"
              available_count: 2
              price_per_night: '475.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-33754003
              hotel_id: HTL-33754330
              room_type: suite
              board_type: half_board
              date: "2025-10-01T00:00:00Z"
              available_count: 2
              price_per_night: '445.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-33754004
              hotel_id: HTL-33754330
              room_type: suite
              board_type: half_board
              date: "2025-10-02T00:00:00Z"
              available_count: 2
              price_per_night: '445.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-33754005
              hotel_id: HTL-33754330
              room_type: suite
              board_type: with_breakfast
              date: "2025-10-01T00:00:00Z"
              available_count: 2
              price_per_night: '420.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-33754006
              hotel_id: HTL-33754330
              room_type: suite
              board_type: with_breakfast
              date: "2025-10-02T00:00:00Z"
              available_count: 2
              price_per_night: '420.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-33754007
              hotel_id: HTL-33754330
              room_type: suite
              board_type: without_breakfast
              date: "2025-10-01T00:00:00Z"
              available_count: 2
              price_per_night: '395.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-33754008
              hotel_id: HTL-33754330
              room_type: suite
              board_type: without_breakfast
              date: "2025-10-02T00:00:00Z"
              available_count: 2
              price_per_night: '395.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
          booking_api_group_bookings: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-33754330
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-33754330
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-33754330
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: "email eq 'victoria.martinez@outlook.com'"
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "booking_reference eq 'BKG-33754330'"
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-33754330
                check_in_date: "2025-10-01T18:00:00Z"
                check_out_date: "2025-10-03T11:00:00Z"
                room_type: suite
                board_type: full_board
                adults_count: 2
                children_count: 2
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Board type modification request - BKG-33754330
                  description: "Customer requests board type change from half_board to full_board for booking BKG-33754330. Check-in: 2025-10-01T18:00:00Z (today, same-day modification). Premium partner hotel. Customer VIP tier: vip - hotel escalation not required per policy 4.1.5. Availability verified. Fee calculation: Base fee $60 × 0.5 (premium tier) + $15 surcharge (2nd modification) = $45 modification fee. Price difference: $60. Total charge: $105."
                  status: open
                  priority: urgent
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-today
                    - vip-customer
                  booking_reference: BKG-33754330
                  hotel_id: HTL-33754330
                  request_type_detail: modify-board-type
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-33754330
                board_type: full_board
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-33754330
                charge_amount: '105.00'
                reason: board_type_modification_fee_and_price_difference
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  tags:
                    - b2c-customer
                    - check-in-today
                    - vip-customer
                  booking_reference: BKG-33754330
                  hotel_id: HTL-33754330
                  check_in_date: "2025-10-01T18:00:00Z"
                  booking_value: 950.0
                  request_type_detail: modify-board-type
                  resolution_action: modification-completed
                  refund_amount: 0
        rubrics_yesno:
          - "Policy states: 'Do not share hotel commission rates or partner tier classifications with customers.' Does the agent's final message avoid revealing the hotel's partner tier classification (e.g., 'premium', 'standard', 'budget')? (Yes = does not reveal the tier classification or does not touch the topic, No = reveals it)"
          - "Policy states (Section 6.3 Customer Communication at Resolution): 'Provide reference numbers (transaction_id, booking_reference).' IF the agent's final message confirms that a payment charge was processed, does it include the transaction ID? (Yes = transaction ID included or no charge mentioned, No = charge confirmed but transaction ID not provided)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


def test_bmd_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I have a booking coming up and I'd like to add late checkout to my reservation. My booking reference is BKG-60883561 and my email is marcus.wellington@techventures.io. Can you help me with this?
    user_context: |
        You are Marcus Wellington, a VIP customer contacting StayBridge support to add late checkout to your upcoming hotel booking at The Belmont Residences. Your check-in is October 2nd.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If the agent informs you about a fee for late checkout (such as $30), confirm that you want to proceed and accept the charge.
        - You want late checkout until 2 PM.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-60883561
              booking_reference: BKG-60883561
              customer_id: CUS-60883561
              hotel_id: HTL-60883561
              check_in_date: "2025-10-02T12:00:00Z"
              check_out_date: "2025-10-04T11:00:00Z"
              booking_value: '1250.00'
              room_type: executive_suite
              board_type: full_board
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history:
                - "2025-09-15T10:00:00Z: check_in_date: 2025-10-01T12:00:00Z -> 2025-10-02T12:00:00Z"
                - "2025-09-20T14:30:00Z: board_type: half_board -> full_board"
              special_requests: []
              created_at: "2025-09-10T09:00:00Z"
              updated_at: "2025-09-20T14:30:00Z"
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-60883561
              customer_id: CUS-60883561
              email: marcus.wellington@techventures.io
              full_name: Marcus Wellington
              vip_tier: vip
              loyalty_program_status: gold
              lifetime_value: '12450.75'
              total_bookings_count: 15
              preferences:
                - quiet room
                - high floor
              special_notes:
                - prefers late checkout when available
              complaint_count: 0
              last_booking_date: "2025-09-15T14:00:00Z"
              created_at: "2024-03-10T10:00:00Z"
              updated_at: "2025-09-15T14:00:00Z"
          hotel_partner_api_hotels:
            - id: HTL-60883561
              hotel_id: HTL-60883561
              hotel_name: The Belmont Residences
              location: Boston
              partner_tier: premium
              contact_name: Jennifer Hartley
              contact_email: reservations@belmontresidences.com
              contact_phone: +1-617-482-7039
              escalation_contact: manager@belmontresidences.com
              amenities:
                - spa
                - gym
                - restaurant
                - concierge
              supports_pets: true
              accessible_rooms_available: true
              created_at: "2024-06-15T10:00:00Z"
              updated_at: "2024-06-15T10:00:00Z"
          payment_api_transactions: []
          zendesk_tickets:
            - id: TCK-59514846
              subject: Date modification request - BKG-60883561
              description: Customer requesting to change check-in date from October 1 to October 2 due to travel schedule change.
              status: solved
              priority: normal
              type: task
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: ORG-10000002
              tags:
                - b2c-customer
                - date-change
              created_at: "2025-09-21T11:30:00Z"
              updated_at: "2025-09-21T14:00:00Z"
              due_at: null
              booking_reference: BKG-60883561
              hotel_id: HTL-60883561
              check_in_date: "2025-10-02T12:00:00Z"
              booking_value: 1250.0
              request_type_detail: modify-dates
              corporate_account_id: null
              group_booking_id: null
              resolution_action: modification-completed
              refund_amount: 0
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Marcus Wellington
              email: marcus.wellington@techventures.io
              role: end-user
              organization_id: ORG-10000002
              phone: +1-617-294-8173
              verified: true
              active: true
              created_at: "2024-05-20T10:00:00Z"
              updated_at: "2024-05-20T10:00:00Z"
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: crm_api_get_customer_profile
              parameters:
                email: marcus.wellington@techventures.io
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-60883561
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-60883561
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: "email eq 'marcus.wellington@techventures.io'"
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "booking_reference eq 'BKG-60883561'"
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Late checkout request - BKG-60883561
                  description: "Customer requesting late checkout for booking BKG-60883561. Customer is VIP tier. Check-in: 2025-10-02 (23 hours away). Hotel: Premium tier. Processing same-day special request per Section 4.5.2."
                  status: open
                  priority: high
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-24h
                    - vip-customer
                  booking_reference: BKG-60883561
                  hotel_id: HTL-60883561
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-60883561
                special_requests:
                  - Late checkout until 2 PM (subject to availability)
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-60883561
                charge_amount: '30.00'
                reason: late_checkout_fee
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  tags:
                    - b2c-customer
                    - check-in-24h
                    - vip-customer
                  booking_reference: BKG-60883561
                  hotel_id: HTL-60883561
                  check_in_date: "2025-10-02T12:00:00Z"
                  booking_value: 1250.0
                  request_type_detail: add-special-request
                  resolution_action: modification-completed
                  refund_amount: 0
        rubrics_yesno:
          - "IF the agent's final message mentions a specific date for the late checkout, does it correctly refer to the check-out date of 2025-10-04 (not the check-in date of 2025-10-02)? (Yes = correct date stated or no date mentioned, No = states an incorrect date such as 2025-10-02)"
          - "Policy states: 'Do not share internal technical fields names with customers.' Does the agent's final message avoid disclosing internal technical field names (e.g., 'request_type_detail', 'resolution_action', 'refund_amount', 'hotel_id', 'booking_value')? (Yes = no internal field names shared, No = internal field names disclosed to the customer)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


def test_bmd_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I need to make a change to my upcoming booking. My booking reference is BKG-56482366, and my name is Michael Reynolds (email: michael.reynolds@protonmail.com). I originally booked for 2 adults and 3 children, but one of the kids can no longer make it, so I need to reduce the children count from 3 to 2. Can you help me with this?
    user_context: |
        You are Michael Reynolds, a customer contacting support to reduce the number of children on your upcoming hotel booking from 3 to 2. One of your children can no longer join the trip.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent informs you about a modification fee and asks for confirmation to proceed, confirm and agree to the fee.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-56482366
              customer_id: CUS-00000006
              hotel_id: HTL-00020156
              check_in_date: "2025-10-02T16:00:00Z"
              check_out_date: "2025-10-05T11:00:00Z"
              booking_value: '420.00'
              room_type: family_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 3
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history:
                - "2025-09-15T10:30:00Z: check_in_date: 2025-10-01T16:00:00Z -> 2025-10-02T16:00:00Z"
              special_requests: []
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-15T10:30:00Z"
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: michael.reynolds@protonmail.com
              full_name: Michael Reynolds
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '1850.75'
              total_bookings_count: 4
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-09-01T10:00:00Z"
              created_at: "2024-08-15T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00020156
              hotel_name: Harbor View Hotel
              location: Seattle
              partner_tier: standard
              contact_name: Jennifer Walsh
              contact_email: info@harborviewhotel.com
              contact_phone: +1-206-847-3921
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
          zendesk_users:
            - id: USR-10000007
              name: Michael Reynolds
              email: michael.reynolds@protonmail.com
              role: end-user
              organization_id: null
              phone: +1-206-394-7281
              verified: true
              active: true
              created_at: "2024-08-15T00:00:00Z"
              updated_at: "2024-08-15T00:00:00Z"
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-56482366
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00020156
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "booking_reference eq 'BKG-56482366'"
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: "email eq 'michael.reynolds@protonmail.com'"
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Guest count modification request - BKG-56482366
                  description: Customer requests to reduce children count from 3 to 2. Booking at standard partner hotel, check-in 2025-10-02. Second modification on this booking.
                  status: open
                  priority: high
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-56482366
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-56482366
                children_count: 2
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-56482366
                charge_amount: '65.00'
                reason: modification_fee
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-56482366
                  hotel_id: HTL-00020156
                  check_in_date: "2025-10-02T16:00:00Z"
                  booking_value: 420.0
                  request_type_detail: modify-guests
                  resolution_action: modification-completed
                  refund_amount: 0
        rubrics_yesno:
          - "Policy states: 'Do not share hotel commission rates or partner tier classifications with customers.' Does the agent's final message avoid revealing the hotel's partner tier classification (e.g., 'standard', 'premium', 'budget')? (Yes = does not reveal partner tier, No = reveals it)"
          - "Policy states: 'Do not share internal technical fields names with customers.' Does the agent's final message avoid using internal technical field names (such as 'children_count', 'resolution_action', 'request_type_detail', 'booking_reference' as field labels, etc.)? (Yes = avoids internal field names or does not mention them, No = uses internal technical field names)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


def test_bmd_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to upgrade my room booking.
    user_context: |
        You are Victoria Miller, a VIP customer contacting StayBridge support to upgrade your room from standard_room to family_room for booking BKG-93676320. You previously contacted support about this same request but want to proceed with it now.

        Only if you are asked for your name — tell the agent you are Victoria Miller.
        Only if you are asked for your email address — tell the agent it is victoria.miller@outlook.com.
        Only if you are asked for booking reference or booking number — provide BKG-93676320.
        Only if you are asked about what type of room you currently have — tell the agent it's a standard room.
        Only if you are asked what type of room you want to upgrade to — tell the agent you want a family room.
        Only if you are asked about previous contact or when you contacted before — tell the agent you reached out about this a couple of days ago.
        Only if you are asked why you need the upgrade or about the reason — tell the agent you're traveling with two kids and really need the extra space.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If informed about charges or fees for the modification, accept them and confirm you want to proceed.
        - Thank the agent once the upgrade is confirmed.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-93676320
              customer_id: CUS-00000006
              hotel_id: HTL-00012350
              check_in_date: "2025-10-06T14:00:00Z"
              check_out_date: "2025-10-08T11:00:00Z"
              booking_value: '340.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 2
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history:
                - "2025-09-25T10:00:00Z: board_type: without_breakfast -> with_breakfast"
              special_requests: []
              created_at: "2025-09-18T09:30:00Z"
              updated_at: "2025-09-25T10:00:00Z"
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: victoria.miller@outlook.com
              full_name: Victoria Miller
              vip_tier: vip
              loyalty_program_status: gold
              lifetime_value: '8750.25'
              total_bookings_count: 15
              preferences:
                - family-friendly
                - ground floor
              special_notes:
                - traveling with young children
              complaint_count: 0
              last_booking_date: "2025-09-18T09:30:00Z"
              created_at: "2024-08-15T10:00:00Z"
              updated_at: "2025-09-18T09:30:00Z"
          hotel_partner_api_hotels:
            - id: HTL-00012350
              hotel_id: HTL-00012350
              hotel_name: Riverside Budget Lodge
              location: Portland
              partner_tier: budget
              contact_name: Kevin Walsh
              contact_email: contact@riversidelodge.com
              contact_phone: +1-503-742-8196
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
          zendesk_tickets:
            - id: TCK-16328708
              subject: Room type upgrade request
              description: Customer requesting upgrade from standard room to family room
              status: solved
              priority: normal
              type: task
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: ORG-10000002
              tags:
                - b2c-customer
                - room-upgrade
                - vip-customer
              created_at: "2025-09-29T13:00:00Z"
              updated_at: "2025-09-29T15:00:00Z"
              due_at: null
              booking_reference: BKG-93676320
              hotel_id: HTL-00012350
              check_in_date: "2025-10-06T14:00:00Z"
              booking_value: 340.0
              request_type_detail: modify-room-type
              corporate_account_id: null
              group_booking_id: null
              resolution_action: information-provided
              refund_amount: 0
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Victoria Miller
              email: victoria.miller@outlook.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-503-847-2938
              verified: true
              active: true
              created_at: "2024-08-15T00:00:00Z"
              updated_at: "2024-08-15T00:00:00Z"
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-00012350
              room_type: family_room
              board_type: with_breakfast
              date: "2025-10-06T00:00:00Z"
              available_count: 2
              price_per_night: '200.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000007
              hotel_id: HTL-00012350
              room_type: family_room
              board_type: with_breakfast
              date: "2025-10-07T00:00:00Z"
              available_count: 2
              price_per_night: '200.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000008
              hotel_id: HTL-00012350
              room_type: family_room
              board_type: without_breakfast
              date: "2025-10-06T00:00:00Z"
              available_count: 2
              price_per_night: '175.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000009
              hotel_id: HTL-00012350
              room_type: family_room
              board_type: without_breakfast
              date: "2025-10-07T00:00:00Z"
              available_count: 2
              price_per_night: '175.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000010
              hotel_id: HTL-00012350
              room_type: family_room
              board_type: half_board
              date: "2025-10-06T00:00:00Z"
              available_count: 2
              price_per_night: '235.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000011
              hotel_id: HTL-00012350
              room_type: family_room
              board_type: half_board
              date: "2025-10-07T00:00:00Z"
              available_count: 2
              price_per_night: '235.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
          booking_api_group_bookings: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-93676320
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00012350
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "booking_reference eq 'BKG-93676320'"
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: "email eq 'victoria.miller@outlook.com'"
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-16328708
                item:
                  status: open
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00012350
                check_in_date: "2025-10-06T14:00:00Z"
                check_out_date: "2025-10-08T11:00:00Z"
                room_type: family_room
                board_type: with_breakfast
                adults_count: 2
                children_count: 2
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-93676320
                room_type: family_room
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-93676320
                charge_amount: '112.50'
                reason: modification_fee_and_price_difference
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-16328708
                item:
                  status: solved
                  priority: normal
                  type: task
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - repeat-issue
                    - vip-customer
                  booking_reference: BKG-93676320
                  hotel_id: HTL-00012350
                  check_in_date: "2025-10-06T14:00:00Z"
                  booking_value: 400.0
                  request_type_detail: modify-room-type
                  resolution_action: modification-completed
                  refund_amount: 0
        rubrics_yesno:
          - "Policy states: 'Do not share hotel commission rates or partner tier classifications with customers.' Does the agent's final message avoid revealing the hotel's partner tier classification (e.g., 'budget', 'standard', 'premium')? (Yes = does not reveal the tier classification, No = reveals it)"
          - "Policy states: 'Do not share internal technical fields names with customers.' Does the agent's final message avoid sharing internal technical field names such as 'request_type_detail', 'resolution_action', 'refund_amount', 'booking_value', or similar system field identifiers? (Yes = does not share internal field names, No = shares them)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


def test_bmd_020(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I'd like to make a change to my upcoming booking.
    user_context: |
        You are Victoria Chen, a platinum tier customer contacting StayBridge support to change your board type on your upcoming booking. Your check-in is on October 5th, 2025.

        Only if you are asked about your booking reference or booking number — tell the agent it is BKG-20465375.
        Only if you are asked about your email address — tell the agent it is victoria.chen@outlook.com.
        Only if you are asked about what change you want to make or details about the board type — tell the agent you currently have full board included but you'd like to change it to without breakfast instead.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm the modification, confirm that you want to proceed.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-20465375
              booking_reference: BKG-20465375
              customer_id: CUS-20465375
              hotel_id: HTL-20465375
              check_in_date: "2025-10-05T14:00:00Z"
              check_out_date: "2025-10-07T11:00:00Z"
              room_type: suite
              board_type: full_board
              booking_value: '485.00'
              adults_count: 2
              children_count: 1
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-10T14:30:00Z"
              updated_at: "2025-09-10T14:30:00Z"
          crm_api_customer_profiles:
            - id: CUS-20465375
              customer_id: CUS-20465375
              email: victoria.chen@outlook.com
              full_name: Victoria Chen
              vip_tier: platinum
              loyalty_program_status: active
              lifetime_value: '12500.00'
              total_bookings_count: 15
              preferences:
                - suite
                - late checkout
              special_notes:
                - prefers quiet floors
              complaint_count: 0
              last_booking_date: "2025-09-10T14:30:00Z"
              created_at: "2022-06-15T09:00:00Z"
              updated_at: "2025-09-10T14:30:00Z"
          hotel_partner_api_hotels:
            - id: HTL-20465375
              hotel_id: HTL-20465375
              hotel_name: Budget Stay Lodge
              location: Boston
              partner_tier: budget
              contact_name: Thomas Rivera
              contact_email: manager@budgetstaylodge.com
              contact_phone: +1-617-392-4518
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
          booking_api_hotel_inventory:
            - id: INV-20465370
              hotel_id: HTL-20465375
              room_type: suite
              board_type: without_breakfast
              date: "2025-10-05T00:00:00Z"
              available_count: 3
              price_per_night: '200.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-20465371
              hotel_id: HTL-20465375
              room_type: suite
              board_type: without_breakfast
              date: "2025-10-06T00:00:00Z"
              available_count: 3
              price_per_night: '200.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-20465372
              hotel_id: HTL-20465375
              room_type: suite
              board_type: with_breakfast
              date: "2025-10-05T00:00:00Z"
              available_count: 3
              price_per_night: '220.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-20465373
              hotel_id: HTL-20465375
              room_type: suite
              board_type: with_breakfast
              date: "2025-10-06T00:00:00Z"
              available_count: 3
              price_per_night: '220.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-20465374
              hotel_id: HTL-20465375
              room_type: suite
              board_type: half_board
              date: "2025-10-05T00:00:00Z"
              available_count: 3
              price_per_night: '235.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-20465375
              hotel_id: HTL-20465375
              room_type: suite
              board_type: half_board
              date: "2025-10-06T00:00:00Z"
              available_count: 3
              price_per_night: '235.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-20465376
              hotel_id: HTL-20465375
              room_type: suite
              board_type: full_board
              date: "2025-10-05T00:00:00Z"
              available_count: 2
              price_per_night: '242.50'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-20465377
              hotel_id: HTL-20465375
              room_type: suite
              board_type: full_board
              date: "2025-10-06T00:00:00Z"
              available_count: 2
              price_per_night: '242.50'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
          zendesk_users:
            - id: USR-10000007
              name: Victoria Chen
              email: victoria.chen@outlook.com
              role: end-user
              organization_id: null
              phone: +1-617-483-2967
              verified: true
              active: true
              created_at: "2022-06-15T09:00:00Z"
              updated_at: "2022-06-15T09:00:00Z"
          payment_api_transactions:
            - id: TXN-20465375
              transaction_id: TXN-20465375
              booking_reference: BKG-20465375
              customer_id: CUS-20465375
              amount: '485.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 8521
              reason: null
              processing_time_estimate: null
              created_at: "2025-09-10T14:30:00Z"
              updated_at: "2025-09-10T14:30:00Z"
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          corporate_api_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-20465375
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-20465375
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-20465375
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-20465375
                check_in_date: "2025-10-05T14:00:00Z"
                check_out_date: "2025-10-07T11:00:00Z"
                room_type: suite
                board_type: without_breakfast
                adults_count: 2
                children_count: 1
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: "email eq 'victoria.chen@outlook.com'"
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "booking_reference eq 'BKG-20465375'"
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Board type modification request - BKG-20465375
                  description: Customer requests to change board type from full_board to without_breakfast. Booking at budget tier hotel for 2025-10-05 check-in. Customer is platinum VIP - modification fee waived. Awaiting processing.
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                  booking_reference: BKG-20465375
                  hotel_id: HTL-20465375
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-20465375
                board_type: without_breakfast
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-20465375
                refund_amount: '85.00'
                reason: modification_price_difference
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  description: "Customer requests to change board type from full_board to without_breakfast. Booking at budget tier hotel for 2025-10-05 check-in. Customer is platinum VIP - modification fee waived. RESOLUTION: Board type successfully modified from full_board to without_breakfast. Original booking value: $485.00. New booking value: $400.00. Price difference refund of $85.00 processed (TXN-00000008). No modification fee charged due to platinum tier exception. Note: Customer qualifies for vip-customer tag."
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                  booking_reference: BKG-20465375
                  hotel_id: HTL-20465375
                  check_in_date: "2025-10-05T14:00:00Z"
                  booking_value: 400.0
                  request_type_detail: modify-board-type
                  resolution_action: modification-completed
                  refund_amount: 85.0
        rubrics_yesno:
          - "Policy states: 'Do not share internal technical fields names with customers.' Does the agent's final message avoid revealing internal technical field names (e.g., 'request_type_detail', 'resolution_action', 'refund_amount', 'tags', 'booking_value')? (Yes = does not reveal internal field names or does not touch the topic, No = reveals one or more internal technical field names)"
          - "Policy states (Section 6.3 Customer Communication at Resolution): 'Provide reference numbers (transaction_id, booking_reference).' IF the agent's final message confirms a refund was processed, does it include the refund transaction ID (the correct value being TXN-00000009)? (Yes = correct transaction ID TXN-00000009 is stated, or no refund is mentioned; No = refund confirmed but transaction ID is missing or a different transaction ID is stated)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


def test_bpy_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm having trouble completing a payment for my hotel booking. My name is Michael Harris and my email is michael.harris@proton.me. The booking reference is BKG-87769453. I tried to pay with my credit card ending in 4521 but I got an error and the payment failed. The amount was $420. Can you help me fix this?
    user_context: |
        You are Michael Harris, a customer who experienced a payment failure when trying to complete your hotel booking. You want help resolving this so you can successfully pay for your reservation.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If the agent asks you to provide a new payment method or credit card, you want to use a new credit card ending in 9876.
        - Confirm and cooperate when the agent explains the resolution process.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-87769453
              booking_reference: BKG-87769453
              customer_id: CUS-74835921
              hotel_id: HTL-00012346
              check_in_date: "2025-10-05T15:00:00Z"
              check_out_date: "2025-10-07T11:00:00Z"
              booking_value: '420.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-15T10:00:00Z"
              updated_at: "2025-09-15T10:00:00Z"
          crm_api_customer_profiles:
            - id: CUS-74835921
              customer_id: CUS-74835921
              email: michael.harris@proton.me
              full_name: Michael Harris
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '420.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-09-15T10:00:00Z"
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-15T10:00:00Z"
          payment_api_transactions:
            - id: TXN-14737996
              transaction_id: TXN-14737996
              booking_reference: BKG-87769453
              customer_id: CUS-74835921
              amount: '420.00'
              currency: USD
              transaction_type: charge
              payment_status: failed
              payment_method: credit_card ending in 4521
              reason: null
              processing_time_estimate: null
              created_at: "2025-09-15T10:05:00Z"
              updated_at: "2025-09-15T10:05:00Z"
          zendesk_users:
            - id: USR-10000007
              name: Michael Harris
              email: michael.harris@proton.me
              role: end-user
              organization_id: null
              phone: +1-617-384-7129
              verified: true
              active: true
              created_at: "2025-09-01T00:00:00Z"
              updated_at: "2025-09-01T00:00:00Z"
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          hotel_partner_api_hotels: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-87769453
            - tool: crm_api_check_vip_status
              parameters:
                customer_id: CUS-74835921
            - tool: payment_api_check_payment_status
              parameters:
                booking_reference: BKG-87769453
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-74835921
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "booking_reference eq 'BKG-87769453'"
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: "email eq 'michael.harris@proton.me'"
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Payment failure assistance - BKG-87769453
                  description: Customer reports payment failure when attempting to complete booking. Transaction TXN-14737996 shows failed status for $420 using credit card ending in 4521. Customer requests help completing payment.
                  status: open
                  priority: high
                  type: incident
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-87769453
                  hotel_id: HTL-00012346
                  check_in_date: "2025-10-05T15:00:00Z"
                  booking_value: 420.0
                  request_type_detail: billing-inquiry
            - tool: payment_api_update_payment_method
              parameters:
                customer_id: CUS-74835921
                new_payment_method: tok_card_ending_9876
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  resolution_action: information-provided
                  refund_amount: 0.0
        rubrics_yesno:
          - "Policy states under 'Customer Communication at Resolution' (Section 6.3): 'Thank customer for contacting StayBridge support.' Does the agent's final message include a thank-you or expression of gratitude to the customer? (Yes = includes a thank-you in any form, No = no thank-you or expression of gratitude present)"
          - "Policy states under 'Customer Communication at Resolution' (Section 6.3): 'Provide reference numbers (transaction_id, booking_reference).' The relevant transaction ID for this case is TXN-14737996. IF the agent's final message provides a resolution summary, does it include the transaction ID TXN-14737996? (Yes = correct transaction ID TXN-14737996 is mentioned, or no resolution summary is provided; No = resolution summary is provided but transaction ID is missing or a different transaction ID is stated)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


def test_cbm_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Nathan Brooks from MidSize Partners. My email is nathan.brooks@midsizepartners.com and my booking reference is BKG-46291486. I need to extend my stay by 2 additional nights - my check-in is October 6th. I actually submitted a request about this a couple of days ago but never heard back. Can you help me get this sorted out?
    user_context: |
        You are Nathan Brooks, a corporate employee from MidSize Partners contacting StayBridge support to extend your hotel booking by 2 additional nights.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If asked to confirm the extension or any associated charges, confirm that you want to proceed.
    init:
      external_booking_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-52816850
              subject: Date modification request for BKG-46291486
              description: Corporate employee requesting to extend stay by 2 nights
              status: pending
              priority: normal
              type: task
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: ORG-10000003
              tags:
                - corporate
                - date-change
              created_at: "2025-09-29T13:00:00Z"
              updated_at: "2025-09-29T14:00:00Z"
              due_at: null
              booking_reference: BKG-46291486
              hotel_id: HTL-46291500
              check_in_date: "2025-10-06T15:00:00Z"
              booking_value: 780.0
              request_type_detail: modify-dates
              corporate_account_id: CRP-49251925
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Nathan Brooks
              email: nathan.brooks@midsizepartners.com
              role: end-user
              organization_id: ORG-10000003
              phone: +1-617-384-9120
              verified: true
              active: true
              created_at: "2025-02-15T00:00:00Z"
              updated_at: "2025-02-15T00:00:00Z"
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-46291486
              customer_id: CUS-00000006
              hotel_id: HTL-46291500
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-08T11:00:00Z"
              booking_value: '780.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: CRP-49251925
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-15T10:00:00Z"
              updated_at: "2025-09-15T10:00:00Z"
          booking_api_group_bookings: []
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-46291500
              room_type: deluxe_room
              board_type: with_breakfast
              date: "2025-10-06T00:00:00Z"
              available_count: 3
              price_per_night: '390.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000007
              hotel_id: HTL-46291500
              room_type: deluxe_room
              board_type: with_breakfast
              date: "2025-10-07T00:00:00Z"
              available_count: 3
              price_per_night: '390.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000008
              hotel_id: HTL-46291500
              room_type: deluxe_room
              board_type: with_breakfast
              date: "2025-10-08T00:00:00Z"
              available_count: 3
              price_per_night: '390.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000009
              hotel_id: HTL-46291500
              room_type: deluxe_room
              board_type: with_breakfast
              date: "2025-10-09T00:00:00Z"
              available_count: 3
              price_per_night: '390.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: nathan.brooks@midsizepartners.com
              full_name: Nathan Brooks
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '2450.00'
              total_bookings_count: 4
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-09-15T10:00:00Z"
              created_at: "2024-06-01T10:00:00Z"
              updated_at: "2025-09-15T10:00:00Z"
          corporate_api_corporate_accounts:
            - id: INT-00000007
              corporate_account_id: CRP-49251925
              company_name: MidSize Partners
              account_tier: mid_market
              account_status: active
              contact_name: Rachel Morrison
              contact_email: rachel.morrison@midsizepartners.com
              contact_phone: +1-617-482-3819
              booking_limit: 20
              credit_limit: '50000.00'
              payment_terms: Net 45
              expiration_date: "2026-06-30T00:00:00Z"
              created_at: "2024-08-15T10:00:00Z"
              updated_at: "2025-08-15T10:00:00Z"
          hotel_partner_api_hotels:
            - id: HTL-46291500
              hotel_id: HTL-46291500
              hotel_name: Riverside Business Hotel
              location: Boston
              partner_tier: standard
              contact_name: Michael Reynolds
              contact_email: reservations@riversidebusiness.com
              contact_phone: +1-617-395-8742
              escalation_contact: null
              amenities:
                - wifi
                - gym
                - business_center
              supports_pets: false
              accessible_rooms_available: true
              created_at: "2025-01-15T10:00:00Z"
              updated_at: "2025-01-15T10:00:00Z"
          payment_api_transactions: []
          lookup_bookings: []
          lookup_hotels: []
          lookup_group_bookings: []
          lookup_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "booking_reference eq 'BKG-46291486'"
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-52816850
                item:
                  status: open
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-46291486
            - tool: crm_api_check_vip_status
              parameters:
                customer_id: CUS-00000006
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-49251925
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-46291500
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-46291500
                check_in_date: "2025-10-08T15:00:00Z"
                check_out_date: "2025-10-10T11:00:00Z"
                room_type: deluxe_room
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-46291486
                check_out_date: "2025-10-10T11:00:00Z"
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-46291486
                charge_amount: '805.00'
                reason: date_modification_price_difference_and_fee
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-52816850
                item:
                  status: solved
                  priority: normal
                  type: task
                  tags:
                    - corporate-account
                    - check-in-upcoming
                  booking_reference: BKG-46291486
                  hotel_id: HTL-46291500
                  check_in_date: "2025-10-06T15:00:00Z"
                  booking_value: 1560.0
                  request_type_detail: modify-dates
                  corporate_account_id: CRP-49251925
                  resolution_action: modification-completed
                  refund_amount: 0
        rubrics_yesno:
          - "Policy states: 'Do not share hotel commission rates or partner tier classifications with customers.' Does the agent's final message avoid revealing the hotel's partner tier classification (e.g., 'standard', 'premium', 'budget')? (Yes = does not reveal the hotel partner tier, No = reveals it)"
          - "Policy section 6.3 (Customer Communication at Resolution) states: 'Provide reference numbers (transaction_id, booking_reference)'. IF the agent's final message confirms that a charge was processed, does it include a transaction ID? (Yes = transaction ID is included or no charge is mentioned, No = charge confirmed but transaction ID is missing)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


def test_ccn_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to urgently cancel my corporate booking. My name is Ryan Mitchell with GlobalFinance LLC and my email is ryan.mitchell@globalfinance.com. The booking reference is BKG-75255341. Our business trip just got cancelled so I won't be needing this reservation anymore. I believe I reached out about this a couple days ago as well.
    user_context: |
        You are Ryan Mitchell, an employee of GlobalFinance LLC (a corporate client) contacting support to cancel your hotel booking because your business trip has been cancelled. This is urgent.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If the agent informs you that no refund is available due to the timing of the cancellation, confirm that you still want to proceed with the cancellation anyway since the trip is cancelled and you won't be using the room.
    init:
      external_booking_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-92832764
              subject: Cancellation inquiry for corporate booking
              description: Employee needs to inquire about cancellation options for upcoming corporate booking
              status: pending
              priority: normal
              type: question
              requester_id: USR-92741658
              assignee_id: AG-83945
              organization_id: ORG-10000003
              tags:
                - cancellation-inquiry
                - corporate-account
              created_at: "2025-09-29T14:30:00Z"
              updated_at: "2025-09-29T14:30:00Z"
              due_at: null
              booking_reference: BKG-75255341
              hotel_id: HTL-58291746
              check_in_date: "2025-10-02T10:00:00Z"
              booking_value: 1120.0
              request_type_detail: cancel-booking
              corporate_account_id: CRP-03413164
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-92741658
              name: Ryan Mitchell
              email: ryan.mitchell@globalfinance.com
              role: end-user
              organization_id: ORG-10000003
              phone: +1-646-849-3128
              verified: true
              active: true
              created_at: "2024-06-01T10:00:00Z"
              updated_at: "2024-06-01T10:00:00Z"
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-75255341
              booking_reference: BKG-75255341
              customer_id: CUS-92741658
              hotel_id: HTL-58291746
              check_in_date: "2025-10-02T10:00:00Z"
              check_out_date: "2025-10-05T11:00:00Z"
              booking_value: '1120.00'
              room_type: executive_suite
              board_type: with_breakfast
              adults_count: 1
              children_count: 0
              booking_status: confirmed
              corporate_account_id: CRP-03413164
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-15T09:00:00Z"
              updated_at: "2025-09-15T09:00:00Z"
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts:
            - id: INT-03413164
              corporate_account_id: CRP-03413164
              company_name: GlobalFinance LLC
              account_tier: enterprise
              account_status: active
              contact_name: Victoria Sullivan
              contact_email: travel@globalfinance.com
              contact_phone: +1-646-849-3027
              booking_limit: 50
              credit_limit: '200000.00'
              payment_terms: Net 60
              expiration_date: "2026-12-31T00:00:00Z"
              created_at: "2024-03-15T10:00:00Z"
              updated_at: "2025-08-20T14:30:00Z"
          crm_api_customer_profiles:
            - id: CUS-92741658
              customer_id: CUS-92741658
              email: ryan.mitchell@globalfinance.com
              full_name: Ryan Mitchell
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '3450.00'
              total_bookings_count: 8
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-09-15T09:00:00Z"
              created_at: "2024-06-01T10:00:00Z"
              updated_at: "2025-09-15T09:00:00Z"
          hotel_partner_api_hotels:
            - id: HTL-58291746
              hotel_id: HTL-58291746
              hotel_name: Metropolitan Business Hotel
              location: Chicago
              partner_tier: standard
              contact_name: Patricia Williams
              contact_email: reservations@metropolitanbusiness.com
              contact_phone: +1-312-847-2193
              escalation_contact: null
              amenities:
                - wifi
                - business_center
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "booking_reference eq 'BKG-75255341'"
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-92832764
                item:
                  status: open
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-75255341
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-58291746
            - tool: crm_api_check_vip_status
              parameters:
                customer_id: CUS-92741658
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-03413164
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-75255341
                booking_status: cancelled
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-92832764
                item:
                  status: solved
                  priority: high
                  type: task
                  tags:
                    - corporate-account
                    - check-in-24h
                  booking_reference: BKG-75255341
                  hotel_id: HTL-58291746
                  check_in_date: "2025-10-02T10:00:00Z"
                  booking_value: 1120.0
                  request_type_detail: cancel-booking
                  corporate_account_id: CRP-03413164
                  resolution_action: modification-completed
                  refund_amount: 0
        rubrics_yesno:
          - "Policy states: 'Do not share hotel commission rates or partner tier classifications with customers.' Does the agent's final message avoid revealing the hotel's partner tier classification (e.g., 'standard', 'premium', 'budget')? (Yes = does not reveal partner tier classification, No = reveals it)"
          - "Policy states: 'Do not share internal technical fields names with customers.' Does the agent's final message avoid sharing internal technical field names (e.g., 'request_type_detail', 'resolution_action', 'booking_status', 'hotel_id', 'booking_value', 'refund_amount')? (Yes = does not share internal field names, No = shares one or more internal field names)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


def test_crf_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to cancel my hotel booking. My name is Michael Brennan, email michael.brennan@fastmail.net. The booking reference is BKG-42253584. I actually reached out about this a few days ago but wanted to follow up and go ahead with the cancellation now.
    user_context: |
        You are Michael Brennan, a customer who wants to cancel your hotel booking BKG-42253584 at Riverside Garden Inn. You previously inquired about cancellation options a few days ago but now you've decided to proceed with the cancellation.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent explains the refund terms (partial refund due to timing), confirm you want to proceed with the cancellation.
    init:
      external_booking_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-14384249
              subject: Cancellation inquiry for booking BKG-42253584
              description: Customer inquiring about cancellation options for upcoming stay
              status: pending
              priority: normal
              type: question
              requester_id: USR-10291745
              assignee_id: AG-83945
              organization_id: ORG-10000001
              tags:
                - cancellation
                - inquiry
              created_at: "2025-09-28T13:00:00Z"
              updated_at: "2025-09-28T13:00:00Z"
              due_at: null
              booking_reference: BKG-42253584
              hotel_id: HTL-91827364
              check_in_date: "2025-10-02T15:00:00Z"
              booking_value: 410.0
              request_type_detail: cancel-booking
              corporate_account_id: null
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-10291745
              name: Michael Brennan
              email: michael.brennan@fastmail.net
              role: end-user
              organization_id: ORG-10000001
              phone: +1-503-294-7821
              verified: true
              active: true
              created_at: "2024-08-20T10:00:00Z"
              updated_at: "2025-09-15T14:30:00Z"
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-42253584
              booking_reference: BKG-42253584
              customer_id: CUS-55102938
              hotel_id: HTL-91827364
              check_in_date: "2025-10-02T15:00:00Z"
              check_out_date: "2025-10-04T11:00:00Z"
              booking_value: '410.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-15T14:30:00Z"
              updated_at: "2025-09-15T14:30:00Z"
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-55102938
              customer_id: CUS-55102938
              email: michael.brennan@fastmail.net
              full_name: Michael Brennan
              vip_tier: standard
              loyalty_program_status: active
              lifetime_value: '1850.75'
              total_bookings_count: 4
              preferences:
                - quiet room
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-09-15T14:30:00Z"
              created_at: "2024-08-20T10:00:00Z"
              updated_at: "2025-09-15T14:30:00Z"
          hotel_partner_api_hotels:
            - id: HTL-91827364
              hotel_id: HTL-91827364
              hotel_name: Riverside Garden Inn
              location: Portland
              partner_tier: standard
              contact_name: Jennifer Walsh
              contact_email: frontdesk@riversidegarden.com
              contact_phone: +1-503-842-3167
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
          payment_api_transactions:
            - id: TXN-42253584
              transaction_id: TXN-42253584
              booking_reference: BKG-42253584
              customer_id: CUS-55102938
              amount: '410.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Mastercard ending in 4738
              reason: null
              processing_time_estimate: null
              created_at: "2025-09-15T14:30:00Z"
              updated_at: "2025-09-15T14:30:00Z"
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "booking_reference eq 'BKG-42253584'"
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-14384249
                item:
                  status: open
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-42253584
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-55102938
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-91827364
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-42253584
                booking_status: cancelled
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-42253584
                refund_amount: '190.00'
                reason: cancellation
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-14384249
                item:
                  status: solved
                  priority: high
                  type: task
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-42253584
                  hotel_id: HTL-91827364
                  check_in_date: "2025-10-02T15:00:00Z"
                  booking_value: 410.0
                  request_type_detail: cancel-booking
                  resolution_action: refund-partial
                  refund_amount: 190.0
        rubrics_yesno:
          - "Policy states: 'Do not share hotel commission rates or partner tier classifications with customers.' Does the agent's final message avoid revealing the hotel's partner tier classification (e.g., describing the hotel as 'standard tier', 'premium tier', or 'budget tier')? (Yes = does not reveal the hotel's partner tier, No = reveals it)"
          - "Policy section 6.3 states that at resolution the agent must: 'Provide timelines (refund processing: 3-5 business days + 5-10 to appear on card).' IF the agent's final message confirms a refund was processed, does it include both parts of the required timeline — the 3-5 business days for processing AND the additional 5-10 days for the refund to appear on the customer's card/statement? (Yes = both parts included or no refund mentioned, No = refund confirmed but the 5-10 days to appear on card is missing)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


def test_crf_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to cancel my hotel booking.
    user_context: |
        You are Marcus Wellington, a customer who wants to cancel your upcoming hotel booking. You have a reservation at a hotel for October 10th that you no longer need.

        Only if you are asked about your booking reference or confirmation number — tell the agent it is BKG-00479748
        Only if you are asked about your email address — tell the agent it is marcus.wellington@proton.me

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Accept the cancellation outcome and acknowledge any refund information provided by the agent.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-00479748
              customer_id: CUS-00479748
              hotel_id: HTL-00479748
              check_in_date: "2025-10-10T14:00:00Z"
              check_out_date: "2025-10-11T11:00:00Z"
              booking_value: '185.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 1
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-20T10:00:00Z"
              updated_at: "2025-09-20T10:00:00Z"
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-00479748
              customer_id: CUS-00479748
              email: marcus.wellington@proton.me
              full_name: Marcus Wellington
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '420.75'
              total_bookings_count: 2
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-09-20T10:00:00Z"
              created_at: "2025-06-15T09:00:00Z"
              updated_at: "2025-09-20T10:00:00Z"
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00479748
              hotel_name: Sunrise Budget Inn
              location: Austin
              partner_tier: budget
              contact_name: Rebecca Chen
              contact_email: frontdesk@sunrisebudgetinn.com
              contact_phone: +1-512-847-3291
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: false
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
          payment_api_transactions: []
          zendesk_tickets: []
          zendesk_users:
            - id: USR-10000007
              name: Marcus Wellington
              email: marcus.wellington@proton.me
              role: end-user
              organization_id: null
              phone: +1-512-293-8471
              verified: true
              active: true
              created_at: "2025-06-15T09:00:00Z"
              updated_at: "2025-06-15T09:00:00Z"
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00479748
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00479748
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00479748
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "booking_reference eq 'BKG-00479748'"
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: "email eq 'marcus.wellington@proton.me'"
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation request - BKG-00479748
                  description: "Customer requests cancellation of booking BKG-00479748. Check-in date: 2025-10-10. Booking value: $185."
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-00479748
                  hotel_id: HTL-00479748
                  check_in_date: "2025-10-10T14:00:00Z"
                  booking_value: 185.0
                  request_type_detail: cancel-booking
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00479748
                booking_status: cancelled
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-00479748
                refund_amount: '170.00'
                reason: cancellation
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  description: "Customer requests cancellation of booking BKG-00479748. Check-in date: 2025-10-10. Booking value: $185. Customer tier: standard. Hotel tier: budget (7-day cancellation policy). Time until check-in: ~217 hours (≥7 days). Policy applied: 100% refund with $15 service fee retained. Refund amount: $170.00. Cancellation processed successfully. Refund transaction: TXN-00000008."
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  resolution_action: refund-full
                  refund_amount: 170.0
        rubrics_yesno:
          - "IF the agent's final message mentions what will happen with the service fee, does it correctly indicate that the $15 service fee is retained (i.e., NOT refunded/reversed)? (Yes = correctly states it is retained, or does not mention the service fee's fate beyond the initial deduction, No = incorrectly implies the service fee will be reversed/refunded back to the customer)"
          - "Policy states: 'Do not share hotel commission rates or partner tier classifications with customers.' Does the agent's final message avoid revealing the hotel's partner tier classification (e.g., 'budget', 'standard', 'premium')? (Yes = does not reveal the partner tier, No = reveals it)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


def test_gbi_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Patricia Morrison, the group coordinator for booking GRP-54973348. I'm following up on my request to set up master account billing for our group stay. We have 12 rooms checking in on October 10th, and I need all room charges plus any incidentals for the entire group to be billed to a single company credit card. I have our company payment details ready. My email is patricia.morrison@eventsplus.com. I believe I submitted a request about this a few days ago but wanted to make sure everything is moving forward.
    user_context: |
        You are Patricia Morrison, a group coordinator for Events Plus, contacting support to follow up on a master account billing setup request for your group booking GRP-54973348. You want all charges for your 12 rooms plus incidentals billed to one company credit card.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If asked for company payment details, confirm you can provide them and are ready to share the company credit card information for billing setup.
    init:
      external_booking_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-43443757
              subject: Group Billing Setup Request - GRP-54973348
              description: Group coordinator requesting master account billing setup for group booking GRP-54973348
              status: pending
              priority: normal
              type: task
              requester_id: USR-54973001
              assignee_id: AG-83945
              organization_id: ORG-10000003
              tags:
                - check-in-upcoming
                - group-coordinator
              created_at: "2025-09-28T13:00:00Z"
              updated_at: "2025-09-29T10:00:00Z"
              due_at: null
              booking_reference: null
              hotel_id: HTL-88776655
              check_in_date: "2025-10-10T15:00:00Z"
              booking_value: null
              request_type_detail: add-special-request
              corporate_account_id: null
              group_booking_id: GRP-54973348
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-54973001
              name: Patricia Morrison
              email: patricia.morrison@eventsplus.com
              role: end-user
              organization_id: ORG-10000003
              phone: +1-415-782-6391
              verified: true
              active: true
              created_at: "2025-08-15T09:00:00Z"
              updated_at: "2025-08-15T09:00:00Z"
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_organizations: []
          zendesk_comments: []
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-54973001
              customer_id: CUS-54973001
              hotel_id: HTL-88776655
              check_in_date: "2025-10-10T15:00:00Z"
              check_out_date: "2025-10-12T11:00:00Z"
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-54973348
              modification_history: []
              special_requests: []
              created_at: "2025-08-15T09:00:00Z"
              updated_at: "2025-08-15T09:00:00Z"
          booking_api_hotel_inventory: []
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-54973348
              coordinator_name: Patricia Morrison
              coordinator_email: patricia.morrison@eventsplus.com
              coordinator_phone: +1-415-782-6391
              total_rooms: 12
              check_in_date: "2025-10-10T15:00:00Z"
              check_out_date: "2025-10-12T11:00:00Z"
              hotel_id: HTL-88776655
              booking_references:
                - BKG-54973001
                - BKG-54973002
                - BKG-54973003
                - BKG-54973004
                - BKG-54973005
                - BKG-54973006
                - BKG-54973007
                - BKG-54973008
                - BKG-54973009
                - BKG-54973010
                - BKG-54973011
                - BKG-54973012
              created_at: "2025-08-15T09:00:00Z"
              updated_at: "2025-08-15T09:00:00Z"
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-54973001
              customer_id: CUS-54973001
              email: patricia.morrison@eventsplus.com
              full_name: Patricia Morrison
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '4800.00'
              total_bookings_count: 12
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-08-15T09:00:00Z"
              created_at: "2025-08-15T09:00:00Z"
              updated_at: "2025-08-15T09:00:00Z"
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-88776655
              hotel_name: Harborview Grand Hotel
              location: San Francisco
              partner_tier: premium
              contact_name: Victoria Chen
              contact_email: vchen@harborviewgrand.com
              contact_phone: +1-415-891-3724
              escalation_contact: director@harborviewgrand.com
              amenities:
                - pool
                - gym
                - spa
                - restaurant
                - conference_room
              supports_pets: true
              accessible_rooms_available: true
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "group_booking_id eq 'GRP-54973348'"
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-43443757
                item:
                  status: open
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-54973348
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-54973001
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-88776655
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-88776655
                booking_reference: BKG-54973001
                issue_type: hotel-confirmation-required
                description: Group coordinator for GRP-54973348 (12 rooms, check-in 2025-10-10) requests master account billing arrangement. All room charges for 12 rooms plus any incidentals to be billed to single company credit card on file. Coordinator has provided company payment details. Hotel confirmation required to configure billing setup.
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-43443757
                item:
                  status: hold
                  priority: normal
                  type: task
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                  description: "Customer request: Group coordinator for GRP-54973348 requests master account billing setup - all 12 room charges and incidentals to be billed to single company credit card. Company payment details provided.\\n\\nKey data: Group booking GRP-54973348, 12 rooms at HTL-88776655 (premium partner), check-in 2025-10-10, total booking value $4,800.00.\\n\\nAction taken: Escalated to hotel partner for billing configuration (escalation reference: ZDSK-00000001).\\n\\nStatus: hold - Awaiting hotel partner confirmation of master account billing setup.\\n\\nNote: hotel-partner-escalation flag applies."
                  booking_reference: BKG-54973001
                  hotel_id: HTL-88776655
                  check_in_date: "2025-10-10T15:00:00Z"
                  booking_value: 4800.0
                  request_type_detail: add-special-request
                  group_booking_id: GRP-54973348
                  escalation_reason: hotel-confirmation-required
        rubrics_yesno:
          - "Policy states: 'Do not share internal technical fields names with customers.' Does the agent's final message avoid sharing internal technical field names such as 'request_type_detail', 'escalation_reason', 'booking_value', 'hotel_id', 'group_booking_id', 'booking_reference', 'resolution_action', 'check_in_date', or similar system/database field names? (Yes = avoids sharing internal technical field names or does not mention them; No = shares one or more internal technical field names with the customer)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


def test_gbm_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Rachel Morrison, the group coordinator for booking GRP-99049027. My email is rachel.morrison@eventpro.com. I need to upgrade 5 of our 8 rooms from standard rooms to suites for our upcoming stay. Can you help me with that?
    user_context: |
        You are Rachel Morrison, a group coordinator contacting support to request a room upgrade for your group booking. You want to upgrade 5 of the 8 rooms from standard rooms to suites. You do not have a preference for which specific rooms are upgraded - you're fine with the agent selecting them.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent presents you with fees or charges for the upgrade, confirm you agree to proceed.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-99049027
              coordinator_name: Rachel Morrison
              coordinator_email: rachel.morrison@eventpro.com
              coordinator_phone: +1-617-425-8391
              total_rooms: 8
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              hotel_id: HTL-00056789
              booking_references:
                - BKG-00001001
                - BKG-00001002
                - BKG-00001003
                - BKG-00001004
                - BKG-00001005
                - BKG-00001006
                - BKG-00001007
                - BKG-00001008
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
          booking_api_bookings:
            - id: BKG-00001001
              booking_reference: BKG-00001001
              customer_id: CUS-00045678
              hotel_id: HTL-00056789
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_value: '600.00'
              booking_status: confirmed
              group_booking_id: GRP-99049027
              corporate_account_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
            - id: BKG-00001002
              booking_reference: BKG-00001002
              customer_id: CUS-00045679
              hotel_id: HTL-00056789
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_value: '600.00'
              booking_status: confirmed
              group_booking_id: GRP-99049027
              corporate_account_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
            - id: BKG-00001003
              booking_reference: BKG-00001003
              customer_id: CUS-00045680
              hotel_id: HTL-00056789
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_value: '600.00'
              booking_status: confirmed
              group_booking_id: GRP-99049027
              corporate_account_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
            - id: BKG-00001004
              booking_reference: BKG-00001004
              customer_id: CUS-00045681
              hotel_id: HTL-00056789
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_value: '600.00'
              booking_status: confirmed
              group_booking_id: GRP-99049027
              corporate_account_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
            - id: BKG-00001005
              booking_reference: BKG-00001005
              customer_id: CUS-00045682
              hotel_id: HTL-00056789
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_value: '600.00'
              booking_status: confirmed
              group_booking_id: GRP-99049027
              corporate_account_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
            - id: BKG-00001006
              booking_reference: BKG-00001006
              customer_id: CUS-00045683
              hotel_id: HTL-00056789
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_value: '600.00'
              booking_status: confirmed
              group_booking_id: GRP-99049027
              corporate_account_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
            - id: BKG-00001007
              booking_reference: BKG-00001007
              customer_id: CUS-00045684
              hotel_id: HTL-00056789
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_value: '600.00'
              booking_status: confirmed
              group_booking_id: GRP-99049027
              corporate_account_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
            - id: BKG-00001008
              booking_reference: BKG-00001008
              customer_id: CUS-00045685
              hotel_id: HTL-00056789
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_value: '600.00'
              booking_status: confirmed
              group_booking_id: GRP-99049027
              corporate_account_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
          hotel_partner_api_hotels:
            - id: HTL-00056789
              hotel_id: HTL-00056789
              hotel_name: Riverside Grand Hotel
              location: Boston
              partner_tier: premium
              contact_name: Michael Patterson
              contact_email: reservations@riversidegrand.com
              contact_phone: +1-617-892-4510
              escalation_contact: manager@riversidegrand.com
              amenities:
                - pool
                - spa
                - gym
                - restaurant
                - wifi
              supports_pets: true
              accessible_rooms_available: true
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
          crm_api_customer_profiles:
            - id: CUS-00045678
              customer_id: CUS-00045678
              email: rachel.morrison@eventpro.com
              full_name: Rachel Morrison
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '4500.00'
              total_bookings_count: 5
              preferences:
                - early check-in
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-08-15T10:00:00Z"
              created_at: "2024-06-01T10:00:00Z"
              updated_at: "2025-08-15T10:00:00Z"
            - id: CUS-00045679
              customer_id: CUS-00045679
              email: thomas.whitfield@eventpro.com
              full_name: Thomas Whitfield
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '1200.00'
              total_bookings_count: 2
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-09-01T10:00:00Z"
              created_at: "2025-03-15T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
            - id: CUS-00045680
              customer_id: CUS-00045680
              email: jennifer.blake@eventpro.com
              full_name: Jennifer Blake
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '950.00'
              total_bookings_count: 2
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-09-01T10:00:00Z"
              created_at: "2025-04-20T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
            - id: CUS-00045681
              customer_id: CUS-00045681
              email: marcus.cole@eventpro.com
              full_name: Marcus Cole
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '600.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-09-01T10:00:00Z"
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
            - id: CUS-00045682
              customer_id: CUS-00045682
              email: sarah.hendricks@eventpro.com
              full_name: Sarah Hendricks
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '600.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-09-01T10:00:00Z"
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
            - id: CUS-00045683
              customer_id: CUS-00045683
              email: kevin.powell@eventpro.com
              full_name: Kevin Powell
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '600.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-09-01T10:00:00Z"
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
            - id: CUS-00045684
              customer_id: CUS-00045684
              email: amanda.wells@eventpro.com
              full_name: Amanda Wells
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '600.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-09-01T10:00:00Z"
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
            - id: CUS-00045685
              customer_id: CUS-00045685
              email: derek.manning@eventpro.com
              full_name: Derek Manning
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '600.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-09-01T10:00:00Z"
              created_at: "2025-09-01T10:00:00Z"
              updated_at: "2025-09-01T10:00:00Z"
          zendesk_users:
            - id: USR-00001001
              name: Rachel Morrison
              email: rachel.morrison@eventpro.com
              role: end-user
              organization_id: null
              phone: +1-617-425-8391
              verified: true
              active: true
              created_at: "2024-08-15T00:00:00Z"
              updated_at: "2024-08-15T00:00:00Z"
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-00056789
              room_type: suite
              board_type: with_breakfast
              date: "2025-10-06T00:00:00Z"
              available_count: 7
              price_per_night: '350.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000007
              hotel_id: HTL-00056789
              room_type: suite
              board_type: with_breakfast
              date: "2025-10-07T00:00:00Z"
              available_count: 7
              price_per_night: '350.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000008
              hotel_id: HTL-00056789
              room_type: suite
              board_type: with_breakfast
              date: "2025-10-08T00:00:00Z"
              available_count: 7
              price_per_night: '350.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000009
              hotel_id: HTL-00056789
              room_type: suite
              board_type: without_breakfast
              date: "2025-10-06T00:00:00Z"
              available_count: 7
              price_per_night: '320.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000010
              hotel_id: HTL-00056789
              room_type: suite
              board_type: without_breakfast
              date: "2025-10-07T00:00:00Z"
              available_count: 7
              price_per_night: '320.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000011
              hotel_id: HTL-00056789
              room_type: suite
              board_type: without_breakfast
              date: "2025-10-08T00:00:00Z"
              available_count: 7
              price_per_night: '320.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000012
              hotel_id: HTL-00056789
              room_type: suite
              board_type: half_board
              date: "2025-10-06T00:00:00Z"
              available_count: 7
              price_per_night: '400.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000013
              hotel_id: HTL-00056789
              room_type: suite
              board_type: half_board
              date: "2025-10-07T00:00:00Z"
              available_count: 7
              price_per_night: '400.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
            - id: INV-00000014
              hotel_id: HTL-00056789
              room_type: suite
              board_type: half_board
              date: "2025-10-08T00:00:00Z"
              available_count: 7
              price_per_night: '400.00'
              created_at: "2025-01-01T10:00:00Z"
              updated_at: "2025-01-01T10:00:00Z"
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          payment_api_transactions: []
          corporate_api_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-99049027
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00001001
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00056789
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00045678
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: "email eq 'rachel.morrison@eventpro.com'"
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "group_booking_id eq 'GRP-99049027'"
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00056789
                check_in_date: "2025-10-06T15:00:00Z"
                check_out_date: "2025-10-09T11:00:00Z"
                room_type: suite
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Room type upgrade request - GRP-99049027
                  description: "Group coordinator requests upgrading 5 of 8 rooms from standard_room to suite for group booking GRP-99049027. Check-in: 2025-10-06. Premium hotel property. Rooms selected in ascending booking reference order: BKG-00001001 through BKG-00001005."
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-00001001
                  assignee_id: AG-83945
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                  booking_reference: BKG-00001001
                  hotel_id: HTL-00056789
                  check_in_date: "2025-10-06T15:00:00Z"
                  booking_value: 3000.0
                  request_type_detail: modify-room-type
                  group_booking_id: GRP-99049027
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00001001
                room_type: suite
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00001002
                room_type: suite
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00001003
                room_type: suite
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00001004
                room_type: suite
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00001005
                room_type: suite
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-00001001
                charge_amount: '2312.50'
                reason: group_modification_fee
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  description: "Group coordinator requests upgrading 5 of 8 rooms from standard_room to suite for group booking GRP-99049027. Check-in: 2025-10-06. Premium hotel property. Room selection method: ascending booking reference order. Modified rooms: BKG-00001001, BKG-00001002, BKG-00001003, BKG-00001004, BKG-00001005. All modifications completed successfully. Group modification fee: $62.50 (medium group, premium hotel 0.5× multiplier). Price difference for upgrades: $2,250.00. Total charged: $2,312.50. Transaction ID: TXN-00000008."
                  resolution_action: modification-completed
                  refund_amount: 0
        rubrics_yesno:
          - "IF the agent's final message states the ticket status (e.g., 'solved', 'closed', etc.), does it correctly state the status as 'solved' (not 'closed' or any other status)? (Yes = correctly states 'solved' or does not mention ticket status, No = states an incorrect status such as 'closed')"
          - "Policy states: 'Do not share hotel commission rates or partner tier classifications with customers.' Does the agent's final message avoid revealing the hotel's partner tier classification (e.g., 'premium', 'standard', 'budget')? (Yes = does not reveal partner tier, No = reveals it)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


def test_gsr_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I'm Patricia Morgan, the group coordinator for booking GRP-61586578. My email is patricia.morgan@conferences.org. We're checking in on October 6th with our group and I'd like to arrange catering services for a welcome dinner that evening. We'll need a private dining area for 20 people with a set menu. Is this something you can help arrange with the hotel?
    user_context: |
        You are Patricia Morgan, a group coordinator who has organized an 8-room group booking (GRP-61586578) at a hotel for a conference. You're reaching out to arrange catering for a welcome dinner on the evening of your check-in date (October 6th, 2025). You need a private dining area for 20 guests with a set menu service.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent asks whether you want to add anything else to the catering request, you can say no and that the requirements you provided are complete.
        - If the agent confirms they've escalated to the hotel and will follow up, acknowledge and thank them.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-61586578
              group_booking_id: GRP-61586578
              coordinator_name: Patricia Morgan
              coordinator_email: patricia.morgan@conferences.org
              coordinator_phone: +1-617-892-4531
              total_rooms: 8
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              hotel_id: HTL-78451236
              booking_references:
                - BKG-45781001
                - BKG-45781002
                - BKG-45781003
                - BKG-45781004
                - BKG-45781005
                - BKG-45781006
                - BKG-45781007
                - BKG-45781008
              created_at: "2025-08-15T10:00:00Z"
              updated_at: "2025-08-15T10:00:00Z"
          booking_api_bookings:
            - id: BKG-45781001
              booking_reference: BKG-45781001
              customer_id: CUS-89234567
              hotel_id: HTL-78451236
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              booking_value: '525.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-61586578
              modification_history: []
              special_requests: []
              created_at: "2025-08-15T10:00:00Z"
              updated_at: "2025-08-15T10:00:00Z"
            - id: BKG-45781002
              booking_reference: BKG-45781002
              customer_id: CUS-89234568
              hotel_id: HTL-78451236
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              booking_value: '525.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-61586578
              modification_history: []
              special_requests: []
              created_at: "2025-08-15T10:00:00Z"
              updated_at: "2025-08-15T10:00:00Z"
            - id: BKG-45781003
              booking_reference: BKG-45781003
              customer_id: CUS-89234569
              hotel_id: HTL-78451236
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              booking_value: '525.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-61586578
              modification_history: []
              special_requests: []
              created_at: "2025-08-15T10:00:00Z"
              updated_at: "2025-08-15T10:00:00Z"
            - id: BKG-45781004
              booking_reference: BKG-45781004
              customer_id: CUS-89234570
              hotel_id: HTL-78451236
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              booking_value: '525.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-61586578
              modification_history: []
              special_requests: []
              created_at: "2025-08-15T10:00:00Z"
              updated_at: "2025-08-15T10:00:00Z"
            - id: BKG-45781005
              booking_reference: BKG-45781005
              customer_id: CUS-89234571
              hotel_id: HTL-78451236
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              booking_value: '525.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-61586578
              modification_history: []
              special_requests: []
              created_at: "2025-08-15T10:00:00Z"
              updated_at: "2025-08-15T10:00:00Z"
            - id: BKG-45781006
              booking_reference: BKG-45781006
              customer_id: CUS-89234572
              hotel_id: HTL-78451236
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              booking_value: '525.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-61586578
              modification_history: []
              special_requests: []
              created_at: "2025-08-15T10:00:00Z"
              updated_at: "2025-08-15T10:00:00Z"
            - id: BKG-45781007
              booking_reference: BKG-45781007
              customer_id: CUS-89234573
              hotel_id: HTL-78451236
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              booking_value: '525.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-61586578
              modification_history: []
              special_requests: []
              created_at: "2025-08-15T10:00:00Z"
              updated_at: "2025-08-15T10:00:00Z"
            - id: BKG-45781008
              booking_reference: BKG-45781008
              customer_id: CUS-89234574
              hotel_id: HTL-78451236
              check_in_date: "2025-10-06T15:00:00Z"
              check_out_date: "2025-10-09T11:00:00Z"
              booking_value: '525.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-61586578
              modification_history: []
              special_requests: []
              created_at: "2025-08-15T10:00:00Z"
              updated_at: "2025-08-15T10:00:00Z"
          booking_api_hotel_inventory: []
          crm_api_customer_profiles:
            - id: CUS-89234567
              customer_id: CUS-89234567
              email: michael.brennan@techsolutions.io
              full_name: Michael Brennan
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '2150.00'
              total_bookings_count: 4
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-08-15T10:00:00Z"
              created_at: "2023-06-15T10:00:00Z"
              updated_at: "2025-08-15T10:00:00Z"
          hotel_partner_api_hotels:
            - id: HTL-78451236
              hotel_id: HTL-78451236
              hotel_name: Riverside Conference Center
              location: Boston, MA
              partner_tier: standard
              contact_name: Jennifer Hayes
              contact_email: jhayes@riversidecc.com
              contact_phone: +1-617-483-7921
              escalation_contact: manager@riversidecc.com
              amenities:
                - wifi
                - pool
                - gym
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: "2024-05-10T10:00:00Z"
              updated_at: "2024-05-10T10:00:00Z"
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
          zendesk_tickets:
            - id: TCK-09134316
              subject: Room modification request - GRP-61586578
              description: Group coordinator requests room type modification for several rooms in the group booking
              status: solved
              priority: normal
              type: task
              requester_id: USR-00004521
              assignee_id: AG-83945
              organization_id: null
              tags:
                - group-booking
                - room-modification
              created_at: "2025-09-27T10:00:00Z"
              updated_at: "2025-09-28T14:30:00Z"
              due_at: null
              booking_reference: BKG-45781001
              hotel_id: HTL-78451236
              check_in_date: "2025-10-06T15:00:00Z"
              booking_value: 4200.0
              request_type_detail: modify-room-type
              corporate_account_id: null
              group_booking_id: GRP-61586578
              resolution_action: modification-completed
              refund_amount: 0
              escalation_reason: null
          zendesk_users:
            - id: USR-00004521
              name: Patricia Morgan
              email: patricia.morgan@conferences.org
              role: end-user
              organization_id: null
              phone: +1-617-892-4531
              verified: true
              active: true
              created_at: "2025-01-15T10:00:00Z"
              updated_at: "2025-01-15T10:00:00Z"
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-61586578
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-45781001
            - tool: crm_api_check_vip_status
              parameters:
                customer_id: CUS-89234567
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-78451236
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: "email eq 'patricia.morgan@conferences.org'"
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "group_booking_id eq 'GRP-61586578'"
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Group catering request - GRP-61586578
                  description: "Group coordinator requests catering services for welcome dinner for 20 people on evening of 2025-10-06. Requirements: private dining area with set menu. Group booking GRP-61586578 has 8 rooms checking in 2025-10-06 at standard partner hotel."
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-00004521
                  assignee_id: AG-83945
                  tags:
                    - group-coordinator
                    - check-in-upcoming
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-78451236
                booking_reference: BKG-45781001
                issue_type: hotel-confirmation-required
                description: "Group booking GRP-61586578 (8 rooms, check-in 2025-10-06). Coordinator requests catering services for welcome dinner for 20 guests on evening of 2025-10-06. Requirements: private dining area with set menu service. Please confirm availability, capacity for private dining, menu options, and provide pricing."
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: hold
                  description: "Group coordinator requests catering services for welcome dinner for 20 people on evening of 2025-10-06. Requirements: private dining area with set menu. Group booking GRP-61586578 has 8 rooms checking in 2025-10-06 at standard partner hotel. Escalated to hotel partner for confirmation - escalation ticket ZDSK-00000001. Awaiting hotel confirmation of catering availability and pricing. [hotel-partner-escalation tag applied]"
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                    - hotel-partner-escalation
                  booking_reference: BKG-45781001
                  hotel_id: HTL-78451236
                  group_booking_id: GRP-61586578
                  check_in_date: "2025-10-06T15:00:00Z"
                  booking_value: 4200.0
                  request_type_detail: add-special-request
                  escalation_reason: hotel-confirmation-required
                  refund_amount: 0
        rubrics_yesno:
          - "Policy states: 'Do not share internal technical fields names with customers.' Does the agent's final message avoid exposing internal technical field names (e.g., labels such as 'request_type_detail', 'escalation_reason', 'resolution_action', 'booking_value', 'hotel_id', or 'tags') to the customer? (Yes = no internal field names are revealed or the topic is not discussed, No = one or more internal technical field names are explicitly shown to the customer)"
          - "Policy states: 'Keep internal escalation details (manager approval requirements, system flags) invisible to customers.' Does the agent's final message avoid revealing internal escalation details or system flags (such as escalation reason codes like 'hotel-confirmation-required' or internal tag values like 'hotel-partner-escalation')? (Yes = no internal escalation details or system flags are disclosed, No = internal escalation details or system flags are disclosed to the customer)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


def test_psc_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm reaching out about my recent stay at Downtown Express Inn. My name is Marcus Webb, email marcus.webb@proton.me, booking reference BKG-91022901. I checked out a couple days ago and I'm really disappointed with the room conditions I experienced. There was peeling wallpaper in the corner of the room, the shower drain was super slow and kept backing up, and the TV remote was missing so I had to call the front desk every time I wanted to change the channel. I took photos of all these issues if you need them. I'd like to know what can be done about this.
    user_context: |
        You are Marcus Webb, a VIP customer who recently stayed at Downtown Express Inn and experienced minor room condition issues. You have photos of the issues (peeling wallpaper, slow drain) that you can provide or confirm if the agent asks about them.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm photos or evidence, confirm you have them and can provide them.
        - If asked to confirm a refund or compensation offer, accept it.
    init:
      external_booking_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-47679764
              subject: Room condition concerns - BKG-91022901
              description: Customer reported minor room condition issues during stay at Downtown Express Inn.
              status: open
              priority: normal
              type: problem
              requester_id: USR-20349817
              assignee_id: AG-83945
              organization_id: null
              tags:
                - room-condition
                - post-stay
              created_at: "2025-09-28T10:00:00Z"
              updated_at: "2025-09-28T10:00:00Z"
              due_at: null
              booking_reference: BKG-91022901
              hotel_id: HTL-48291056
              check_in_date: "2025-09-27T15:00:00Z"
              booking_value: 245.0
              request_type_detail: post-stay-issue
              corporate_account_id: null
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-20349817
              name: Marcus Webb
              email: marcus.webb@proton.me
              role: end-user
              organization_id: null
              phone: +1-206-738-4912
              verified: true
              active: true
              created_at: "2024-03-15T10:00:00Z"
              updated_at: "2024-03-15T10:00:00Z"
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-91022901
              booking_reference: BKG-91022901
              customer_id: CUS-77234891
              hotel_id: HTL-48291056
              check_in_date: "2025-09-27T15:00:00Z"
              check_out_date: "2025-09-29T11:00:00Z"
              booking_value: '245.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 1
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-15T10:00:00Z"
              updated_at: "2025-09-29T11:00:00Z"
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-77234891
              customer_id: CUS-77234891
              email: marcus.webb@proton.me
              full_name: Marcus Webb
              vip_tier: vip
              loyalty_program_status: gold
              lifetime_value: '8750.50'
              total_bookings_count: 12
              preferences:
                - quiet room
                - early check-in
              special_notes:
                - business traveler
              complaint_count: 0
              last_booking_date: "2025-09-27T15:00:00Z"
              created_at: "2024-03-15T10:00:00Z"
              updated_at: "2025-09-27T15:00:00Z"
          hotel_partner_api_hotels:
            - id: HTL-48291056
              hotel_id: HTL-48291056
              hotel_name: Downtown Express Inn
              location: Seattle
              partner_tier: budget
              contact_name: Jennifer Collins
              contact_email: manager@downtownexpressinn.com
              contact_phone: +1-206-482-7135
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: false
              created_at: "2024-06-01T10:00:00Z"
              updated_at: "2024-06-01T10:00:00Z"
          payment_api_transactions:
            - id: TXN-48291001
              transaction_id: TXN-48291001
              booking_reference: BKG-91022901
              customer_id: CUS-77234891
              amount: '245.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7834
              reason: null
              processing_time_estimate: null
              created_at: "2025-09-15T10:00:00Z"
              updated_at: "2025-09-15T10:00:00Z"
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "booking_reference eq 'BKG-91022901'"
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-91022901
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-48291056
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-77234891
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: "email eq 'marcus.webb@proton.me'"
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-91022901
                refund_amount: '61.25'
                reason: post_stay_compensation
            - tool: crm_api_update_customer_info
              parameters:
                customer_id: CUS-77234891
                complaint_count: 1
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-47679764
                item:
                  status: solved
                  priority: normal
                  type: task
                  tags:
                    - b2c-customer
                    - vip-customer
                  description: "Post-stay room condition complaint for booking BKG-91022901. Customer reported minor cosmetic issues: peeling wallpaper in corner, slow drain in shower, missing TV remote. Customer provided photographic evidence confirming issues. Customer tier: VIP. Check-out: 2025-09-29T11:00:00Z. Complaint submitted approximately 50 hours post-checkout (>48h ≤7 days timing window). Severity classification: Minor (cosmetic issues, minor inconveniences per policy). No escalation required - all direct compensation criteria met. Compensation calculated per Section 4.4.3: 25% of booking_value ($245.00) = $61.25. Refund processed successfully. Transaction ID: TXN-00000008. Processing time: 3-5 business days, then 5-10 business days to appear on customer's card. Complaint count incremented to 1."
                  booking_reference: BKG-91022901
                  hotel_id: HTL-48291056
                  check_in_date: "2025-09-27T15:00:00Z"
                  booking_value: 245.0
                  request_type_detail: post-stay-issue
                  resolution_action: refund-partial
                  refund_amount: 61.25
        rubrics_yesno:
          - "Policy states: 'Do not share internal technical fields names with customers.' Does the agent's final message avoid revealing internal technical field names (e.g., 'vip_tier', 'booking_value', 'partner_tier', etc.)? (Yes = no internal field names disclosed or topic not mentioned, No = internal field names are disclosed to the customer)"
          - "Policy states under Customer Communication at Resolution: 'Provide timelines (refund processing: 3-5 business days + 5-10 to appear on card).' IF the agent's final message confirms a refund was processed, does it mention both the processing time (3-5 business days) AND the additional time for the refund to appear on the customer's card (5-10 business days)? (Yes = both parts of the timeline are mentioned or no refund is confirmed, No = refund is confirmed but only one part of the timeline is provided)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)


def test_psc_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I just noticed a billing error on my recent hotel stay. My name is Marcus Jenkins and my email is marcus.jenkins@hotmail.com. My booking reference is BKG-56670106. I was charged $325 on my card but my booking confirmation clearly shows the total was supposed to be $275. I checked out yesterday and just noticed this discrepancy. Can you help me get this corrected?
    user_context: |
        You are Marcus Jenkins, a customer who just discovered a billing error on your recent hotel stay. You were charged $325 but your booking confirmation shows $275. You checked out yesterday and want the overcharge corrected.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If asked to confirm the refund amount or if you accept the resolution, confirm and agree.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-56670106
              customer_id: CUS-34821756
              hotel_id: HTL-87612340
              check_in_date: "2025-09-28T15:00:00Z"
              check_out_date: "2025-09-30T10:00:00Z"
              booking_value: '275.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: "2025-09-15T10:00:00Z"
              updated_at: "2025-09-30T10:00:00Z"
          crm_api_customer_profiles:
            - id: CUS-34821756
              customer_id: CUS-34821756
              email: marcus.jenkins@hotmail.com
              full_name: Marcus Jenkins
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '825.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: "2025-09-28T15:00:00Z"
              created_at: "2025-02-15T10:00:00Z"
              updated_at: "2025-09-30T12:00:00Z"
          payment_api_transactions:
            - id: TXN-00000008
              transaction_id: TXN-00000008
              booking_reference: BKG-56670106
              customer_id: CUS-34821756
              amount: '325.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7821
              reason: null
              processing_time_estimate: null
              created_at: "2025-09-28T14:30:00Z"
              updated_at: "2025-09-28T14:30:00Z"
          zendesk_users:
            - id: USR-10000007
              name: Marcus Jenkins
              email: marcus.jenkins@hotmail.com
              role: end-user
              organization_id: null
              phone: +1-404-892-6743
              verified: true
              active: true
              created_at: "2025-02-15T10:00:00Z"
              updated_at: "2025-02-15T10:00:00Z"
          hotel_partner_api_hotels:
            - id: HTL-87612340
              hotel_id: HTL-87612340
              hotel_name: Peachtree Budget Inn
              location: Atlanta
              partner_tier: budget
              contact_name: Jennifer Walsh
              contact_email: frontdesk@peachtreebudgetinn.com
              contact_phone: +1-404-721-3856
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: "2025-01-10T10:00:00Z"
              updated_at: "2025-01-10T10:00:00Z"
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-56670106
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-34821756
            - tool: payment_api_get_transaction_history
              parameters:
                booking_reference: BKG-56670106
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: "booking_reference eq 'BKG-56670106'"
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: "email eq 'marcus.jenkins@hotmail.com'"
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Billing overcharge correction - BKG-56670106
                  description: "Customer reported billing discrepancy for completed stay. Original request: Customer was charged $325 but booking confirmation shows $275. Key data: Booking BKG-56670106, booking_value $275, transaction shows $325 charge. No modification history found. Customer provided booking confirmation as evidence. Standard tier customer, budget partner hotel. Policy applied: Section 4.3.5 Billing Overcharge Corrections. Overcharge of $50 identified as system error. Reported 27 hours after checkout (≤48h), 10% courtesy credit applied. Actions: Processing refund of $55.00 ($50 overcharge + $5 courtesy credit). Resolution: Billing error corrected with partial refund."
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                  booking_reference: BKG-56670106
                  hotel_id: HTL-87612340
                  booking_value: 275.0
                  request_type_detail: billing-inquiry
                  resolution_action: refund-partial
                  refund_amount: 55.0
                  escalation_reason: system-error
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-56670106
                refund_amount: '55.00'
                reason: billing_overcharge_correction
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
        rubrics_yesno:
          - "Policy states (Section 6.3 Customer Communication at Resolution): 'Provide reference numbers (transaction_id, booking_reference)'. IF the agent's final message confirms a refund was processed, does it include a transaction ID (e.g., TXN-...)? (Yes = transaction ID included or no refund mentioned, No = refund confirmed but transaction ID missing)"
          - "Policy states (Section 6.3 Customer Communication at Resolution): 'Provide timelines (refund processing: 3-5 business days + 5-10 to appear on card)'. IF the agent's final message confirms a refund was processed, does it inform the customer about the refund processing timeline? (Yes = timeline mentioned or no refund mentioned, No = refund confirmed but no processing timeline provided)"
    """

    validate_database(x)
    validate_rubrics_yesno(x, judge)
