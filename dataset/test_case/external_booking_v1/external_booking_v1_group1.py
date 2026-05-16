# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

from thinkingbox.common import Judge, TestContext

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


def validate_rubrics(x: TestContext, judge: Judge):
    rubrics_definitions = x.effects[SERVER_NAME].get("rubrics", {})

    # Evaluate rubrics using Judge FIRST (before any assertions)
    score_list = []
    rubric_results = {}
    total_score = 0
    total_possible = 0

    if not rubrics_definitions:
        return

    agent_response = x.response

    for rubric_id, rubric_config in rubrics_definitions.items():
        criteria_text = rubric_config.get("criteria_text", "")
        reward = rubric_config.get("reward", 0)

        # Use Judge to evaluate the rubric
        score_result = judge.custom_rubric_score(
            message=agent_response, rubric=criteria_text, numerical_score=reward
        )

        score_list.append(score_result)
        rubric_results[rubric_id] = {
            "criteria_text": criteria_text,
            "score": score_result["score"],
            "total_score": score_result["total_score"],
        }

    total_score = sum(item["score"] for item in score_list)
    total_possible = sum(
        item["total_score"] for item in score_list if item["total_score"] > 0
    )

    assert judge.numerical_threshold(
        score_list
    ), f"Rubrics threshold not met: {total_score}/{total_possible} < 70%"


def test_bmd_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to change my check-in date for booking BKG-10433218. I'm Marcus Wellington, email marcus.wellington@protonmail.com. I was supposed to check in today October 1st, but something came up and I need to push it back to October 2nd instead. Is that possible?
    user_context: |
        You are Marcus Wellington, a customer contacting support to change your hotel booking check-in date from October 1st (today) to October 2nd. Your booking reference is BKG-10433218.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If the agent mentions a modification fee or that they need to confirm with the hotel, acknowledge this and express understanding. You accept any reasonable fees for the date change.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-10433218
              booking_reference: BKG-10433218
              customer_id: CUS-10433218
              hotel_id: HTL-10433218
              check_in_date: '2025-10-01T15:00:00Z'
              check_out_date: '2025-10-02T11:00:00Z'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_value: '450.00'
              booking_status: confirmed
              modification_history: []
              corporate_account_id: null
              group_booking_id: null
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory:
            - id: INV-10433001
              hotel_id: HTL-10433218
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-02T00:00:00Z'
              available_count: 3
              price_per_night: '450.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-10433002
              hotel_id: HTL-10433218
              room_type: deluxe_room
              board_type: without_breakfast
              date: '2025-10-02T00:00:00Z'
              available_count: 3
              price_per_night: '420.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-10433003
              hotel_id: HTL-10433218
              room_type: deluxe_room
              board_type: half_board
              date: '2025-10-02T00:00:00Z'
              available_count: 3
              price_per_night: '480.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-10433218
              customer_id: CUS-10433218
              email: marcus.wellington@protonmail.com
              full_name: Marcus Wellington
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '450.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-10433218
              hotel_id: HTL-10433218
              hotel_name: The Harrington Suites
              location: Boston
              partner_tier: premium
              contact_name: Victoria Reynolds
              contact_email: reservations@harringtonsuites.com
              contact_phone: +1-617-482-3109
              escalation_contact: manager@harringtonsuites.com
              amenities:
                - wifi
                - gym
                - concierge
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
          payment_api_transactions:
            - id: TXN-10433218
              transaction_id: TXN-10433218
              booking_reference: BKG-10433218
              customer_id: CUS-10433218
              amount: '450.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7823
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          zendesk_tickets: []
          zendesk_users:
            - id: USR-10433218
              name: Marcus Wellington
              email: marcus.wellington@protonmail.com
              role: end-user
              organization_id: null
              phone: +1-617-384-2917
              verified: true
              active: true
              created_at: '2025-09-01T00:00:00Z'
              updated_at: '2025-09-01T00:00:00Z'
            - id: USR-10433001
              name: Jennifer Walsh
              email: jennifer.walsh@staybridge.com
              role: agent
              organization_id: null
              phone: +1-617-555-0147
              verified: true
              active: true
              created_at: '2025-01-01T00:00:00Z'
              updated_at: '2025-01-01T00:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-10433218
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-10433218
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-10433218
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-10433218
                check_in_date: '2025-10-02T15:00:00Z'
                check_out_date: '2025-10-03T11:00:00Z'
                room_type: deluxe_room
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.wellington@protonmail.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-10433218'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Date modification request - BKG-10433218
                  description: 'Customer requests to change check-in date from 2025-10-01 to 2025-10-02. Same-day modification at premium partner hotel. Customer tier: standard. B2C individual traveler. Availability confirmed in system for deluxe_room with breakfast, 2 adults. Requires hotel partner confirmation for same-day modification per policy (standard tier customers). Modification fee of $30 will apply upon hotel approval. Note: hotel-partner-escalation tag applies but cannot be stored in tags field.'
                  status: open
                  priority: urgent
                  type: task
                  requester_id: USR-10433218
                  assignee_id: AG-83945
                  booking_reference: BKG-10433218
                  hotel_id: HTL-10433218
                  check_in_date: '2025-10-02T15:00:00Z'
                  booking_value: 450.0
                  request_type_detail: modify-dates
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-10433218
                booking_reference: BKG-10433218
                issue_type: same-day-modification
                description: 'Customer requests to change check-in date from 2025-10-01 to 2025-10-02. Deluxe room with breakfast for 2 adults, 0 children. Original booking value: $450. Room availability confirmed in StayBridge system. Modification fee of $30 will apply upon approval. Please confirm if this same-day date change can be accommodated.'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: hold
                  tags:
                    - b2c-customer
                    - check-in-today
                    - hotel-partner-escalation
                  escalation_reason: same-day-modification
                  refund_amount: 0.0
    """

    validate_database(x)


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
              check_in_date: '2025-10-01T18:00:00Z'
              check_out_date: '2025-10-03T11:00:00Z'
              room_type: suite
              board_type: half_board
              adults_count: 2
              children_count: 2
              booking_status: confirmed
              booking_value: '890.00'
              modification_history:
                - '2025-09-28T10:00:00Z: room_type: standard_room -> suite'
              special_requests: []
              corporate_account_id: null
              group_booking_id: null
              created_at: '2025-09-20T10:00:00Z'
              updated_at: '2025-09-28T10:00:00Z'
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
              last_booking_date: '2025-09-20T10:00:00Z'
              created_at: '2024-06-15T10:00:00Z'
              updated_at: '2025-09-20T10:00:00Z'
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
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Victoria Martinez
              email: victoria.martinez@outlook.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-312-594-8176
              verified: true
              active: true
              created_at: '2024-06-15T00:00:00Z'
              updated_at: '2024-06-15T00:00:00Z'
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
              created_at: '2025-09-29T13:00:00Z'
              updated_at: '2025-09-29T15:00:00Z'
              due_at: null
              booking_reference: BKG-33754330
              hotel_id: HTL-33754330
              check_in_date: '2025-10-01T18:00:00Z'
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
              date: '2025-10-01T00:00:00Z'
              available_count: 2
              price_per_night: '475.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-33754002
              hotel_id: HTL-33754330
              room_type: suite
              board_type: full_board
              date: '2025-10-02T00:00:00Z'
              available_count: 2
              price_per_night: '475.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-33754003
              hotel_id: HTL-33754330
              room_type: suite
              board_type: half_board
              date: '2025-10-01T00:00:00Z'
              available_count: 2
              price_per_night: '445.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-33754004
              hotel_id: HTL-33754330
              room_type: suite
              board_type: half_board
              date: '2025-10-02T00:00:00Z'
              available_count: 2
              price_per_night: '445.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-33754005
              hotel_id: HTL-33754330
              room_type: suite
              board_type: with_breakfast
              date: '2025-10-01T00:00:00Z'
              available_count: 2
              price_per_night: '420.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-33754006
              hotel_id: HTL-33754330
              room_type: suite
              board_type: with_breakfast
              date: '2025-10-02T00:00:00Z'
              available_count: 2
              price_per_night: '420.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-33754007
              hotel_id: HTL-33754330
              room_type: suite
              board_type: without_breakfast
              date: '2025-10-01T00:00:00Z'
              available_count: 2
              price_per_night: '395.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-33754008
              hotel_id: HTL-33754330
              room_type: suite
              board_type: without_breakfast
              date: '2025-10-02T00:00:00Z'
              available_count: 2
              price_per_night: '395.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
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
                filter: email eq 'victoria.martinez@outlook.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-33754330'
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-33754330
                check_in_date: '2025-10-01T18:00:00Z'
                check_out_date: '2025-10-03T11:00:00Z'
                room_type: suite
                board_type: full_board
                adults_count: 2
                children_count: 2
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Board type modification request - BKG-33754330
                  description: 'Customer requests board type change from half_board to full_board for booking BKG-33754330. Check-in: 2025-10-01T18:00:00Z (today, same-day modification). Premium partner hotel. Customer VIP tier: vip - hotel escalation not required per policy 4.1.5. Availability verified. Fee calculation: Base fee $60 × 0.5 (premium tier) + $15 surcharge (2nd modification) = $45 modification fee. Price difference: $60. Total charge: $105.'
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
                  check_in_date: '2025-10-01T18:00:00Z'
                  booking_value: 950.0
                  request_type_detail: modify-board-type
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


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
              check_in_date: '2025-10-02T12:00:00Z'
              check_out_date: '2025-10-04T11:00:00Z'
              booking_value: '1250.00'
              room_type: executive_suite
              board_type: full_board
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history:
                - '2025-09-15T10:00:00Z: check_in_date: 2025-10-01T12:00:00Z -> 2025-10-02T12:00:00Z'
                - '2025-09-20T14:30:00Z: board_type: half_board -> full_board'
              special_requests: []
              created_at: '2025-09-10T09:00:00Z'
              updated_at: '2025-09-20T14:30:00Z'
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
              last_booking_date: '2025-09-15T14:00:00Z'
              created_at: '2024-03-10T10:00:00Z'
              updated_at: '2025-09-15T14:00:00Z'
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
              created_at: '2024-06-15T10:00:00Z'
              updated_at: '2024-06-15T10:00:00Z'
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
              created_at: '2025-09-21T11:30:00Z'
              updated_at: '2025-09-21T14:00:00Z'
              due_at: null
              booking_reference: BKG-60883561
              hotel_id: HTL-60883561
              check_in_date: '2025-10-02T12:00:00Z'
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
              created_at: '2024-05-20T10:00:00Z'
              updated_at: '2024-05-20T10:00:00Z'
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
                filter: email eq 'marcus.wellington@techventures.io'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-60883561'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Late checkout request - BKG-60883561
                  description: 'Customer requesting late checkout for booking BKG-60883561. Customer is VIP tier. Check-in: 2025-10-02 (23 hours away). Hotel: Premium tier. Processing same-day special request per Section 4.5.2.'
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
                  check_in_date: '2025-10-02T12:00:00Z'
                  booking_value: 1250.0
                  request_type_detail: add-special-request
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


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
              check_in_date: '2025-10-02T16:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              booking_value: '420.00'
              room_type: family_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 3
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history:
                - '2025-09-15T10:30:00Z: check_in_date: 2025-10-01T16:00:00Z -> 2025-10-02T16:00:00Z'
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-15T10:30:00Z'
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
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2024-08-15T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
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
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Michael Reynolds
              email: michael.reynolds@protonmail.com
              role: end-user
              organization_id: null
              phone: +1-206-394-7281
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
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
                filter: booking_reference eq 'BKG-56482366'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'michael.reynolds@protonmail.com'
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
                  check_in_date: '2025-10-02T16:00:00Z'
                  booking_value: 420.0
                  request_type_detail: modify-guests
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_bmd_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I need to extend my hotel stay.
    user_context: |
        You are Victoria Chen, a customer contacting support to extend your hotel stay.

        Only if you are asked about your name — tell the agent you are Victoria Chen.
        Only if you are asked about your email address — tell the agent it is victoria.chen@datalogic.net.
        Only if you are asked about your booking reference or confirmation number — tell the agent it is BKG-73872148.
        Only if you are asked about your current checkout date — tell the agent you are currently scheduled to check out on October 6th, 2025.
        Only if you are asked about how long you want to extend or how many additional nights — tell the agent you would like to stay 2 additional nights.
        Only if you are asked about your new checkout date — tell the agent you would like to check out on October 8th, 2025 instead.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If asked to confirm the cost for the additional nights, agree to proceed with the modification.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-73872148
              customer_id: CUS-00000006
              hotel_id: HTL-00012350
              check_in_date: '2025-10-04T14:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              booking_value: '680.00'
              room_type: suite
              board_type: half_board
              adults_count: 3
              children_count: 1
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: victoria.chen@datalogic.net
              full_name: Victoria Chen
              vip_tier: platinum
              loyalty_program_status: platinum-elite
              lifetime_value: '28750.50'
              total_bookings_count: 42
              preferences:
                - quiet room
                - high floor
              special_notes:
                - prefers morning check-in calls
              complaint_count: 0
              last_booking_date: '2025-09-20T14:00:00Z'
              created_at: '2023-06-10T00:00:00Z'
              updated_at: '2025-09-20T00:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00012350
              hotel_id: HTL-00012350
              hotel_name: Riverside Suites Hotel
              location: Chicago
              partner_tier: standard
              contact_name: Patricia Reynolds
              contact_email: manager@riversidesuites.com
              contact_phone: +1-312-847-2956
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - breakfast
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Victoria Chen
              email: victoria.chen@datalogic.net
              role: end-user
              organization_id: ORG-10000002
              phone: +1-312-694-7831
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-00012350
              room_type: suite
              board_type: half_board
              date: '2025-10-04T00:00:00Z'
              available_count: 2
              price_per_night: '340.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-00012350
              room_type: suite
              board_type: half_board
              date: '2025-10-05T00:00:00Z'
              available_count: 2
              price_per_night: '340.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000008
              hotel_id: HTL-00012350
              room_type: suite
              board_type: half_board
              date: '2025-10-06T00:00:00Z'
              available_count: 2
              price_per_night: '340.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000009
              hotel_id: HTL-00012350
              room_type: suite
              board_type: half_board
              date: '2025-10-07T00:00:00Z'
              available_count: 2
              price_per_night: '340.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000010
              hotel_id: HTL-00012350
              room_type: suite
              board_type: full_board
              date: '2025-10-04T00:00:00Z'
              available_count: 2
              price_per_night: '380.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000011
              hotel_id: HTL-00012350
              room_type: suite
              board_type: full_board
              date: '2025-10-05T00:00:00Z'
              available_count: 2
              price_per_night: '380.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000012
              hotel_id: HTL-00012350
              room_type: suite
              board_type: full_board
              date: '2025-10-06T00:00:00Z'
              available_count: 2
              price_per_night: '380.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000013
              hotel_id: HTL-00012350
              room_type: suite
              board_type: full_board
              date: '2025-10-07T00:00:00Z'
              available_count: 2
              price_per_night: '380.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000014
              hotel_id: HTL-00012350
              room_type: suite
              board_type: all_inclusive
              date: '2025-10-04T00:00:00Z'
              available_count: 2
              price_per_night: '450.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000015
              hotel_id: HTL-00012350
              room_type: suite
              board_type: all_inclusive
              date: '2025-10-05T00:00:00Z'
              available_count: 2
              price_per_night: '450.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000016
              hotel_id: HTL-00012350
              room_type: suite
              board_type: all_inclusive
              date: '2025-10-06T00:00:00Z'
              available_count: 2
              price_per_night: '450.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000017
              hotel_id: HTL-00012350
              room_type: suite
              board_type: all_inclusive
              date: '2025-10-07T00:00:00Z'
              available_count: 2
              price_per_night: '450.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
          lookup_bookings: []
          lookup_hotels: []
          lookup_group_bookings: []
          lookup_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-73872148
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00012350
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-73872148'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'victoria.chen@datalogic.net'
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00012350
                check_in_date: '2025-10-04T14:00:00Z'
                check_out_date: '2025-10-08T11:00:00Z'
                room_type: suite
                board_type: half_board
                adults_count: 3
                children_count: 1
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Date modification request - BKG-73872148
                  description: 'Customer requests to extend stay by 2 nights. Original dates: 2025-10-04 to 2025-10-06. Requested new check-out: 2025-10-08. Platinum customer - modification fee waived. Verifying availability and processing.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                  booking_reference: BKG-73872148
                  hotel_id: HTL-00012350
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-73872148
                check_out_date: '2025-10-08T11:00:00Z'
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-73872148
                charge_amount: '680.00'
                reason: price_difference
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  description: 'Customer requested to extend stay by 2 nights. Original dates: 2025-10-04 to 2025-10-06. New dates: 2025-10-04 to 2025-10-08. Platinum customer (vip_tier: platinum) - modification fee waived per Section 4.1.4. Price difference of $680.00 charged for additional 2 nights. Modification completed successfully.'
                  check_in_date: '2025-10-04T14:00:00Z'
                  booking_value: 1360.0
                  request_type_detail: modify-dates
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


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
              check_in_date: '2025-10-06T14:00:00Z'
              check_out_date: '2025-10-08T11:00:00Z'
              booking_value: '340.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 2
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history:
                - '2025-09-25T10:00:00Z: board_type: without_breakfast -> with_breakfast'
              special_requests: []
              created_at: '2025-09-18T09:30:00Z'
              updated_at: '2025-09-25T10:00:00Z'
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
              last_booking_date: '2025-09-18T09:30:00Z'
              created_at: '2024-08-15T10:00:00Z'
              updated_at: '2025-09-18T09:30:00Z'
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
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
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
              created_at: '2025-09-29T13:00:00Z'
              updated_at: '2025-09-29T15:00:00Z'
              due_at: null
              booking_reference: BKG-93676320
              hotel_id: HTL-00012350
              check_in_date: '2025-10-06T14:00:00Z'
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
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-00012350
              room_type: family_room
              board_type: with_breakfast
              date: '2025-10-06T00:00:00Z'
              available_count: 2
              price_per_night: '200.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-00012350
              room_type: family_room
              board_type: with_breakfast
              date: '2025-10-07T00:00:00Z'
              available_count: 2
              price_per_night: '200.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000008
              hotel_id: HTL-00012350
              room_type: family_room
              board_type: without_breakfast
              date: '2025-10-06T00:00:00Z'
              available_count: 2
              price_per_night: '175.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000009
              hotel_id: HTL-00012350
              room_type: family_room
              board_type: without_breakfast
              date: '2025-10-07T00:00:00Z'
              available_count: 2
              price_per_night: '175.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000010
              hotel_id: HTL-00012350
              room_type: family_room
              board_type: half_board
              date: '2025-10-06T00:00:00Z'
              available_count: 2
              price_per_night: '235.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000011
              hotel_id: HTL-00012350
              room_type: family_room
              board_type: half_board
              date: '2025-10-07T00:00:00Z'
              available_count: 2
              price_per_night: '235.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
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
                filter: booking_reference eq 'BKG-93676320'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'victoria.miller@outlook.com'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-16328708
                item:
                  status: open
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00012350
                check_in_date: '2025-10-06T14:00:00Z'
                check_out_date: '2025-10-08T11:00:00Z'
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
                  check_in_date: '2025-10-06T14:00:00Z'
                  booking_value: 400.0
                  request_type_detail: modify-room-type
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_bmd_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I have a booking at Harbor View Lodge next week and I was wondering if I could request an early check-in. My name is Marcus Riley, email marcus.riley@mailbox.org, and my booking reference is BKG-57986872. We're traveling with our child and it would be really helpful to get into the room earlier if possible. Can you help with that?
    user_context: |
        You are Marcus Riley, a customer contacting StayBridge support to add an early check-in request to your upcoming booking BKG-57986872.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If the agent informs you about a fee (such as $25 for early check-in), accept it and confirm you want to proceed.
        - You understand early check-in is subject to availability at the hotel.
    init:
      external_booking_v1:
        data_patch:
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: marcus.riley@mailbox.org
              full_name: Marcus Riley
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '850.00'
              total_bookings_count: 4
              preferences:
                - quiet room
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-03-15T00:00:00Z'
              updated_at: '2025-09-15T12:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Riley
              email: marcus.riley@mailbox.org
              role: end-user
              organization_id: ORG-10000002
              phone: +1-206-847-3294
              verified: true
              active: true
              created_at: '2025-03-15T00:00:00Z'
              updated_at: '2025-03-15T00:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-57986872
              customer_id: CUS-00000006
              hotel_id: HTL-00012350
              check_in_date: '2025-10-07T14:00:00Z'
              check_out_date: '2025-10-10T11:00:00Z'
              booking_value: '410.00'
              room_type: deluxe_room
              board_type: half_board
              adults_count: 2
              children_count: 1
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history:
                - '2025-09-20T10:00:00Z: board_type: with_breakfast -> half_board'
                - '2025-09-22T14:30:00Z: adults_count: 1 -> 2'
                - '2025-09-25T09:15:00Z: check_out_date: 2025-10-09T11:00:00Z -> 2025-10-10T11:00:00Z'
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-25T09:15:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00012350
              hotel_name: Harbor View Lodge
              location: Seattle
              partner_tier: budget
              contact_name: Patricia Wong
              contact_email: frontdesk@harborviewlodge.com
              contact_phone: +1-206-493-7821
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: false
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_tickets:
            - id: TCK-77434873
              subject: Booking modification request - BKG-57986872
              description: Customer requested modification to booking BKG-57986872.
              status: solved
              priority: normal
              type: task
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: ORG-10000002
              tags:
                - booking-modification
                - b2c-customer
              created_at: '2025-09-23T10:00:00Z'
              updated_at: '2025-09-23T14:00:00Z'
              due_at: null
              booking_reference: BKG-57986872
              hotel_id: HTL-00012350
              check_in_date: '2025-10-07T14:00:00Z'
              booking_value: 410.0
              request_type_detail: modify-dates
              corporate_account_id: null
              group_booking_id: null
              resolution_action: modification-completed
              refund_amount: 0.0
              escalation_reason: null
          payment_api_transactions:
            - id: TXN-20000001
              transaction_id: TXN-20000001
              booking_reference: BKG-57986872
              customer_id: CUS-00000006
              amount: '410.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7892
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-15T10:05:00Z'
              updated_at: '2025-09-15T10:05:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: crm_api_get_customer_profile
              parameters:
                email: marcus.riley@mailbox.org
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.riley@mailbox.org'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-57986872
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00012350
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-57986872'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Early check-in request - BKG-57986872
                  description: 'Customer requests early check-in for booking BKG-57986872. Check-in date: 2025-10-07. Hotel: Harbor View Lodge (budget tier). Customer tier: standard. Early check-in fee of $25 applies. Subject to availability.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-57986872
                  hotel_id: HTL-00012350
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-57986872
                special_requests:
                  - Early check-in requested - subject to availability
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-57986872
                charge_amount: '25.00'
                reason: early_check_in_fee
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  check_in_date: '2025-10-07T14:00:00Z'
                  booking_value: 410.0
                  request_type_detail: add-special-request
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_bmd_015(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I'd like to upgrade my room for my upcoming stay.
    user_context: |
        You are Maria Santos, a customer contacting support to upgrade your hotel room from executive suite to presidential suite for your upcoming booking.

        Only if you are asked about your booking reference or confirmation number — it is BKG-47143455.
        Only if you are asked about your name — your name is Maria Santos.
        Only if you are asked about your email address — it is maria.santos@outlook.com.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If asked to confirm the room upgrade or any additional charges for the price difference, agree and confirm you want to proceed.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000010
              booking_reference: BKG-47143455
              customer_id: CUS-00047143
              hotel_id: HTL-00047143
              check_in_date: '2025-10-09T14:00:00Z'
              check_out_date: '2025-10-11T11:00:00Z'
              booking_value: '1100.00'
              room_type: executive_suite
              board_type: full_board
              adults_count: 2
              children_count: 2
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00047143
              customer_id: CUS-00047143
              email: maria.santos@outlook.com
              full_name: Maria Santos
              vip_tier: platinum
              loyalty_program_status: platinum-elite
              lifetime_value: '8500.00'
              total_bookings_count: 5
              preferences:
                - quiet room
                - high floor
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2024-01-15T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00047143
              hotel_id: HTL-00047143
              hotel_name: The Ritz Pavillon
              location: Chicago
              partner_tier: premium
              contact_name: Patricia Wellman
              contact_email: manager@ritzpavillon.com
              contact_phone: +1-312-847-9821
              escalation_contact: director@ritzpavillon.com
              amenities:
                - pool
                - gym
                - spa
                - restaurant
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-00047143
              room_type: presidential_suite
              board_type: full_board
              date: '2025-10-09T00:00:00Z'
              available_count: 3
              price_per_night: '750.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-00047143
              room_type: presidential_suite
              board_type: full_board
              date: '2025-10-10T00:00:00Z'
              available_count: 3
              price_per_night: '750.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10047143
              name: Maria Santos
              email: maria.santos@outlook.com
              role: end-user
              organization_id: null
              phone: +1-312-549-7823
              verified: true
              active: true
              created_at: '2024-01-15T10:00:00Z'
              updated_at: '2024-01-15T10:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-47143455
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00047143
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00047143
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00047143
                check_in_date: '2025-10-09T14:00:00Z'
                check_out_date: '2025-10-11T11:00:00Z'
                room_type: presidential_suite
                board_type: full_board
                adults_count: 2
                children_count: 2
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'maria.santos@outlook.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-47143455'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Room type modification request - BKG-47143455
                  description: 'Customer requests room type change from executive_suite to presidential_suite. Platinum customer with booking at premium hotel. Check-in: 2025-10-09. Time until check-in: 193 hours (≥7 days). Modification fee: $0 (platinum waiver applies). Price difference: $400.00 charge required.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10047143
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                  booking_reference: BKG-47143455
                  hotel_id: HTL-00047143
                  request_type_detail: modify-room-type
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-47143455
                room_type: presidential_suite
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-47143455
                charge_amount: '400.00'
                reason: price_difference
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  description: 'Customer requests room type change from executive_suite to presidential_suite. Platinum customer with booking at premium hotel. Check-in: 2025-10-09. Time until check-in: 193 hours (≥7 days). Modification fee: $0 (platinum waiver applies). Price difference: $400.00 charge processed. RESOLUTION: Room type successfully modified to presidential_suite. Additional charge of $400.00 processed (TXN-00000008). New booking value: $1,500.00.'
                  check_in_date: '2025-10-09T14:00:00Z'
                  booking_value: 1500.0
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_bmd_017(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I need to change the dates for my upcoming hotel booking. My name is Marcus Wellington, email marcus.wellington@techmail.net. The booking reference is BKG-36690967. I'd like to move my check-in from October 15th to October 20th instead. Is that possible?
    user_context: |
        You are Marcus Wellington, a customer contacting StayBridge support to change your hotel booking dates. You want to move your check-in from October 15 to October 20, 2025.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If the agent mentions a modification fee (such as $15), confirm you are okay with proceeding and accept the charge.
        - You want to keep the same duration of stay (4 nights), just shifted to the new dates.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-36690967
              booking_reference: BKG-36690967
              customer_id: CUS-00056789
              hotel_id: HTL-00078901
              check_in_date: '2025-10-15T14:00:00Z'
              check_out_date: '2025-10-19T11:00:00Z'
              booking_value: '560.00'
              room_type: family_room
              board_type: with_breakfast
              adults_count: 3
              children_count: 2
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history:
                - '2025-09-20T10:00:00Z: check_in_date: 2025-10-10T14:00:00Z -> 2025-10-15T14:00:00Z'
              special_requests: []
              created_at: '2025-09-15T12:00:00Z'
              updated_at: '2025-09-20T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00056789
              customer_id: CUS-00056789
              email: marcus.wellington@techmail.net
              full_name: Marcus Wellington
              vip_tier: vip
              loyalty_program_status: silver
              lifetime_value: '3250.00'
              total_bookings_count: 12
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T12:00:00Z'
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-09-20T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00078901
              hotel_id: HTL-00078901
              hotel_name: Riverside Budget Inn
              location: Boston
              partner_tier: budget
              contact_name: Patricia Walsh
              contact_email: info@riversidebudgetinn.com
              contact_phone: +1-617-294-5832
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: false
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-10000001
              hotel_id: HTL-00078901
              room_type: family_room
              board_type: with_breakfast
              date: '2025-10-20T00:00:00Z'
              available_count: 2
              price_per_night: '140.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-10000002
              hotel_id: HTL-00078901
              room_type: family_room
              board_type: with_breakfast
              date: '2025-10-21T00:00:00Z'
              available_count: 2
              price_per_night: '140.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-10000003
              hotel_id: HTL-00078901
              room_type: family_room
              board_type: with_breakfast
              date: '2025-10-22T00:00:00Z'
              available_count: 2
              price_per_night: '140.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-10000004
              hotel_id: HTL-00078901
              room_type: family_room
              board_type: with_breakfast
              date: '2025-10-23T00:00:00Z'
              available_count: 2
              price_per_night: '140.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-10000005
              hotel_id: HTL-00078901
              room_type: family_room
              board_type: without_breakfast
              date: '2025-10-20T00:00:00Z'
              available_count: 2
              price_per_night: '125.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-10000006
              hotel_id: HTL-00078901
              room_type: family_room
              board_type: without_breakfast
              date: '2025-10-21T00:00:00Z'
              available_count: 2
              price_per_night: '125.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-10000007
              hotel_id: HTL-00078901
              room_type: family_room
              board_type: without_breakfast
              date: '2025-10-22T00:00:00Z'
              available_count: 2
              price_per_night: '125.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-10000008
              hotel_id: HTL-00078901
              room_type: family_room
              board_type: without_breakfast
              date: '2025-10-23T00:00:00Z'
              available_count: 2
              price_per_night: '125.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Wellington
              email: marcus.wellington@techmail.net
              role: end-user
              organization_id: ORG-10000002
              phone: +1-617-482-9371
              verified: true
              active: true
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
          zendesk_tickets:
            - id: TCK-05466889
              subject: Billing inquiry - BKG-36690967
              description: Customer inquiry about billing charges on booking
              status: open
              priority: normal
              type: question
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: ORG-10000002
              tags:
                - billing
                - inquiry
              created_at: '2025-09-30T13:00:00Z'
              updated_at: '2025-09-30T13:00:00Z'
              due_at: null
              booking_reference: BKG-36690967
              hotel_id: HTL-00078901
              check_in_date: '2025-10-15T14:00:00Z'
              booking_value: 560.0
              request_type_detail: billing-inquiry
              corporate_account_id: null
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          payment_api_transactions:
            - id: TXN-10000001
              transaction_id: TXN-10000001
              booking_reference: BKG-36690967
              customer_id: CUS-00056789
              amount: '560.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7823
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-15T12:00:00Z'
              updated_at: '2025-09-15T12:00:00Z'
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
                booking_reference: BKG-36690967
            - tool: crm_api_check_vip_status
              parameters:
                customer_id: CUS-00056789
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00078901
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00078901
                check_in_date: '2025-10-20T14:00:00Z'
                check_out_date: '2025-10-24T11:00:00Z'
                room_type: family_room
                board_type: with_breakfast
                adults_count: 3
                children_count: 2
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.wellington@techmail.net'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-36690967'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Date modification request - BKG-36690967
                  description: Customer requesting to change check-in date from 2025-10-15 to 2025-10-20, shifting entire stay to Oct 20-24. Booking at budget partner hotel, VIP tier customer (vip). Second modification - $15 surcharge applies. Original value $560, no price difference expected.
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                  booking_reference: BKG-36690967
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-36690967
                check_in_date: '2025-10-20T14:00:00Z'
                check_out_date: '2025-10-24T11:00:00Z'
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-36690967
                charge_amount: '15.00'
                reason: modification_fee
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                  booking_reference: BKG-36690967
                  hotel_id: HTL-00078901
                  check_in_date: '2025-10-20T14:00:00Z'
                  booking_value: 560.0
                  request_type_detail: modify-dates
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_bmd_019(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I have a booking coming up and I need to add pet accommodation to my reservation. My name is Rachel Henderson, email is rachel.henderson@outlook.com, and my booking reference is BKG-56272980. I'll be bringing my dog with me. Can you help with this?
    user_context: |
        You are Rachel Henderson, a customer contacting StayBridge support to request pet accommodation for your upcoming hotel booking. You want to bring your dog on your trip and need this noted on your reservation.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent confirms your pet accommodation has been added and mentions potential hotel fees at check-in, acknowledge and thank them.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-56272980
              booking_reference: BKG-56272980
              customer_id: CUS-00000006
              hotel_id: HTL-00000006
              check_in_date: '2025-10-03T14:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              booking_value: '350.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: rachel.henderson@outlook.com
              full_name: Rachel Henderson
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '650.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T12:00:00Z'
              created_at: '2025-06-01T10:00:00Z'
              updated_at: '2025-08-15T12:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00000006
              hotel_name: Harbor View Hotel
              location: Boston
              partner_tier: standard
              contact_name: Jennifer Walsh
              contact_email: contact@harborviewhotel.com
              contact_phone: +1-617-283-4506
              escalation_contact: null
              amenities:
                - wifi
                - restaurant
                - parking
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions:
            - id: TXN-00000008
              transaction_id: TXN-00000008
              booking_reference: BKG-56272980
              customer_id: CUS-00000006
              amount: '350.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7823
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          zendesk_tickets:
            - id: TCK-69901627
              subject: Pet accommodation request - BKG-56272980
              description: Customer requesting pet accommodation for their upcoming stay
              status: solved
              priority: normal
              type: task
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: null
              tags:
                - b2c-customer
                - special-request
              created_at: '2025-09-28T10:00:00Z'
              updated_at: '2025-09-28T15:00:00Z'
              due_at: null
              booking_reference: BKG-56272980
              hotel_id: HTL-00000006
              check_in_date: '2025-10-03T14:00:00Z'
              booking_value: 350.0
              request_type_detail: add-special-request
              corporate_account_id: null
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Rachel Henderson
              email: rachel.henderson@outlook.com
              role: end-user
              organization_id: null
              phone: +1-617-482-7319
              verified: true
              active: true
              created_at: '2025-06-01T10:00:00Z'
              updated_at: '2025-06-01T10:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-56272980
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00000006
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'rachel.henderson@outlook.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-56272980'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-69901627
                item:
                  status: open
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-56272980
                special_requests:
                  - pet accommodation
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-69901627
                item:
                  status: solved
                  priority: normal
                  type: task
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - repeat-issue
                  booking_reference: BKG-56272980
                  hotel_id: HTL-00000006
                  check_in_date: '2025-10-03T14:00:00Z'
                  booking_value: 350.0
                  request_type_detail: add-special-request
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


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
              check_in_date: '2025-10-05T14:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
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
              created_at: '2025-09-10T14:30:00Z'
              updated_at: '2025-09-10T14:30:00Z'
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
              last_booking_date: '2025-09-10T14:30:00Z'
              created_at: '2022-06-15T09:00:00Z'
              updated_at: '2025-09-10T14:30:00Z'
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
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-20465370
              hotel_id: HTL-20465375
              room_type: suite
              board_type: without_breakfast
              date: '2025-10-05T00:00:00Z'
              available_count: 3
              price_per_night: '200.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-20465371
              hotel_id: HTL-20465375
              room_type: suite
              board_type: without_breakfast
              date: '2025-10-06T00:00:00Z'
              available_count: 3
              price_per_night: '200.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-20465372
              hotel_id: HTL-20465375
              room_type: suite
              board_type: with_breakfast
              date: '2025-10-05T00:00:00Z'
              available_count: 3
              price_per_night: '220.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-20465373
              hotel_id: HTL-20465375
              room_type: suite
              board_type: with_breakfast
              date: '2025-10-06T00:00:00Z'
              available_count: 3
              price_per_night: '220.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-20465374
              hotel_id: HTL-20465375
              room_type: suite
              board_type: half_board
              date: '2025-10-05T00:00:00Z'
              available_count: 3
              price_per_night: '235.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-20465375
              hotel_id: HTL-20465375
              room_type: suite
              board_type: half_board
              date: '2025-10-06T00:00:00Z'
              available_count: 3
              price_per_night: '235.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-20465376
              hotel_id: HTL-20465375
              room_type: suite
              board_type: full_board
              date: '2025-10-05T00:00:00Z'
              available_count: 2
              price_per_night: '242.50'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-20465377
              hotel_id: HTL-20465375
              room_type: suite
              board_type: full_board
              date: '2025-10-06T00:00:00Z'
              available_count: 2
              price_per_night: '242.50'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Victoria Chen
              email: victoria.chen@outlook.com
              role: end-user
              organization_id: null
              phone: +1-617-483-2967
              verified: true
              active: true
              created_at: '2022-06-15T09:00:00Z'
              updated_at: '2022-06-15T09:00:00Z'
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
              created_at: '2025-09-10T14:30:00Z'
              updated_at: '2025-09-10T14:30:00Z'
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
                check_in_date: '2025-10-05T14:00:00Z'
                check_out_date: '2025-10-07T11:00:00Z'
                room_type: suite
                board_type: without_breakfast
                adults_count: 2
                children_count: 1
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'victoria.chen@outlook.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-20465375'
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
                  description: 'Customer requests to change board type from full_board to without_breakfast. Booking at budget tier hotel for 2025-10-05 check-in. Customer is platinum VIP - modification fee waived. RESOLUTION: Board type successfully modified from full_board to without_breakfast. Original booking value: $485.00. New booking value: $400.00. Price difference refund of $85.00 processed (TXN-00000008). No modification fee charged due to platinum tier exception. Note: Customer qualifies for vip-customer tag.'
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                  booking_reference: BKG-20465375
                  hotel_id: HTL-20465375
                  check_in_date: '2025-10-05T14:00:00Z'
                  booking_value: 400.0
                  request_type_detail: modify-board-type
                  resolution_action: modification-completed
                  refund_amount: 85.0
    """

    validate_database(x)


def test_bmd_021(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to add wheelchair accessibility to my upcoming booking. Can you help?
    user_context: |
        You are Michaela Reynolds, a customer contacting StayBridge support to add wheelchair accessibility as a special request to your upcoming hotel booking.

        Only if you are asked about your booking reference or confirmation number — tell the agent it is BKG-56464170
        Only if you are asked about your name — tell the agent your name is Michaela Reynolds
        Only if you are asked about your email address — tell the agent it is michaela.reynolds@outlook.com

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-56464170
              customer_id: CUS-00000006
              hotel_id: HTL-00056464
              check_in_date: '2025-10-06T14:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '395.00'
              room_type: accessible_room
              board_type: with_breakfast
              adults_count: 1
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: michaela.reynolds@outlook.com
              full_name: Michaela Reynolds
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '890.50'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-03-10T09:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00056464
              hotel_name: Riverside Grand Hotel
              location: Chicago
              partner_tier: premium
              contact_name: Jennifer Blake
              contact_email: contact@riversidegrand.com
              contact_phone: +1-312-847-9253
              escalation_contact: manager@riversidegrand.com
              amenities:
                - pool
                - gym
                - restaurant
                - wifi
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions: []
          zendesk_tickets:
            - id: TCK-80531003
              subject: Booking inquiry for accessible room
              description: Customer inquired about accessible room features and amenities
              status: solved
              priority: normal
              type: question
              requester_id: USR-10000007
              assignee_id: USR-10000002
              organization_id: null
              tags:
                - inquiry
                - accessibility
              created_at: '2025-09-19T10:00:00Z'
              updated_at: '2025-09-19T14:00:00Z'
              due_at: null
              booking_reference: BKG-56464170
              hotel_id: HTL-00056464
              check_in_date: '2025-10-06T14:00:00Z'
              booking_value: 395.0
              request_type_detail: other
              corporate_account_id: null
              group_booking_id: null
              resolution_action: information-provided
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Michaela Reynolds
              email: michaela.reynolds@outlook.com
              role: end-user
              organization_id: null
              phone: +1-312-694-8273
              verified: true
              active: true
              created_at: '2025-03-10T09:00:00Z'
              updated_at: '2025-03-10T09:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-56464170
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00056464
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'michaela.reynolds@outlook.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-56464170'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Wheelchair accessibility request - BKG-56464170
                  description: 'Customer requests wheelchair accessibility accommodation to be added to booking BKG-56464170. Check-in: 2025-10-06. Hotel has accessible rooms available. Request is ≥24h in advance. No fee applies for accessibility accommodations.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-56464170
                special_requests:
                  - wheelchair accessibility
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  booking_reference: BKG-56464170
                  hotel_id: HTL-00056464
                  check_in_date: '2025-10-06T14:00:00Z'
                  booking_value: 395.0
                  request_type_detail: add-special-request
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_bmd_022(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to upgrade my room for my upcoming booking.
    user_context: |
        You are Marcus Wellington, a customer contacting StayBridge support to request a room upgrade for your booking.

        Only if you are asked about your booking reference or confirmation number — tell the agent it is BKG-30923271.
        Only if you are asked about your current room type — you currently have a deluxe room.
        Only if you are asked about what room type you want or your desired upgrade — you would like to upgrade to a suite.
        Only if you are asked about your name — your name is Marcus Wellington.
        Only if you are asked about your email address — your email is marcus.wellington@hotmail.com.
        Only if you are asked about previous contact or history with this issue — you made a similar request a few days ago but didn't get a resolution and haven't heard back yet.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent mentions fees or charges for the modification, accept and confirm you are okay to proceed.
    init:
      external_booking_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-93745299
              subject: Room type modification request
              description: Customer requesting change from deluxe_room to suite for booking BKG-30923271
              status: pending
              priority: normal
              type: task
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: ORG-10000001
              tags:
                - booking-modification
                - room-upgrade
              created_at: '2025-09-27T10:30:00Z'
              updated_at: '2025-09-27T10:30:00Z'
              due_at: null
              booking_reference: BKG-30923271
              hotel_id: HTL-74829316
              check_in_date: '2025-10-08T14:00:00Z'
              booking_value: 615.0
              request_type_detail: modify-room-type
              corporate_account_id: null
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Marcus Wellington
              email: marcus.wellington@hotmail.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-773-482-9156
              verified: true
              active: true
              created_at: '2023-08-10T10:00:00Z'
              updated_at: '2023-08-10T10:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-30923271
              booking_reference: BKG-30923271
              customer_id: CUS-38471925
              hotel_id: HTL-74829316
              check_in_date: '2025-10-08T14:00:00Z'
              check_out_date: '2025-10-11T11:00:00Z'
              booking_value: '615.00'
              room_type: deluxe_room
              board_type: half_board
              adults_count: 2
              children_count: 2
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history:
                - '2025-09-20T09:15:00Z: board_type: with_breakfast -> half_board'
              special_requests: []
              created_at: '2025-09-15T08:30:00Z'
              updated_at: '2025-09-20T09:15:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000010
              hotel_id: HTL-74829316
              room_type: suite
              board_type: half_board
              date: '2025-10-08T00:00:00Z'
              available_count: 2
              price_per_night: '240.00'
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
            - id: INV-00000011
              hotel_id: HTL-74829316
              room_type: suite
              board_type: half_board
              date: '2025-10-09T00:00:00Z'
              available_count: 2
              price_per_night: '240.00'
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
            - id: INV-00000012
              hotel_id: HTL-74829316
              room_type: suite
              board_type: half_board
              date: '2025-10-10T00:00:00Z'
              available_count: 2
              price_per_night: '240.00'
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
            - id: INV-00000013
              hotel_id: HTL-74829316
              room_type: suite
              board_type: without_breakfast
              date: '2025-10-08T00:00:00Z'
              available_count: 2
              price_per_night: '210.00'
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
            - id: INV-00000014
              hotel_id: HTL-74829316
              room_type: suite
              board_type: with_breakfast
              date: '2025-10-08T00:00:00Z'
              available_count: 2
              price_per_night: '225.00'
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
            - id: INV-00000015
              hotel_id: HTL-74829316
              room_type: suite
              board_type: full_board
              date: '2025-10-08T00:00:00Z'
              available_count: 2
              price_per_night: '260.00'
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
          booking_api_group_bookings: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-38471925
              customer_id: CUS-38471925
              email: marcus.wellington@hotmail.com
              full_name: Marcus Wellington
              vip_tier: vip
              loyalty_program_status: gold
              lifetime_value: '8750.30'
              total_bookings_count: 15
              preferences:
                - quiet room
                - king bed
              special_notes:
                - prefers early check-in when available
              complaint_count: 0
              last_booking_date: '2025-09-15T08:30:00Z'
              created_at: '2023-08-10T10:00:00Z'
              updated_at: '2025-09-15T08:30:00Z'
          hotel_partner_api_hotels:
            - id: HTL-74829316
              hotel_id: HTL-74829316
              hotel_name: Riverside Garden Hotel
              location: Chicago
              partner_tier: standard
              contact_name: Patricia Morrison
              contact_email: reservations@riversidegarden.com
              contact_phone: +1-312-547-8293
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
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
                filter: booking_reference eq 'BKG-30923271'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-93745299
                item:
                  status: open
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-30923271
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-74829316
            - tool: crm_api_check_vip_status
              parameters:
                customer_id: CUS-38471925
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-74829316
                check_in_date: '2025-10-08T14:00:00Z'
                check_out_date: '2025-10-11T11:00:00Z'
                room_type: suite
                board_type: half_board
                adults_count: 2
                children_count: 2
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-30923271
                room_type: suite
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-30923271
                charge_amount: '120.00'
                reason: modification_fee_and_price_difference
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-38471925
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.wellington@hotmail.com'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-93745299
                item:
                  status: solved
                  priority: normal
                  type: task
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                    - repeat-issue
                  description: 'Room type modification request - BKG-30923271. Customer (VIP tier) requested change from deluxe_room to suite. Modification executed successfully. Time until check-in: 169 hours (≥7 days). Hotel tier: standard. Second modification (+$15 surcharge). Modification fee: $15. Price difference: $105 (suite upgrade). Total charged: $120 via TXN-00000008. New booking value: $720. Note: Customer has vip_tier=vip status.'
                  booking_reference: BKG-30923271
                  hotel_id: HTL-74829316
                  check_in_date: '2025-10-08T14:00:00Z'
                  booking_value: 720.0
                  request_type_detail: modify-room-type
                  resolution_action: modification-completed
                  refund_amount: 0.0
    """

    validate_database(x)


def test_bmd_023(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I have a booking coming up and I'd like to upgrade my room if possible.
    user_context: |
        You are Marcus Reynolds, a customer contacting StayBridge support to request a room upgrade for your upcoming booking.
        Only if you are asked about your name — tell the agent it is Marcus Reynolds.
        Only if you are asked about your email or email address — tell the agent it is marcus.reynolds@travelmail.net.
        Only if you are asked about your booking reference or confirmation number — tell the agent it is BKG-12419049.
        Only if you are asked about your current room type — tell the agent you currently have a standard room.
        Only if you are asked about what type of room you want to upgrade to or which room you prefer — tell the agent you would like a deluxe room.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent informs you that the deluxe room is not available, acknowledge the information politely and thank them for checking.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00084739
              booking_reference: BKG-12419049
              customer_id: CUS-74839216
              hotel_id: HTL-84739201
              check_in_date: '2025-10-04T14:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              booking_value: '330.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-74839216
              customer_id: CUS-74839216
              email: marcus.reynolds@travelmail.net
              full_name: Marcus Reynolds
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '892.50'
              total_bookings_count: 4
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-03-10T09:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Reynolds
              email: marcus.reynolds@travelmail.net
              role: end-user
              organization_id: null
              phone: +1-312-847-3928
              verified: true
              active: true
              created_at: '2025-03-10T09:00:00Z'
              updated_at: '2025-03-10T09:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-84739201
              hotel_id: HTL-84739201
              hotel_name: Riverfront Suites Chicago
              location: Chicago
              partner_tier: standard
              contact_name: Jennifer Walsh
              contact_email: manager@riverfrontsuites.com
              contact_phone: +1-312-892-4567
              escalation_contact: null
              amenities:
                - wifi
                - gym
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-84739001
              hotel_id: HTL-84739201
              room_type: standard_room
              board_type: without_breakfast
              date: '2025-10-04T00:00:00Z'
              available_count: 2
              price_per_night: '165.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: INV-84739002
              hotel_id: HTL-84739201
              room_type: standard_room
              board_type: without_breakfast
              date: '2025-10-05T00:00:00Z'
              available_count: 2
              price_per_night: '165.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          payment_api_transactions:
            - id: TXN-74839001
              transaction_id: TXN-74839001
              booking_reference: BKG-12419049
              customer_id: CUS-74839216
              amount: '330.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Mastercard ending in 7821
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
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
                booking_reference: BKG-12419049
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-84739201
                check_in_date: '2025-10-04T14:00:00Z'
                check_out_date: '2025-10-06T11:00:00Z'
                room_type: deluxe_room
                board_type: without_breakfast
                adults_count: 2
                children_count: 0
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-74839216
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.reynolds@travelmail.net'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-12419049'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Room type modification request - BKG-12419049
                  description: Customer requested room type upgrade from standard_room to deluxe_room for booking BKG-12419049 (check-in 2025-10-04). Verified booking status is confirmed. Checked availability for deluxe_room - not available for requested dates. Modification request denied due to unavailability per Section 4.1.2.
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-12419049
                  hotel_id: HTL-84739201
                  check_in_date: '2025-10-04T14:00:00Z'
                  booking_value: 330.0
                  request_type_detail: modify-room-type
                  resolution_action: policy-applied-no-action
                  refund_amount: 0
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
    """

    validate_database(x)


def test_bmd_024(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to change the check-in date for my booking BKG-66319314. My email is marcus.davies@outlook.com. Can you help me reschedule to a different date?
    user_context: |
        You are Marcus Davies, a customer who wants to change the check-in date for your booking. You may not fully recall or be aware that the booking was previously cancelled.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          zendesk_users:
            - id: USR-10000010
              name: Marcus Davies
              email: marcus.davies@outlook.com
              role: end-user
              organization_id: null
              phone: +1-617-842-3195
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          zendesk_tickets:
            - id: TCK-91905865
              subject: Cancellation confirmation - BKG-66319314
              description: Customer requested confirmation of booking cancellation for BKG-66319314
              status: solved
              priority: normal
              type: question
              requester_id: USR-10000010
              assignee_id: AG-83945
              organization_id: null
              tags:
                - cancellation
                - confirmation
              created_at: '2025-09-29T10:00:00Z'
              updated_at: '2025-09-29T16:00:00Z'
              due_at: null
              booking_reference: BKG-66319314
              hotel_id: HTL-00088245
              check_in_date: '2025-10-05T14:00:00Z'
              booking_value: 280.0
              request_type_detail: null
              corporate_account_id: null
              group_booking_id: null
              resolution_action: policy-applied-no-action
              refund_amount: null
              escalation_reason: null
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-66319314
              booking_reference: BKG-66319314
              customer_id: CUS-00000010
              hotel_id: HTL-00088245
              check_in_date: '2025-10-05T14:00:00Z'
              check_out_date: '2025-10-06T14:00:00Z'
              booking_value: '280.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 1
              children_count: 1
              booking_status: cancelled
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-28T12:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-00000010
              customer_id: CUS-00000010
              email: marcus.davies@outlook.com
              full_name: Marcus Davies
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '850.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-01-20T10:00:00Z'
              updated_at: '2025-09-28T12:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00088245
              hotel_id: HTL-00088245
              hotel_name: The Harrington Suites
              location: Boston
              partner_tier: premium
              contact_name: Jonathan Blackwell
              contact_email: manager@harringtonsuites.com
              contact_phone: +1-617-923-4501
              escalation_contact: director@harringtonsuites.com
              amenities:
                - wifi
                - gym
                - restaurant
                - business_center
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2024-06-01T10:00:00Z'
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.davies@outlook.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-66319314'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-66319314
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000010
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Date modification request - BKG-66319314
                  description: Customer requested to change check-in dates for booking BKG-66319314. Booking status is cancelled. Per policy Section 4.1.2, modifications are only available for bookings with status confirmed. Customer informed, no action taken on booking.
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000010
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                  booking_reference: BKG-66319314
                  hotel_id: HTL-00088245
                  check_in_date: '2025-10-05T14:00:00Z'
                  booking_value: 280.0
                  request_type_detail: modify-dates
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  resolution_action: policy-applied-no-action
                  refund_amount: 0
    """

    validate_database(x)


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
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
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
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
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
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
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
              created_at: '2025-09-15T10:05:00Z'
              updated_at: '2025-09-15T10:05:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Michael Harris
              email: michael.harris@proton.me
              role: end-user
              organization_id: null
              phone: +1-617-384-7129
              verified: true
              active: true
              created_at: '2025-09-01T00:00:00Z'
              updated_at: '2025-09-01T00:00:00Z'
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
                filter: booking_reference eq 'BKG-87769453'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'michael.harris@proton.me'
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
                  check_in_date: '2025-10-05T15:00:00Z'
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
    """

    validate_database(x)


def test_bpy_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Marcus Wellington and I had a payment issue with my booking BKG-50752735. The payment failed yesterday due to insufficient funds on my old card, but I've since updated my payment method to a new card. I'd like to retry the payment so my booking is fully confirmed. My email is marcus.wellington@lexmail.net.
    user_context: |
        You are Marcus Wellington, a VIP customer contacting support about a failed payment for your hotel booking. You want to retry the payment with your new card.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If asked for the last 4 digits of your new card, provide: 3847
        - If asked to confirm you want to update your payment method, confirm yes
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-50752735
              booking_reference: BKG-50752735
              customer_id: CUS-50752735
              hotel_id: HTL-12345678
              check_in_date: '2025-10-08T15:00:00Z'
              check_out_date: '2025-10-10T11:00:00Z'
              booking_value: '780.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-50752735
              customer_id: CUS-50752735
              email: marcus.wellington@lexmail.net
              full_name: Marcus Wellington
              vip_tier: vip
              loyalty_program_status: gold
              lifetime_value: '4500.00'
              total_bookings_count: 8
              preferences:
                - quiet room
                - high floor
              special_notes:
                - prefers morning check-in calls
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-03-10T09:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-12345678
              hotel_id: HTL-12345678
              hotel_name: The Langham Chicago
              location: Chicago
              partner_tier: premium
              contact_name: Victoria Ashworth
              contact_email: reservations@langhamchicago.com
              contact_phone: +1-312-923-7500
              escalation_contact: gm@langhamchicago.com
              amenities:
                - pool
                - spa
                - gym
                - restaurant
                - concierge
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2024-02-15T10:00:00Z'
              updated_at: '2024-02-15T10:00:00Z'
          payment_api_transactions:
            - id: TXN-45494808
              transaction_id: TXN-45494808
              booking_reference: BKG-50752735
              customer_id: CUS-50752735
              amount: '780.00'
              currency: USD
              transaction_type: charge
              payment_status: failed
              payment_method: Visa ending in 4829
              reason: insufficient_funds
              processing_time_estimate: null
              created_at: '2025-09-30T10:00:00Z'
              updated_at: '2025-09-30T10:00:00Z'
          zendesk_tickets:
            - id: TCK-31367837
              subject: Payment failure - BKG-50752735
              description: Customer reported payment failure for booking BKG-50752735. Transaction TXN-45494808 shows insufficient funds.
              status: pending
              priority: high
              type: incident
              requester_id: USR-50752735
              assignee_id: AG-83945
              organization_id: null
              tags:
                - b2c-customer
                - payment-issue
              created_at: '2025-09-30T14:30:00Z'
              updated_at: '2025-09-30T16:00:00Z'
              due_at: null
              booking_reference: BKG-50752735
              hotel_id: HTL-12345678
              check_in_date: '2025-10-08T15:00:00Z'
              booking_value: 780.0
              request_type_detail: billing-inquiry
              corporate_account_id: null
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-50752735
              name: Marcus Wellington
              email: marcus.wellington@lexmail.net
              role: end-user
              organization_id: null
              phone: +1-617-483-7291
              verified: true
              active: true
              created_at: '2024-03-10T09:00:00Z'
              updated_at: '2024-03-10T09:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-50752735
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-50752735
            - tool: payment_api_check_payment_status
              parameters:
                booking_reference: BKG-50752735
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.wellington@lexmail.net'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-50752735'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-31367837
                item:
                  status: open
            - tool: payment_api_update_payment_method
              parameters:
                customer_id: CUS-50752735
                new_payment_method: tok_card_ending_3847
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-31367837
                item:
                  status: solved
                  type: incident
                  priority: high
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                  description: 'Customer reported payment failure for booking BKG-50752735. Payment status verified as failed (TXN-45494808, reason: insufficient_funds). Customer is VIP tier. New payment method (card ending 3847) successfully registered in system. Customer informed to retry payment through checkout flow. Resolution: Payment method updated, information provided.'
                  booking_reference: BKG-50752735
                  hotel_id: HTL-12345678
                  check_in_date: '2025-10-08T15:00:00Z'
                  booking_value: 780.0
                  request_type_detail: billing-inquiry
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_bpy_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm really frustrated here. I have booking BKG-77014363 and I've been trying to complete my payment for the past hour but it keeps failing! I've tried 3 times now and each time it just fails. My check-in is on October 3rd and I'm worried I'm going to lose my reservation. Can someone please explain why my payments keep getting declined? My name is Marcus Wellington, email is marcus.wellington@outlook.com.
    user_context: |
        You are Marcus Wellington, a frustrated customer who has tried to pay for your hotel booking 3 times in the past hour but all attempts failed. You're worried about your upcoming check-in on October 3rd.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If the agent asks whether you'd like to try a different payment method or provide an alternative card, agree and say you want to use your other card ending in 4521.
        - Maintain a frustrated but cooperative tone throughout the conversation.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-77014363
              booking_reference: BKG-77014363
              customer_id: CUS-77014363
              hotel_id: HTL-55823167
              check_in_date: '2025-10-03T15:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              booking_value: '245.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-20T10:00:00Z'
              updated_at: '2025-09-20T10:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-77014363
              customer_id: CUS-77014363
              email: marcus.wellington@outlook.com
              full_name: Marcus Wellington
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '890.50'
              total_bookings_count: 3
              preferences:
                - quiet room
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-20T14:00:00Z'
              created_at: '2025-03-15T10:00:00Z'
              updated_at: '2025-09-20T12:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-55823167
              hotel_id: HTL-55823167
              hotel_name: Comfort Stay Express
              location: Boston
              partner_tier: budget
              contact_name: Helen Martinez
              contact_email: frontdesk@comfortstayexpress.com
              contact_phone: +1-617-294-7531
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: false
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
          payment_api_transactions:
            - id: TXN-13518233
              transaction_id: TXN-13518233
              booking_reference: BKG-77014363
              customer_id: CUS-77014363
              amount: '245.00'
              currency: USD
              transaction_type: charge
              payment_status: failed
              payment_method: Visa ending in 7832
              reason: null
              processing_time_estimate: null
              created_at: '2025-10-01T12:30:00Z'
              updated_at: '2025-10-01T12:30:00Z'
            - id: TXN-85574443
              transaction_id: TXN-85574443
              booking_reference: BKG-77014363
              customer_id: CUS-77014363
              amount: '245.00'
              currency: USD
              transaction_type: charge
              payment_status: failed
              payment_method: Visa ending in 7832
              reason: null
              processing_time_estimate: null
              created_at: '2025-10-01T12:15:00Z'
              updated_at: '2025-10-01T12:15:00Z'
            - id: TXN-49578856
              transaction_id: TXN-49578856
              booking_reference: BKG-77014363
              customer_id: CUS-77014363
              amount: '245.00'
              currency: USD
              transaction_type: charge
              payment_status: failed
              payment_method: Visa ending in 7832
              reason: null
              processing_time_estimate: null
              created_at: '2025-10-01T12:00:00Z'
              updated_at: '2025-10-01T12:00:00Z'
          zendesk_tickets: []
          zendesk_users:
            - id: USR-77014363
              name: Marcus Wellington
              email: marcus.wellington@outlook.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-617-438-9271
              verified: true
              active: true
              created_at: '2025-03-15T10:00:00Z'
              updated_at: '2025-03-15T10:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-77014363
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-77014363
            - tool: payment_api_check_payment_status
              parameters:
                booking_reference: BKG-77014363
            - tool: payment_api_get_transaction_history
              parameters:
                booking_reference: BKG-77014363
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-77014363'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.wellington@outlook.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Payment failure inquiry - BKG-77014363
                  description: 'Customer reporting multiple failed payment attempts for booking BKG-77014363. Three payment transactions (TXN-49578856, TXN-85574443, TXN-13518233) all show payment_status: failed. Customer is frustrated and asking why payments keep failing. Check-in scheduled for 2025-10-03 at budget tier hotel. Booking value: $245.00.'
                  status: open
                  priority: high
                  type: incident
                  requester_id: USR-77014363
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-77014363
                  hotel_id: HTL-55823167
                  request_type_detail: billing-inquiry
            - tool: payment_api_update_payment_method
              parameters:
                customer_id: CUS-77014363
                new_payment_method: tok_card_ending_4521
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  description: 'Customer reporting multiple failed payment attempts for booking BKG-77014363. Three payment transactions (TXN-49578856, TXN-85574443, TXN-13518233) all show payment_status: failed. Customer is frustrated and asking why payments keep failing. Check-in scheduled for 2025-10-03 at budget tier hotel. Booking value: $245.00. Resolution: Updated payment method to card ending in 4521. Customer advised to retry payment through checkout flow.'
                  resolution_action: information-provided
                  refund_amount: 0
                  booking_value: 245.0
                  check_in_date: '2025-10-03T15:00:00Z'
    """

    validate_database(x)


def test_bpy_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I just received my credit card statement and I was charged $715 for my recent hotel stay, but my booking confirmation clearly shows $650. That's a $65 difference I can't explain. My name is Rachel Martinez, email rachel.martinez@outlook.com, and my booking reference is BKG-90229413. I checked out on September 27th from Harbor View Inn. Can you help me understand why I was overcharged?
    user_context: |
        You are Rachel Martinez, a VIP customer contacting StayBridge support about a billing discrepancy. You stayed at Harbor View Inn and were charged $715 on your credit card instead of the $650 booking value. You want an explanation for the $65 overcharge and expect it to be corrected.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: rachel.martinez@outlook.com
              full_name: Rachel Martinez
              vip_tier: vip
              loyalty_program_status: gold-member
              lifetime_value: '8750.50'
              total_bookings_count: 14
              preferences:
                - quiet room
                - high floor
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-27T11:00:00Z'
              created_at: '2024-08-15T09:00:00Z'
              updated_at: '2025-09-27T11:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-90229413
              customer_id: CUS-00000006
              hotel_id: HTL-00012350
              check_in_date: '2025-09-24T15:00:00Z'
              check_out_date: '2025-09-27T11:00:00Z'
              booking_value: '650.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-27T11:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00012350
              hotel_name: Harbor View Inn
              location: San Francisco
              partner_tier: standard
              contact_name: Jennifer Walsh
              contact_email: info@harborviewinn.com
              contact_phone: +1-415-892-3744
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - business_center
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions:
            - id: TXN-18699938
              transaction_id: TXN-18699938
              booking_reference: BKG-90229413
              customer_id: CUS-00000006
              amount: '715.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7812
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Rachel Martinez
              email: rachel.martinez@outlook.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-415-736-2891
              verified: true
              active: true
              created_at: '2024-08-15T09:00:00Z'
              updated_at: '2024-08-15T09:00:00Z'
          zendesk_tickets:
            - id: TCK-67749649
              subject: Pre-stay room preference inquiry
              description: Customer inquired about room preferences before their upcoming stay at Harbor View Inn
              status: solved
              priority: low
              type: question
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: ORG-10000002
              tags:
                - pre-stay
                - room-preference
              created_at: '2025-09-23T10:00:00Z'
              updated_at: '2025-09-23T14:00:00Z'
              due_at: null
              booking_reference: BKG-90229413
              hotel_id: HTL-00012350
              check_in_date: null
              booking_value: 650.0
              request_type_detail: other
              corporate_account_id: null
              group_booking_id: null
              resolution_action: information-provided
              refund_amount: null
              escalation_reason: null
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: crm_api_get_customer_profile
              parameters:
                email: rachel.martinez@outlook.com
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-90229413
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00012350
            - tool: payment_api_get_transaction_history
              parameters:
                booking_reference: BKG-90229413
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'rachel.martinez@outlook.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-90229413'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Billing overcharge inquiry - BKG-90229413
                  description: 'Customer reports credit card charged $715 instead of booking value $650 for booking BKG-90229413. Transaction TXN-18699938 shows $715 charge. Booking has no modification history. Overcharge amount: $65. Checkout date: 2025-09-27. Days since checkout: 4 days.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-90229413
                refund_amount: '65.00'
                reason: billing_overcharge_correction
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  tags:
                    - b2c-customer
                    - vip-customer
                  booking_reference: BKG-90229413
                  hotel_id: HTL-00012350
                  booking_value: 650.0
                  request_type_detail: billing-inquiry
                  resolution_action: refund-partial
                  refund_amount: 65.0
                  escalation_reason: system-error
    """

    validate_database(x)


def test_bpy_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need a receipt for my upcoming hotel booking. My name is Thomas Reynolds and my email is thomas.reynolds@outlook.com. The booking reference is BKG-38156149. I need the receipt for expense reimbursement at my company. Can you help me with that?
    user_context: |
        You are Thomas Reynolds, a customer contacting StayBridge support to request a receipt for your hotel booking. You need this receipt for expense reimbursement purposes at your workplace.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-38156149
              booking_reference: BKG-38156149
              customer_id: CUS-29384756
              hotel_id: HTL-47829163
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              room_type: deluxe_room
              board_type: with_breakfast
              booking_status: confirmed
              booking_value: '485.00'
              adults_count: 2
              children_count: 0
              special_requests: []
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-29384756
              customer_id: CUS-29384756
              email: thomas.reynolds@outlook.com
              full_name: Thomas Reynolds
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '2450.00'
              total_bookings_count: 5
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-06-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          zendesk_users:
            - id: USR-29384756
              name: Thomas Reynolds
              email: thomas.reynolds@outlook.com
              role: end-user
              organization_id: null
              phone: +1-646-892-3471
              verified: true
              active: true
              created_at: '2024-06-15T10:00:00Z'
              updated_at: '2024-06-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-47829163
              hotel_id: HTL-47829163
              hotel_name: The Lakefront Grand Hotel
              location: Chicago
              partner_tier: premium
              contact_name: Victoria Harrington
              contact_email: manager@lakefrontgrand.com
              contact_phone: +1-312-847-5921
              escalation_contact: director@lakefrontgrand.com
              amenities:
                - wifi
                - gym
                - restaurant
                - business_center
                - spa
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2024-03-01T10:00:00Z'
              updated_at: '2024-03-01T10:00:00Z'
          payment_api_transactions:
            - id: TXN-47829163
              transaction_id: TXN-47829163
              booking_reference: BKG-38156149
              customer_id: CUS-29384756
              amount: '485.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7842
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-15T10:05:00Z'
              updated_at: '2025-09-15T10:05:00Z'
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
                booking_reference: BKG-38156149
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-29384756
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'thomas.reynolds@outlook.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-38156149'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Receipt request - BKG-38156149
                  description: Customer requesting receipt for booking BKG-38156149 for expense reimbursement purposes.
                  status: open
                  priority: low
                  type: question
                  requester_id: USR-29384756
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-38156149
                  hotel_id: HTL-47829163
                  booking_value: 485.0
                  request_type_detail: billing-inquiry
            - tool: payment_api_generate_invoice
              parameters:
                booking_reference: BKG-38156149
                invoice_type: receipt
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_bpy_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm following up on a receipt request I made a few days ago. My name is Marcus Taylor, email marcus.taylor@outlook.com. I need a detailed receipt for my booking BKG-78403690 that shows the nightly rates and any additional charges - my company requires this for my expense report. I stayed September 20-23 and the total was $560. Can you help me get this sorted?
    user_context: |
        You are Marcus Taylor, a customer who stayed at a hotel recently and needs a receipt for your company expense report. You previously contacted support about this a few days ago but haven't received the receipt yet.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Once you receive the receipt link and confirmation, thank the agent and end the conversation.
    init:
      external_booking_v1:
        data_patch:
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: marcus.taylor@outlook.com
              full_name: Marcus Taylor
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '560.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-20T15:00:00Z'
              created_at: '2025-08-10T14:30:00Z'
              updated_at: '2025-09-23T11:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-78403690
              customer_id: CUS-00000006
              hotel_id: HTL-00012346
              check_in_date: '2025-09-20T15:00:00Z'
              check_out_date: '2025-09-23T11:00:00Z'
              booking_value: '560.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-05T09:15:00Z'
              updated_at: '2025-09-23T11:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Taylor
              email: marcus.taylor@outlook.com
              role: end-user
              organization_id: null
              phone: +1-617-483-2190
              verified: true
              active: true
              created_at: '2025-08-10T14:30:00Z'
              updated_at: '2025-08-10T14:30:00Z'
          zendesk_tickets:
            - id: TCK-03432445
              subject: Receipt request for booking BKG-78403690
              description: Customer needs detailed receipt showing nightly rates and charges for company expense report
              status: pending
              priority: low
              type: question
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: null
              tags:
                - receipt-request
              created_at: '2025-09-27T13:00:00Z'
              updated_at: '2025-09-27T14:15:00Z'
              due_at: null
              booking_reference: BKG-78403690
              hotel_id: HTL-00012346
              check_in_date: null
              booking_value: 560.0
              request_type_detail: billing-inquiry
              corporate_account_id: null
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          payment_api_transactions:
            - id: TXN-00000008
              transaction_id: TXN-00000008
              booking_reference: BKG-78403690
              customer_id: CUS-00000006
              amount: '560.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7823
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-05T09:20:00Z'
              updated_at: '2025-09-05T09:20:00Z'
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
            - tool: crm_api_get_customer_profile
              parameters:
                email: marcus.taylor@outlook.com
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-78403690
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.taylor@outlook.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-78403690'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-03432445
                item:
                  status: open
            - tool: payment_api_generate_invoice
              parameters:
                booking_reference: BKG-78403690
                invoice_type: receipt
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-03432445
                item:
                  status: solved
                  priority: low
                  type: question
                  tags:
                    - b2c-customer
                  booking_reference: BKG-78403690
                  hotel_id: HTL-00012346
                  booking_value: 560.0
                  request_type_detail: billing-inquiry
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_bpy_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I recently stayed at Harbor View Inn and I have a question about my bill. My booking reference is BKG-10762268 and my email is victoria.chen@globalmail.net. I was charged $375 for my stay, which I expected, but I also see a separate $15 charge labeled as a 'service fee' on my card. I don't understand why I was charged this service fee - can you please explain what it's for? I didn't cancel anything.
    user_context: |
        You are Victoria Chen, a platinum member customer who recently completed a stay at Harbor View Inn. You are confused about a $15 service fee that appeared as a separate charge on your credit card. You did NOT cancel your booking - you completed your stay normally. You want to understand why this fee was charged.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent offers a refund for the service fee, accept it gratefully.
        - Confirm that you did not cancel your booking if asked - you completed your stay as planned.
    init:
      external_booking_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-64160529
              subject: Billing question about room rate charges
              description: Customer had questions about the nightly rate breakdown on their invoice
              status: solved
              priority: normal
              type: question
              requester_id: USR-10762268
              assignee_id: AG-83945
              organization_id: null
              tags:
                - b2c-customer
                - billing
              created_at: '2025-09-29T10:00:00Z'
              updated_at: '2025-09-29T15:00:00Z'
              due_at: null
              booking_reference: BKG-10762268
              hotel_id: HTL-10762268
              check_in_date: '2025-09-28T15:00:00Z'
              booking_value: 375.0
              request_type_detail: billing-inquiry
              corporate_account_id: null
              group_booking_id: null
              resolution_action: information-provided
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-10762268
              name: Victoria Chen
              email: victoria.chen@globalmail.net
              role: end-user
              organization_id: null
              phone: +1-415-982-7341
              verified: true
              active: true
              created_at: '2024-08-15T09:00:00Z'
              updated_at: '2024-08-15T09:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-10762268
              booking_reference: BKG-10762268
              customer_id: CUS-10762268
              hotel_id: HTL-10762268
              check_in_date: '2025-09-28T15:00:00Z'
              check_out_date: '2025-09-30T11:00:00Z'
              booking_value: '375.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-30T11:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-10762268
              customer_id: CUS-10762268
              email: victoria.chen@globalmail.net
              full_name: Victoria Chen
              vip_tier: platinum
              loyalty_program_status: platinum-elite
              lifetime_value: '35892.75'
              total_bookings_count: 48
              preferences:
                - quiet room
                - high floor
              special_notes:
                - prefers email communication
              complaint_count: 1
              last_booking_date: '2025-09-30T11:00:00Z'
              created_at: '2022-03-15T10:00:00Z'
              updated_at: '2025-09-30T11:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-10762268
              hotel_id: HTL-10762268
              hotel_name: Harbor View Inn
              location: Seattle
              partner_tier: budget
              contact_name: Kevin Mitchell
              contact_email: front.desk@harborviewinn.com
              contact_phone: +1-206-847-3925
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2024-05-01T10:00:00Z'
              updated_at: '2024-05-01T10:00:00Z'
          payment_api_transactions:
            - id: TXN-07159696
              transaction_id: TXN-07159696
              booking_reference: BKG-10762268
              customer_id: CUS-10762268
              amount: '15.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7829
              reason: service_fee
              processing_time_estimate: null
              created_at: '2025-09-28T15:00:00Z'
              updated_at: '2025-09-28T15:00:00Z'
            - id: TXN-38851606
              transaction_id: TXN-38851606
              booking_reference: BKG-10762268
              customer_id: CUS-10762268
              amount: '375.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7829
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-10762268'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'victoria.chen@globalmail.net'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Billing inquiry - service fee charge - BKG-10762268
                  description: Customer questioning $15 service fee charge (TXN-07159696) separate from $375 booking payment. Investigating charge validity.
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10762268
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                  booking_reference: BKG-10762268
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-10762268
            - tool: payment_api_get_transaction_history
              parameters:
                booking_reference: BKG-10762268
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-10762268
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-10762268
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-10762268
                refund_amount: '15.00'
                reason: billing_error_service_fee_non_cancelled_booking
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  description: 'Customer questioned $15 service fee charge (TXN-07159696) on booking BKG-10762268. Booking status was checked_out (not cancelled). Per Section 4.2.1, service fees only apply to cancellation refunds. This was a billing error - service fee charged on non-cancelled booking. Processed $15 refund. Transaction ID: TXN-00000010.'
                  tags:
                    - b2c-customer
                    - vip-customer
                  booking_reference: BKG-10762268
                  hotel_id: HTL-10762268
                  booking_value: 375.0
                  request_type_detail: billing-inquiry
                  resolution_action: refund-partial
                  refund_amount: 15.0
                  escalation_reason: system-error
    """

    validate_database(x)


def test_cbi_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to get a corporate invoice for my recent stay. Thanks!
    user_context: |
        You are James Reynolds, an employee at TechCorp Inc., contacting support to request a corporate invoice for a completed business trip booking. You need the invoice for expense processing/reimbursement purposes.

        Only if you are asked about your name — your name is James Reynolds.
        Only if you are asked about your email address — your email is james.reynolds@techcorp.com.
        Only if you are asked about your company or organization — you are with TechCorp Inc.
        Only if you are asked about the booking reference or confirmation number — the booking reference is BKG-68164535.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-68164535
              customer_id: CUS-38471293
              hotel_id: HTL-49273618
              check_in_date: '2025-09-25T15:00:00Z'
              check_out_date: '2025-09-28T11:00:00Z'
              booking_value: '1890.00'
              room_type: executive_suite
              board_type: with_breakfast
              adults_count: 1
              children_count: 0
              booking_status: checked_out
              corporate_account_id: CRP-75161369
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-28T11:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts:
            - id: INT-00000007
              corporate_account_id: CRP-75161369
              company_name: TechCorp Inc.
              account_tier: enterprise
              account_status: active
              contact_name: Patricia Morrison
              contact_email: patricia.morrison@techcorp.com
              contact_phone: +1-408-739-2841
              booking_limit: 50
              credit_limit: '200000.00'
              payment_terms: Net 60
              expiration_date: '2026-12-31T00:00:00Z'
              created_at: '2024-03-15T10:00:00Z'
              updated_at: '2025-11-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-38471293
              email: james.reynolds@techcorp.com
              full_name: James Reynolds
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '3780.00'
              total_bookings_count: 2
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-28T11:00:00Z'
              created_at: '2025-01-15T00:00:00Z'
              updated_at: '2025-09-28T11:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-49273618
              hotel_name: The Westin San Jose
              location: San Jose
              partner_tier: premium
              contact_name: Derek Watanabe
              contact_email: manager@westinsanjose.com
              contact_phone: +1-408-295-2000
              escalation_contact: director@westinsanjose.com
              amenities:
                - pool
                - gym
                - spa
                - restaurant
                - wifi
                - business_center
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2024-01-01T10:00:00Z'
              updated_at: '2024-01-01T10:00:00Z'
          payment_api_transactions:
            - id: TXN-00000008
              transaction_id: TXN-00000008
              booking_reference: BKG-68164535
              customer_id: CUS-38471293
              amount: '1890.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Corporate Card ending in 4567
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          zendesk_tickets: []
          zendesk_users:
            - id: USR-10000007
              name: James Reynolds
              email: james.reynolds@techcorp.com
              role: end-user
              organization_id: null
              phone: +1-408-815-3927
              verified: true
              active: true
              created_at: '2025-01-15T00:00:00Z'
              updated_at: '2025-01-15T00:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-68164535
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-75161369
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'james.reynolds@techcorp.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-68164535'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Corporate invoice request - BKG-68164535
                  description: Corporate account holder from TechCorp Inc. requests corporate invoice for completed booking BKG-68164535 for expense processing. Booking value $1,890, checked out 2025-09-28.
                  status: open
                  priority: low
                  type: question
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  booking_reference: BKG-68164535
            - tool: corporate_api_generate_corporate_invoice
              parameters:
                booking_reference: BKG-68164535
                corporate_account_id: CRP-75161369
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  tags:
                    - corporate-account
                  booking_reference: BKG-68164535
                  hotel_id: HTL-49273618
                  booking_value: 1890.0
                  request_type_detail: billing-inquiry
                  corporate_account_id: CRP-75161369
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_cbi_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there! I'm Michael Richardson from NewClient Corp. I'm reaching out regarding our corporate account CRP-79955271. I'd like to understand what benefits we currently have with our account tier and how they compare to the mid-market and enterprise tiers. We're evaluating whether it might be worth upgrading our account. My email is m.richardson@newclientcorp.com.
    user_context: |
        You are Michael Richardson, an employee of NewClient Corp, a corporate account holder on the small business tier. You want to understand your current corporate account benefits and learn about the differences compared to mid-market and enterprise tiers to evaluate if upgrading is worthwhile for your company.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          corporate_api_corporate_accounts:
            - id: INT-00000007
              corporate_account_id: CRP-79955271
              company_name: NewClient Corp
              account_tier: small_business
              account_status: active
              contact_name: Jennifer Martinez
              contact_email: j.martinez@newclientcorp.com
              contact_phone: +1-415-294-7831
              booking_limit: 5
              credit_limit: '10000.00'
              payment_terms: Net 30
              expiration_date: '2026-06-30T00:00:00Z'
              created_at: '2025-03-15T09:00:00Z'
              updated_at: '2025-03-15T09:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Michael Richardson
              email: m.richardson@newclientcorp.com
              role: end-user
              organization_id: null
              phone: +1-415-738-9024
              verified: true
              active: true
              created_at: '2025-04-20T10:00:00Z'
              updated_at: '2025-04-20T10:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_organizations: []
          zendesk_articles: []
          booking_api_bookings: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          crm_api_customer_profiles: []
          hotel_partner_api_hotels: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-79955271
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'm.richardson@newclientcorp.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: requester_id eq 'USR-10000007'
            - tool: zendesk_search_articles
              parameters:
                query: corporate account benefits
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Corporate account benefits inquiry - CRP-79955271
                  description: Customer from NewClient Corp (small_business tier) inquiring about current corporate account benefits and comparison to mid-market and enterprise tiers for potential upgrade consideration.
                  status: open
                  priority: low
                  type: question
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - corporate-account
                  corporate_account_id: CRP-79955271
                  request_type_detail: other
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_cbi_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to ask about our payment terms and when our next invoice is due.
    user_context: |
        You are Rachel Morrison, a corporate account holder from MidSize Partners contacting support to inquire about your company's payment terms and when the next invoice is due for September bookings.

        GOAL: Get clear information about your payment terms and when you should expect to pay for the completed September bookings.

        Only if you are asked about your name or who you are — tell the agent you are Rachel Morrison.
        Only if you are asked about your company — tell the agent you are from MidSize Partners.
        Only if you are asked for your account number or corporate account details — provide corporate account CRP-77449058.
        Only if you are asked about your email address — tell the agent it is rachel.morrison@midsizepartners.com.
        Only if you are asked for more details or context about the bookings — tell the agent you had 3 bookings completed in September.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          zendesk_users:
            - id: USR-10000007
              name: Rachel Morrison
              email: rachel.morrison@midsizepartners.com
              role: end-user
              organization_id: ORG-10000003
              phone: +1-617-284-9037
              verified: true
              active: true
              created_at: '2024-09-15T10:00:00Z'
              updated_at: '2024-09-15T10:00:00Z'
          zendesk_tickets:
            - id: TCK-14770054
              subject: Booking modification request - date change
              description: Corporate account holder requesting modification to existing reservation dates for upcoming business trip
              status: solved
              priority: normal
              type: task
              requester_id: USR-10000007
              assignee_id: USR-10000002
              organization_id: ORG-10000003
              tags:
                - booking-modification
                - corporate-account
              created_at: '2025-09-25T14:30:00Z'
              updated_at: '2025-09-25T17:00:00Z'
              due_at: null
              booking_reference: BKG-00089231
              hotel_id: HTL-00012345
              check_in_date: '2025-11-28T14:00:00Z'
              booking_value: 1850.0
              request_type_detail: modify-dates
              corporate_account_id: CRP-77449058
              group_booking_id: null
              resolution_action: modification-completed
              refund_amount: 0
              escalation_reason: null
          corporate_api_corporate_accounts:
            - id: INT-00000007
              corporate_account_id: CRP-77449058
              company_name: MidSize Partners
              account_tier: mid_market
              account_status: active
              contact_name: Rachel Morrison
              contact_email: rachel.morrison@midsizepartners.com
              contact_phone: +1-617-284-9037
              booking_limit: 15
              credit_limit: '50000.00'
              payment_terms: Net 45
              expiration_date: '2026-09-30T00:00:00Z'
              created_at: '2024-09-01T09:00:00Z'
              updated_at: '2025-11-15T12:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings: []
          booking_api_hotel_inventory: []
          booking_api_group_bookings: []
          crm_api_customer_profiles: []
          hotel_partner_api_hotels: []
          payment_api_transactions: []
          lookup_bookings: []
          lookup_hotels: []
          lookup_group_bookings: []
          lookup_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'rachel.morrison@midsizepartners.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: requester_id eq 'USR-10000007'
                orderby: created_at desc
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-77449058
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Corporate billing inquiry - payment terms - CRP-77449058
                  description: 'Corporate account holder from MidSize Partners inquiring about payment terms and invoice due date for completed September bookings. Account tier: mid_market, Payment terms: Net 45.'
                  status: open
                  priority: low
                  type: question
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - corporate-account
                  request_type_detail: billing-inquiry
                  corporate_account_id: CRP-77449058
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_cbi_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I have a question about our corporate account.
    user_context: |
        You are Jennifer Taylor, a corporate account holder from GrowingBusiness Inc., contacting support to inquire about your company's credit limit and current utilization. You have upcoming travel planned and want to ensure you won't exceed your credit limit when booking.

        Only if you are asked about your name — tell the agent you are Jennifer Taylor.
        Only if you are asked about your company name — tell the agent it is GrowingBusiness Inc.
        Only if you are asked about your email address — tell the agent it is jennifer.taylor@growingbusiness.com.
        Only if you are asked what specific information you need — tell the agent you'd like to know what your current credit limit is and how much of it you're currently using.
        Only if you are asked why you need this information — explain that you have some upcoming business travel planned and you want to make sure you have enough room on the account before booking additional stays.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If the agent provides credit limit and utilization information, acknowledge receipt and thank them for the help.
    init:
      external_booking_v1:
        data_patch:
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: jennifer.taylor@growingbusiness.com
              full_name: Jennifer Taylor
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '3350.00'
              total_bookings_count: 8
              preferences:
                - early check-in
                - non-smoking room
              special_notes:
                - corporate traveler - GrowingBusiness Inc.
              complaint_count: 0
              last_booking_date: '2025-11-15T14:00:00Z'
              created_at: '2024-08-15T10:00:00Z'
              updated_at: '2025-11-20T12:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Jennifer Taylor
              email: jennifer.taylor@growingbusiness.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-617-482-7391
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          corporate_api_corporate_accounts:
            - id: INT-00000007
              corporate_account_id: CRP-11998679
              company_name: GrowingBusiness Inc.
              account_tier: small_business
              account_status: active
              contact_name: Jennifer Taylor
              contact_email: jennifer.taylor@growingbusiness.com
              contact_phone: +1-617-482-7391
              booking_limit: 5
              credit_limit: '10000.00'
              payment_terms: Net 30
              expiration_date: '2026-06-30T00:00:00Z'
              created_at: '2024-08-01T10:00:00Z'
              updated_at: '2025-11-27T19:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-00097345
              customer_id: CUS-00000006
              hotel_id: HTL-00012345
              check_in_date: '2025-12-05T15:00:00Z'
              check_out_date: '2025-12-08T11:00:00Z'
              booking_value: '1200.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 1
              children_count: 0
              booking_status: confirmed
              corporate_account_id: CRP-11998679
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-11-01T10:00:00Z'
              updated_at: '2025-11-01T10:00:00Z'
            - id: BKG-00000007
              booking_reference: BKG-00097346
              customer_id: CUS-00000006
              hotel_id: HTL-00012346
              check_in_date: '2025-12-10T15:00:00Z'
              check_out_date: '2025-12-13T11:00:00Z'
              booking_value: '1300.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 1
              children_count: 0
              booking_status: confirmed
              corporate_account_id: CRP-11998679
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-11-05T10:00:00Z'
              updated_at: '2025-11-05T10:00:00Z'
            - id: BKG-00000008
              booking_reference: BKG-00097347
              customer_id: CUS-00000006
              hotel_id: HTL-00012345
              check_in_date: '2025-10-20T15:00:00Z'
              check_out_date: '2025-10-22T11:00:00Z'
              booking_value: '800.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 1
              children_count: 0
              booking_status: checked_out
              corporate_account_id: CRP-11998679
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-10-01T10:00:00Z'
              updated_at: '2025-10-22T12:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          hotel_partner_api_hotels: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: crm_api_get_customer_profile
              parameters:
                email: jennifer.taylor@growingbusiness.com
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'jennifer.taylor@growingbusiness.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: requester_id eq 'USR-10000007'
                orderby: created_at desc
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Credit limit and utilization inquiry - Corporate Account
                  description: Corporate account holder from GrowingBusiness Inc. is requesting information about their current credit limit and how close they are to it. Customer has upcoming travel planned and wants to ensure they won't exceed their credit limit.
                  status: open
                  priority: low
                  type: question
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - corporate-account
                  request_type_detail: billing-inquiry
                  corporate_account_id: CRP-11998679
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-11998679
            - tool: corporate_api_get_corporate_booking_history
              parameters:
                corporate_account_id: CRP-11998679
            - tool: zendesk_search_articles
              parameters:
                query: corporate account benefits
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_cbm_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to change the check-in date for my hotel booking. I'm Michael Reynolds from TechCorp Inc., my email is michael.reynolds@techcorp.com. My booking reference is BKG-18495931. I'd like to move my check-in from October 5th to October 8th. Is that possible?
    user_context: |
        You are Michael Reynolds, a corporate employee at TechCorp Inc., contacting support to change your hotel booking check-in date from October 5, 2025 to October 8, 2025. Your booking reference is BKG-18495931.

        Your original stay is 5 nights (October 5-10). When moving check-in to October 8, you want to keep the same 5-night duration, so your checkout should also move to October 13, 2025. If the agent asks about checkout, confirm you want it changed to October 13.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-18495931
              customer_id: CUS-00000006
              hotel_id: HTL-00012350
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-10T11:00:00Z'
              booking_value: '1850.00'
              room_type: executive_suite
              board_type: full_board
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: CRP-59407816
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          corporate_api_corporate_accounts:
            - id: INT-00000007
              corporate_account_id: CRP-59407816
              company_name: TechCorp Inc.
              account_tier: enterprise
              account_status: active
              contact_name: Jennifer Martinez
              contact_email: jennifer.martinez@techcorp.com
              contact_phone: +1-415-782-9134
              booking_limit: 50
              credit_limit: '200000.00'
              payment_terms: Net 60
              expiration_date: '2026-12-31T00:00:00Z'
              created_at: '2024-06-15T10:00:00Z'
              updated_at: '2024-06-15T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: michael.reynolds@techcorp.com
              full_name: Michael Reynolds
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '8500.00'
              total_bookings_count: 5
              preferences:
                - quiet room
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-03-10T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00012350
              hotel_id: HTL-00012350
              hotel_name: Riverside Business Hotel
              location: Chicago
              partner_tier: standard
              contact_name: Patricia Chen
              contact_email: reservations@riversidebusiness.com
              contact_phone: +1-312-847-5219
              escalation_contact: null
              amenities:
                - wifi
                - business_center
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: full_board
              date: '2025-10-08T00:00:00Z'
              available_count: 3
              price_per_night: '370.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: full_board
              date: '2025-10-09T00:00:00Z'
              available_count: 3
              price_per_night: '370.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000008
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: full_board
              date: '2025-10-10T00:00:00Z'
              available_count: 3
              price_per_night: '370.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000009
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: full_board
              date: '2025-10-11T00:00:00Z'
              available_count: 3
              price_per_night: '370.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000010
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: full_board
              date: '2025-10-12T00:00:00Z'
              available_count: 3
              price_per_night: '370.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000011
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: without_breakfast
              date: '2025-10-08T00:00:00Z'
              available_count: 3
              price_per_night: '295.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000012
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: without_breakfast
              date: '2025-10-09T00:00:00Z'
              available_count: 3
              price_per_night: '295.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000013
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: without_breakfast
              date: '2025-10-10T00:00:00Z'
              available_count: 3
              price_per_night: '295.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000014
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: without_breakfast
              date: '2025-10-11T00:00:00Z'
              available_count: 3
              price_per_night: '295.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000015
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: without_breakfast
              date: '2025-10-12T00:00:00Z'
              available_count: 3
              price_per_night: '295.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000016
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: with_breakfast
              date: '2025-10-08T00:00:00Z'
              available_count: 3
              price_per_night: '325.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000017
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: with_breakfast
              date: '2025-10-09T00:00:00Z'
              available_count: 3
              price_per_night: '325.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000018
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: with_breakfast
              date: '2025-10-10T00:00:00Z'
              available_count: 3
              price_per_night: '325.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000019
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: with_breakfast
              date: '2025-10-11T00:00:00Z'
              available_count: 3
              price_per_night: '325.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000020
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: with_breakfast
              date: '2025-10-12T00:00:00Z'
              available_count: 3
              price_per_night: '325.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000021
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: half_board
              date: '2025-10-08T00:00:00Z'
              available_count: 3
              price_per_night: '350.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000022
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: half_board
              date: '2025-10-09T00:00:00Z'
              available_count: 3
              price_per_night: '350.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000023
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: half_board
              date: '2025-10-10T00:00:00Z'
              available_count: 3
              price_per_night: '350.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000024
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: half_board
              date: '2025-10-11T00:00:00Z'
              available_count: 3
              price_per_night: '350.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000025
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: half_board
              date: '2025-10-12T00:00:00Z'
              available_count: 3
              price_per_night: '350.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000026
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: all_inclusive
              date: '2025-10-08T00:00:00Z'
              available_count: 3
              price_per_night: '425.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000027
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: all_inclusive
              date: '2025-10-09T00:00:00Z'
              available_count: 3
              price_per_night: '425.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000028
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: all_inclusive
              date: '2025-10-10T00:00:00Z'
              available_count: 3
              price_per_night: '425.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000029
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: all_inclusive
              date: '2025-10-11T00:00:00Z'
              available_count: 3
              price_per_night: '425.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000030
              hotel_id: HTL-00012350
              room_type: executive_suite
              board_type: all_inclusive
              date: '2025-10-12T00:00:00Z'
              available_count: 3
              price_per_night: '425.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Michael Reynolds
              email: michael.reynolds@techcorp.com
              role: end-user
              organization_id: ORG-10000003
              phone: +1-415-693-7284
              verified: true
              active: true
              created_at: '2024-03-10T00:00:00Z'
              updated_at: '2024-03-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-18495931
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-59407816
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00012350
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00012350
                check_in_date: '2025-10-08T15:00:00Z'
                check_out_date: '2025-10-13T11:00:00Z'
                room_type: executive_suite
                board_type: full_board
                adults_count: 2
                children_count: 0
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'michael.reynolds@techcorp.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-18495931'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Date modification request - BKG-18495931
                  description: Corporate account holder from TechCorp Inc. (Enterprise tier) requests to change check-in date from 2025-10-05 to 2025-10-08 for booking BKG-18495931 at standard partner hotel. Executive suite, full board, booking value $1,850.
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - corporate-account
                    - check-in-upcoming
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-18495931
                check_in_date: '2025-10-08T15:00:00Z'
                check_out_date: '2025-10-13T11:00:00Z'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  priority: normal
                  type: task
                  tags:
                    - corporate-account
                    - check-in-upcoming
                  booking_reference: BKG-18495931
                  hotel_id: HTL-00012350
                  check_in_date: '2025-10-08T15:00:00Z'
                  booking_value: 1850.0
                  request_type_detail: modify-dates
                  corporate_account_id: CRP-59407816
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_cbm_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to modify my hotel booking. I'm Marcus Wellington from GlobalFinance LLC, email marcus.wellington@globalfinance.com. My booking reference is BKG-82071518. I need to downgrade from the presidential suite to an executive suite due to a budget revision at our company. The check-in is today so I'm hoping this can be handled quickly.
    user_context: |
        You are Marcus Wellington, an employee of GlobalFinance LLC contacting support to request a room type change on your corporate booking. You need to change from presidential_suite to executive_suite due to budget constraints from your company.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent explains that hotel confirmation is needed for same-day changes, acknowledge and accept this process.
        - You want to keep the same board type (breakfast included) if possible.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-82071518
              booking_reference: BKG-82071518
              customer_id: CUS-48291756
              hotel_id: HTL-93847261
              check_in_date: '2025-10-01T16:00:00Z'
              check_out_date: '2025-10-03T11:00:00Z'
              booking_value: '2100.00'
              room_type: presidential_suite
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: CRP-80793597
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-93847001
              hotel_id: HTL-93847261
              room_type: executive_suite
              board_type: without_breakfast
              date: '2025-10-01T00:00:00Z'
              available_count: 3
              price_per_night: '800.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-93847002
              hotel_id: HTL-93847261
              room_type: executive_suite
              board_type: with_breakfast
              date: '2025-10-01T00:00:00Z'
              available_count: 3
              price_per_night: '850.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-93847003
              hotel_id: HTL-93847261
              room_type: executive_suite
              board_type: half_board
              date: '2025-10-01T00:00:00Z'
              available_count: 3
              price_per_night: '900.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-93847004
              hotel_id: HTL-93847261
              room_type: executive_suite
              board_type: full_board
              date: '2025-10-01T00:00:00Z'
              available_count: 3
              price_per_night: '950.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-93847005
              hotel_id: HTL-93847261
              room_type: executive_suite
              board_type: without_breakfast
              date: '2025-10-02T00:00:00Z'
              available_count: 3
              price_per_night: '800.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-93847006
              hotel_id: HTL-93847261
              room_type: executive_suite
              board_type: with_breakfast
              date: '2025-10-02T00:00:00Z'
              available_count: 3
              price_per_night: '850.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-93847007
              hotel_id: HTL-93847261
              room_type: executive_suite
              board_type: half_board
              date: '2025-10-02T00:00:00Z'
              available_count: 3
              price_per_night: '900.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-93847008
              hotel_id: HTL-93847261
              room_type: executive_suite
              board_type: full_board
              date: '2025-10-02T00:00:00Z'
              available_count: 3
              price_per_night: '950.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          booking_api_group_bookings: []
          crm_api_customer_profiles:
            - id: CUS-48291756
              customer_id: CUS-48291756
              email: marcus.wellington@globalfinance.com
              full_name: Marcus Wellington
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '15000.00'
              total_bookings_count: 5
              preferences:
                - quiet room
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-06-15T09:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          corporate_api_corporate_accounts:
            - id: INT-80793597
              corporate_account_id: CRP-80793597
              company_name: GlobalFinance LLC
              account_tier: enterprise
              account_status: active
              contact_name: Jennifer Castillo
              contact_email: jcastillo@globalfinance.com
              contact_phone: +1-312-847-9215
              booking_limit: 50
              credit_limit: '200000.00'
              payment_terms: Net 60
              expiration_date: '2026-12-31T00:00:00Z'
              created_at: '2024-01-15T09:00:00Z'
              updated_at: '2025-08-20T14:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-93847261
              hotel_id: HTL-93847261
              hotel_name: The Grandview Palace
              location: Chicago
              partner_tier: premium
              contact_name: Victoria Harrington
              contact_email: reservations@grandviewpalace.com
              contact_phone: +1-312-528-7193
              escalation_contact: manager@grandviewpalace.com
              amenities:
                - pool
                - gym
                - spa
                - restaurant
                - wifi
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions: []
          zendesk_tickets: []
          zendesk_users:
            - id: USR-48291756
              name: Marcus Wellington
              email: marcus.wellington@globalfinance.com
              role: end-user
              organization_id: ORG-10000003
              phone: +1-312-749-8362
              verified: true
              active: true
              created_at: '2024-06-15T09:00:00Z'
              updated_at: '2024-06-15T09:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-82071518
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-82071518'
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-48291756
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-80793597
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-93847261
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-93847261
                check_in_date: '2025-10-01T16:00:00Z'
                check_out_date: '2025-10-03T11:00:00Z'
                room_type: executive_suite
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.wellington@globalfinance.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Room type modification request - BKG-82071518
                  description: 'Customer from GlobalFinance LLC (Enterprise corporate account CRP-80793597) requesting room type change from presidential_suite to executive_suite. Same-day modification at premium hotel - requires hotel partner confirmation. Enterprise tier: modification fee waived. Executive suite availability confirmed (3 rooms available). Price difference: -$400 (refund due upon approval).'
                  status: open
                  priority: urgent
                  type: task
                  requester_id: USR-48291756
                  assignee_id: AG-83945
                  tags:
                    - corporate-account
                    - check-in-today
                  booking_reference: BKG-82071518
                  hotel_id: HTL-93847261
                  check_in_date: '2025-10-01T16:00:00Z'
                  booking_value: 2100.0
                  request_type_detail: modify-room-type
                  corporate_account_id: CRP-80793597
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-93847261
                booking_reference: BKG-82071518
                issue_type: same-day-modification
                description: 'Enterprise corporate customer (GlobalFinance LLC) requests same-day room type modification from presidential_suite to executive_suite. Check-in: 2025-10-01T16:00:00Z (3 hours from now). Executive suite availability confirmed (3 rooms available). Please confirm if this modification can be accommodated.'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: hold
                  description: 'Customer from GlobalFinance LLC (Enterprise corporate account CRP-80793597) requesting room type change from presidential_suite to executive_suite. Same-day modification at premium hotel - requires hotel partner confirmation. Enterprise tier: modification fee waived. Executive suite availability confirmed (3 rooms available). Price difference: -$400 (refund due upon approval). Hotel escalation: Escalated with ticket ZDSK-00000013. Awaiting hotel confirmation for same-day room type change.'
                  tags:
                    - corporate-account
                    - check-in-today
                    - hotel-partner-escalation
                  escalation_reason: same-day-modification
                  refund_amount: 0
    """

    validate_database(x)


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
              created_at: '2025-09-29T13:00:00Z'
              updated_at: '2025-09-29T14:00:00Z'
              due_at: null
              booking_reference: BKG-46291486
              hotel_id: HTL-46291500
              check_in_date: '2025-10-06T15:00:00Z'
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
              created_at: '2025-02-15T00:00:00Z'
              updated_at: '2025-02-15T00:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-46291486
              customer_id: CUS-00000006
              hotel_id: HTL-46291500
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-08T11:00:00Z'
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
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-46291500
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-06T00:00:00Z'
              available_count: 3
              price_per_night: '390.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-46291500
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-07T00:00:00Z'
              available_count: 3
              price_per_night: '390.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000008
              hotel_id: HTL-46291500
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-08T00:00:00Z'
              available_count: 3
              price_per_night: '390.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000009
              hotel_id: HTL-46291500
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-09T00:00:00Z'
              available_count: 3
              price_per_night: '390.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
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
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
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
              expiration_date: '2026-06-30T00:00:00Z'
              created_at: '2024-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
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
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
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
                filter: booking_reference eq 'BKG-46291486'
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
                check_in_date: '2025-10-08T15:00:00Z'
                check_out_date: '2025-10-10T11:00:00Z'
                room_type: deluxe_room
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-46291486
                check_out_date: '2025-10-10T11:00:00Z'
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
                  check_in_date: '2025-10-06T15:00:00Z'
                  booking_value: 1560.0
                  request_type_detail: modify-dates
                  corporate_account_id: CRP-49251925
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_cbm_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'd like to change the meal plan on my upcoming hotel booking. Can you help with this?
    user_context: |
        You are Marcus Henderson, a corporate employee at RegionalSales Inc., contacting support to change the board type on your upcoming hotel booking from without_breakfast to full_board.

        Only if you are asked about your booking reference or confirmation number — tell the agent it is BKG-22141888.
        Only if you are asked about your email address — tell the agent it is marcus.henderson@regionalsales.com.
        Only if you are asked about your current meal plan or board type — tell the agent you currently have the room without breakfast.
        Only if you are asked about what meal plan you want or what change you'd like to make — tell the agent you'd like to upgrade to full board instead.
        Only if you are asked about the trip type or company — tell the agent this is a business trip through your company RegionalSales Inc.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm the charges or fee for the modification, confirm that you agree to proceed.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-22141888
              customer_id: CUS-44556677
              hotel_id: HTL-88990011
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              room_type: suite
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_value: '890.00'
              booking_status: confirmed
              corporate_account_id: CRP-54235733
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-44556677
              customer_id: CUS-44556677
              email: marcus.henderson@regionalsales.com
              full_name: Marcus Henderson
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '2450.00'
              total_bookings_count: 4
              preferences:
                - early check-in
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-20T14:00:00Z'
              created_at: '2025-02-15T10:00:00Z'
              updated_at: '2025-08-20T14:00:00Z'
          corporate_api_corporate_accounts:
            - id: INT-00000007
              corporate_account_id: CRP-54235733
              company_name: RegionalSales Inc.
              account_tier: mid_market
              account_status: active
              contact_name: Jennifer Walsh
              contact_email: jwalsh@regionalsales.com
              contact_phone: +1-404-738-2914
              booking_limit: 15
              credit_limit: '50000.00'
              payment_terms: Net 45
              expiration_date: '2026-08-31T00:00:00Z'
              created_at: '2024-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-88990011
              hotel_id: HTL-88990011
              hotel_name: The Regency Suites
              location: Atlanta
              partner_tier: premium
              contact_name: Victoria Palmer
              contact_email: vpalmer@regencysuites.com
              contact_phone: +1-404-512-7834
              escalation_contact: management@regencysuites.com
              amenities:
                - pool
                - spa
                - gym
                - restaurant
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Henderson
              email: marcus.henderson@regionalsales.com
              role: end-user
              organization_id: ORG-10000006
              phone: +1-404-293-8174
              verified: true
              active: true
              created_at: '2025-02-20T00:00:00Z'
              updated_at: '2025-02-20T00:00:00Z'
          zendesk_organizations:
            - id: ORG-10000006
              name: RegionalSales Inc.
              domain_names:
                - regionalsales.com
              details: Corporate travel client - mid-market tier
              notes: Net 45 payment terms
              created_at: '2024-09-01T00:00:00Z'
              updated_at: '2024-09-01T00:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-88990011
              room_type: suite
              board_type: full_board
              date: '2025-10-04T00:00:00Z'
              available_count: 3
              price_per_night: '350.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-88990011
              room_type: suite
              board_type: full_board
              date: '2025-10-05T00:00:00Z'
              available_count: 3
              price_per_night: '350.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000008
              hotel_id: HTL-88990011
              room_type: suite
              board_type: full_board
              date: '2025-10-06T00:00:00Z'
              available_count: 3
              price_per_night: '350.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000009
              hotel_id: HTL-88990011
              room_type: suite
              board_type: without_breakfast
              date: '2025-10-04T00:00:00Z'
              available_count: 4
              price_per_night: '297.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000010
              hotel_id: HTL-88990011
              room_type: suite
              board_type: without_breakfast
              date: '2025-10-05T00:00:00Z'
              available_count: 4
              price_per_night: '297.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000011
              hotel_id: HTL-88990011
              room_type: suite
              board_type: without_breakfast
              date: '2025-10-06T00:00:00Z'
              available_count: 4
              price_per_night: '297.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000012
              hotel_id: HTL-88990011
              room_type: suite
              board_type: with_breakfast
              date: '2025-10-04T00:00:00Z'
              available_count: 3
              price_per_night: '315.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000013
              hotel_id: HTL-88990011
              room_type: suite
              board_type: half_board
              date: '2025-10-04T00:00:00Z'
              available_count: 3
              price_per_night: '330.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000014
              hotel_id: HTL-88990011
              room_type: suite
              board_type: all_inclusive
              date: '2025-10-04T00:00:00Z'
              available_count: 2
              price_per_night: '425.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_tickets: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          payment_api_transactions: []
          booking_api_group_bookings: []
          lookup_bookings: []
          lookup_hotels: []
          lookup_group_bookings: []
          lookup_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-22141888
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-44556677
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-54235733
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-88990011
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.henderson@regionalsales.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-22141888'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Board type modification request - BKG-22141888
                  description: 'Corporate customer from RegionalSales Inc. requests to change board type from without_breakfast to full_board for booking BKG-22141888. Check-in: 2025-10-04.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-88990011
                check_in_date: '2025-10-04T15:00:00Z'
                check_out_date: '2025-10-07T11:00:00Z'
                room_type: suite
                board_type: full_board
                adults_count: 2
                children_count: 0
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-22141888
                board_type: full_board
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-22141888
                charge_amount: '172.50'
                reason: board_type_modification_fee_and_price_difference
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  tags:
                    - corporate-account
                    - check-in-upcoming
                  booking_reference: BKG-22141888
                  hotel_id: HTL-88990011
                  check_in_date: '2025-10-04T15:00:00Z'
                  booking_value: 1050.0
                  request_type_detail: modify-board-type
                  corporate_account_id: CRP-54235733
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_cbm_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to change my hotel booking dates. My name is Michael Henderson and my email is m.henderson@consultinggroup.com. I'm booking through my company ConsultingGroup. My booking reference is BKG-29270653 and I need to move my check-in from October 8th to October 12th instead. Is that possible?
    user_context: |
        You are Michael Henderson, an employee at ConsultingGroup who needs to change your hotel booking dates. You want to move your check-in from October 8, 2025 to October 12, 2025.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent explains that manager approval is required, acknowledge and accept the process.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-29270653
              booking_reference: BKG-29270653
              customer_id: CUS-37482916
              hotel_id: HTL-48273651
              check_in_date: '2025-10-08T15:00:00Z'
              check_out_date: '2025-10-10T11:00:00Z'
              room_type: executive_suite
              board_type: with_breakfast
              booking_value: '1250.00'
              booking_status: confirmed
              corporate_account_id: CRP-05929622
              group_booking_id: null
              adults_count: 2
              children_count: 0
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory:
            - id: INV-10000006
              hotel_id: HTL-48273651
              room_type: executive_suite
              board_type: with_breakfast
              date: '2025-10-12T00:00:00Z'
              available_count: 2
              price_per_night: '625.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-10000007
              hotel_id: HTL-48273651
              room_type: executive_suite
              board_type: without_breakfast
              date: '2025-10-12T00:00:00Z'
              available_count: 2
              price_per_night: '575.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-10000008
              hotel_id: HTL-48273651
              room_type: executive_suite
              board_type: half_board
              date: '2025-10-12T00:00:00Z'
              available_count: 2
              price_per_night: '700.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-10000009
              hotel_id: HTL-48273651
              room_type: executive_suite
              board_type: with_breakfast
              date: '2025-10-13T00:00:00Z'
              available_count: 2
              price_per_night: '625.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-10000010
              hotel_id: HTL-48273651
              room_type: executive_suite
              board_type: without_breakfast
              date: '2025-10-13T00:00:00Z'
              available_count: 2
              price_per_night: '575.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-10000011
              hotel_id: HTL-48273651
              room_type: executive_suite
              board_type: half_board
              date: '2025-10-13T00:00:00Z'
              available_count: 2
              price_per_night: '700.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          corporate_api_corporate_accounts:
            - id: INT-05929622
              corporate_account_id: CRP-05929622
              company_name: ConsultingGroup
              account_tier: mid_market
              account_status: active
              contact_name: Patricia Wells
              contact_email: pwells@consultinggroup.com
              contact_phone: +1-617-482-7391
              booking_limit: 15
              credit_limit: '50000.00'
              payment_terms: Net 45
              expiration_date: '2026-12-31T00:00:00Z'
              created_at: '2024-03-15T10:00:00Z'
              updated_at: '2025-08-20T14:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-37482916
              customer_id: CUS-37482916
              email: m.henderson@consultinggroup.com
              full_name: Michael Henderson
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '3500.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-06-10T09:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-48273651
              hotel_id: HTL-48273651
              hotel_name: Metropolitan Business Hotel
              location: Boston
              partner_tier: standard
              contact_name: Jonathan Brooks
              contact_email: reservations@metropolitanbusiness.com
              contact_phone: +1-617-294-5831
              escalation_contact: null
              amenities:
                - wifi
                - gym
                - business_center
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2024-06-01T10:00:00Z'
          payment_api_transactions: []
          zendesk_tickets:
            - id: TCK-79473834
              subject: Billing inquiry - BKG-29270653
              description: Customer requesting clarification on additional charges for corporate booking
              status: solved
              priority: normal
              type: question
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: null
              tags:
                - billing
                - corporate-account
              created_at: '2025-09-25T14:30:00Z'
              updated_at: '2025-09-26T11:00:00Z'
              due_at: null
              booking_reference: BKG-29270653
              hotel_id: HTL-48273651
              check_in_date: '2025-10-08T15:00:00Z'
              booking_value: 1250.0
              request_type_detail: billing-inquiry
              corporate_account_id: CRP-05929622
              group_booking_id: null
              resolution_action: information-provided
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Michael Henderson
              email: m.henderson@consultinggroup.com
              role: end-user
              organization_id: null
              phone: +1-617-394-8271
              verified: true
              active: true
              created_at: '2025-06-10T09:00:00Z'
              updated_at: '2025-06-10T09:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-29270653
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-37482916
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-05929622
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-48273651
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-48273651
                check_in_date: '2025-10-12T15:00:00Z'
                check_out_date: '2025-10-14T11:00:00Z'
                room_type: executive_suite
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'm.henderson@consultinggroup.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-29270653'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Date modification request - BKG-29270653
                  description: 'Corporate customer requests to change check-in date from 2025-10-08 to 2025-10-12 for booking BKG-29270653. Corporate account: CRP-05929622 (ConsultingGroup, mid-market tier, active). Original booking value: $1,250.00. Room type: executive_suite. Availability confirmed for new dates. Per corporate policy (mid-market tier with booking value ≥$1,000), manager approval is required before executing modification. Modification fees will be waived upon approval.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - corporate-account
                    - check-in-upcoming
                  booking_reference: BKG-29270653
                  hotel_id: HTL-48273651
                  check_in_date: '2025-10-08T15:00:00Z'
                  booking_value: 1250.0
                  request_type_detail: modify-dates
                  corporate_account_id: CRP-05929622
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: hold
    """

    validate_database(x)


def test_cbm_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Marcus Bennett from DataDriven Co. and I urgently need to make a change to my corporate booking BKG-88623924. I need to switch my room type from suite to a deluxe room. My check-in is tomorrow and this change is really important for my trip. My email is marcus.bennett@datadriven.co. Can you help me with this?
    user_context: |
        You are Marcus Bennett, a corporate traveler from DataDriven Co., urgently needing to change your room type from suite to deluxe_room for your upcoming booking.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If the agent explains that manager approval is required before the modification can be processed, acknowledge this and thank them for handling the request.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-88623924
              booking_reference: BKG-88623924
              customer_id: CUS-82947361
              hotel_id: HTL-94825173
              check_in_date: '2025-10-02T14:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              room_type: suite
              board_type: half_board
              adults_count: 2
              children_count: 0
              booking_value: '1450.00'
              booking_status: confirmed
              corporate_account_id: CRP-73597746
              group_booking_id: null
              modification_history:
                - '2025-09-20T10:00:00Z: board_type: with_breakfast -> half_board'
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-20T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-94825173
              hotel_id: HTL-94825173
              hotel_name: Riverside Budget Suites
              location: Chicago
              partner_tier: budget
              contact_name: Patricia Hernandez
              contact_email: manager@riversidebudget.com
              contact_phone: +1-312-528-7342
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-82947361
              customer_id: CUS-82947361
              email: marcus.bennett@datadriven.co
              full_name: Marcus Bennett
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '4350.75'
              total_bookings_count: 8
              preferences:
                - early check-in
                - quiet room
              special_notes:
                - corporate traveler - prefers efficiency
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-06-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          corporate_api_corporate_accounts:
            - id: INT-00000007
              corporate_account_id: CRP-73597746
              company_name: DataDriven Co.
              account_tier: mid_market
              account_status: active
              contact_name: Jennifer Walsh
              contact_email: jwalsh@datadriven.co
              contact_phone: +1-312-847-5921
              booking_limit: 15
              credit_limit: '50000.00'
              payment_terms: Net 45
              expiration_date: '2026-06-30T00:00:00Z'
              created_at: '2024-02-15T10:00:00Z'
              updated_at: '2025-08-20T10:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-94825173
              room_type: deluxe_room
              board_type: half_board
              date: '2025-10-02T00:00:00Z'
              available_count: 3
              price_per_night: '145.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-94825173
              room_type: deluxe_room
              board_type: half_board
              date: '2025-10-03T00:00:00Z'
              available_count: 3
              price_per_night: '145.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000008
              hotel_id: HTL-94825173
              room_type: deluxe_room
              board_type: half_board
              date: '2025-10-04T00:00:00Z'
              available_count: 3
              price_per_night: '145.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000009
              hotel_id: HTL-94825173
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-02T00:00:00Z'
              available_count: 4
              price_per_night: '130.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000010
              hotel_id: HTL-94825173
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-03T00:00:00Z'
              available_count: 4
              price_per_night: '130.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000011
              hotel_id: HTL-94825173
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-04T00:00:00Z'
              available_count: 4
              price_per_night: '130.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000012
              hotel_id: HTL-94825173
              room_type: deluxe_room
              board_type: without_breakfast
              date: '2025-10-02T00:00:00Z'
              available_count: 5
              price_per_night: '115.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000013
              hotel_id: HTL-94825173
              room_type: deluxe_room
              board_type: without_breakfast
              date: '2025-10-03T00:00:00Z'
              available_count: 5
              price_per_night: '115.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000014
              hotel_id: HTL-94825173
              room_type: deluxe_room
              board_type: without_breakfast
              date: '2025-10-04T00:00:00Z'
              available_count: 5
              price_per_night: '115.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Bennett
              email: marcus.bennett@datadriven.co
              role: end-user
              organization_id: ORG-10000003
              phone: +1-312-694-8273
              verified: true
              active: true
              created_at: '2024-06-15T00:00:00Z'
              updated_at: '2024-06-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-88623924'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-88623924
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-94825173
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-82947361
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-73597746
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-94825173
                check_in_date: '2025-10-02T14:00:00Z'
                check_out_date: '2025-10-05T11:00:00Z'
                room_type: deluxe_room
                board_type: half_board
                adults_count: 2
                children_count: 0
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.bennett@datadriven.co'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Room type modification request - BKG-88623924
                  description: 'Corporate customer (DataDriven Co., mid_market tier) requests room type change from suite to deluxe_room for booking BKG-88623924. Check-in: 2025-10-02. Original booking value: $1,450. Per policy Section 4.1.4, mid_market corporate bookings ≥$1,000 require manager approval before modification execution. Room availability confirmed. Awaiting manager approval.'
                  status: open
                  priority: high
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: hold
                  tags:
                    - corporate-account
                    - check-in-upcoming
                  booking_reference: BKG-88623924
                  hotel_id: HTL-94825173
                  check_in_date: '2025-10-02T14:00:00Z'
                  booking_value: 1450.0
                  request_type_detail: modify-room-type
                  corporate_account_id: CRP-73597746
                  refund_amount: 0
    """

    validate_database(x)


def test_cbm_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I have a booking coming up in a couple of days and I'd like to add breakfast to it. My name is James Wilson, email james.wilson@localservicesllc.net, and the booking reference is BKG-15220472. It's a corporate booking through LocalServices LLC. Can you help me upgrade to include breakfast?
    user_context: |
        You are James Wilson, an employee at LocalServices LLC, contacting support to add breakfast to your upcoming hotel booking (BKG-15220472). You want to upgrade from without_breakfast to with_breakfast.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If the agent informs you of any fees or charges for the modification, confirm you are okay to proceed.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-15220472
              booking_reference: BKG-15220472
              customer_id: CUS-84629175
              hotel_id: HTL-77320841
              check_in_date: '2025-10-03T15:00:00Z'
              check_out_date: '2025-10-04T11:00:00Z'
              booking_value: '310.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: CRP-53615305
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-77320841
              hotel_id: HTL-77320841
              hotel_name: Budget Stay Inn
              location: Denver
              partner_tier: budget
              contact_name: Patricia Nelson
              contact_email: frontdesk@budgetstayinn.com
              contact_phone: +1-720-493-6821
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          corporate_api_corporate_accounts:
            - id: INT-53615305
              corporate_account_id: CRP-53615305
              company_name: LocalServices LLC
              account_tier: small_business
              account_status: active
              contact_name: Marcus Bradley
              contact_email: contact@localservicesllc.net
              contact_phone: +1-720-841-5972
              booking_limit: 5
              credit_limit: '10000.00'
              payment_terms: Net 30
              expiration_date: '2026-06-30T00:00:00Z'
              created_at: '2025-02-15T10:00:00Z'
              updated_at: '2025-02-15T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-84629175
              customer_id: CUS-84629175
              email: james.wilson@localservicesllc.net
              full_name: James Wilson
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '850.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T14:00:00Z'
              created_at: '2025-03-10T10:00:00Z'
              updated_at: '2025-08-15T12:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-77320841-01
              hotel_id: HTL-77320841
              room_type: standard_room
              board_type: with_breakfast
              date: '2025-10-03T00:00:00Z'
              available_count: 8
              price_per_night: '340.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-77320841-02
              hotel_id: HTL-77320841
              room_type: standard_room
              board_type: without_breakfast
              date: '2025-10-03T00:00:00Z'
              available_count: 10
              price_per_night: '310.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-77320841-03
              hotel_id: HTL-77320841
              room_type: standard_room
              board_type: half_board
              date: '2025-10-03T00:00:00Z'
              available_count: 5
              price_per_night: '380.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-29481730
              name: James Wilson
              email: james.wilson@localservicesllc.net
              role: end-user
              organization_id: null
              phone: +1-720-384-5167
              verified: true
              active: true
              created_at: '2025-03-10T10:00:00Z'
              updated_at: '2025-03-10T10:00:00Z'
            - id: USR-20847361
              name: Rachel Martinez
              email: rachel.martinez@staybridge.com
              role: agent
              organization_id: null
              phone: +1-720-528-4193
              verified: true
              active: true
              created_at: '2024-01-15T10:00:00Z'
              updated_at: '2024-01-15T10:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          payment_api_transactions: []
          lookup_bookings: []
          lookup_hotels: []
          lookup_group_bookings: []
          lookup_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-15220472
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-77320841
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-53615305
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-84629175
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-77320841
                check_in_date: '2025-10-03T15:00:00Z'
                check_out_date: '2025-10-04T11:00:00Z'
                room_type: standard_room
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'james.wilson@localservicesllc.net'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-15220472'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Board type modification request - BKG-15220472
                  description: 'Customer requests to change board type from without_breakfast to with_breakfast. Booking at budget partner hotel, check-in 2025-10-03. Corporate account: CRP-53615305 (small_business tier). Modification fee: $37.50, price difference: $30.00. Total charge: $67.50.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-29481730
                  assignee_id: AG-83945
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-15220472
                board_type: with_breakfast
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-15220472
                charge_amount: '67.50'
                reason: modification_fee_and_price_difference
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  tags:
                    - corporate-account
                    - check-in-upcoming
                  booking_reference: BKG-15220472
                  hotel_id: HTL-77320841
                  check_in_date: '2025-10-03T15:00:00Z'
                  booking_value: 340.0
                  request_type_detail: modify-board-type
                  corporate_account_id: CRP-53615305
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_cbm_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Jennifer Watson from QuickStart Inc. and I need to add a late checkout request to my upcoming booking. My email is jennifer.watson@quickstartinc.com and the booking reference is BKG-28986143. I'd like to request a late checkout until 2 PM if possible. Can you help me with this?
    user_context: |
        You are Jennifer Watson, an employee of QuickStart Inc. contacting support to add a late checkout special request to your upcoming hotel booking BKG-28986143. You want late checkout until 2 PM.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If the agent informs you of a late checkout fee (e.g., $30) and asks for your acceptance or confirmation, agree to the fee.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-28986143
              booking_reference: BKG-28986143
              customer_id: CUS-84729103
              hotel_id: HTL-76382914
              check_in_date: '2025-10-02T18:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              booking_value: '580.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 1
              children_count: 0
              booking_status: confirmed
              corporate_account_id: CRP-77901043
              group_booking_id: null
              modification_history:
                - '2025-09-15T10:00:00Z: room_type: standard_room -> deluxe_room'
                - '2025-09-20T14:30:00Z: check_in_date: 2025-10-01T15:00:00Z -> 2025-10-02T18:00:00Z'
              special_requests: []
              created_at: '2025-09-10T09:30:00Z'
              updated_at: '2025-09-20T14:30:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts:
            - id: INT-00000007
              corporate_account_id: CRP-77901043
              company_name: QuickStart Inc.
              account_tier: small_business
              account_status: active
              contact_name: Michael Torres
              contact_email: mtorres@quickstartinc.com
              contact_phone: +1-408-793-2156
              booking_limit: 5
              credit_limit: '15000.00'
              payment_terms: Net 30
              expiration_date: '2026-06-30T00:00:00Z'
              created_at: '2024-08-01T10:00:00Z'
              updated_at: '2025-01-15T11:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-84729103
              customer_id: CUS-84729103
              email: jennifer.watson@quickstartinc.com
              full_name: Jennifer Watson
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '2340.50'
              total_bookings_count: 8
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-10T09:30:00Z'
              created_at: '2024-03-15T10:00:00Z'
              updated_at: '2025-09-10T09:30:00Z'
          hotel_partner_api_hotels:
            - id: HTL-76382914
              hotel_id: HTL-76382914
              hotel_name: Prestige Tower Hotel
              location: Chicago
              partner_tier: premium
              contact_name: Amanda Richards
              contact_email: frontdesk@prestigetower.com
              contact_phone: +1-312-847-6293
              escalation_contact: manager@prestigetower.com
              amenities:
                - wifi
                - gym
                - restaurant
                - business_center
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2024-05-01T10:00:00Z'
              updated_at: '2024-05-01T10:00:00Z'
          payment_api_transactions: []
          zendesk_tickets:
            - id: TCK-41036971
              subject: General inquiry about booking BKG-28986143
              description: Customer inquiring about booking details and hotel amenities
              status: open
              priority: normal
              type: question
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: ORG-10000006
              tags:
                - booking-inquiry
                - corporate-account
              created_at: '2025-09-30T13:00:00Z'
              updated_at: '2025-09-30T13:00:00Z'
              due_at: null
              booking_reference: BKG-28986143
              hotel_id: HTL-76382914
              check_in_date: '2025-10-02T18:00:00Z'
              booking_value: 580.0
              request_type_detail: other
              corporate_account_id: CRP-77901043
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Jennifer Watson
              email: jennifer.watson@quickstartinc.com
              role: end-user
              organization_id: ORG-10000006
              phone: +1-408-793-2847
              verified: true
              active: true
              created_at: '2024-04-10T10:00:00Z'
              updated_at: '2024-04-10T10:00:00Z'
          zendesk_organizations:
            - id: ORG-10000006
              name: QuickStart Inc.
              domain_names:
                - quickstartinc.com
              details: Small business corporate account
              notes: Small business tier - standard support
              created_at: '2024-04-01T10:00:00Z'
              updated_at: '2024-04-01T10:00:00Z'
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-28986143
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-84729103
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-77901043
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-76382914
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'jennifer.watson@quickstartinc.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-28986143'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Late checkout special request - BKG-28986143
                  description: 'Corporate customer from QuickStart Inc. (CRP-77901043, small_business tier) requesting late checkout for booking BKG-28986143 at premium partner hotel. Check-in: 2025-10-02T18:00:00Z (29 hours from now). Booking value: $580.'
                  status: open
                  priority: high
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - corporate-account
                    - check-in-upcoming
                  booking_reference: BKG-28986143
                  hotel_id: HTL-76382914
                  corporate_account_id: CRP-77901043
                  request_type_detail: add-special-request
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-28986143
                special_requests:
                  - Late checkout until 2 PM - subject to availability
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-28986143
                charge_amount: '30.00'
                reason: late_checkout_fee
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  description: 'Corporate customer from QuickStart Inc. (CRP-77901043, small_business tier) requesting late checkout for booking BKG-28986143 at premium partner hotel. Check-in: 2025-10-02T18:00:00Z. Booking value: $580. Customer requested late checkout until 2 PM. Fee of $30 charged and accepted. Late checkout added to booking special_requests. No modification fee applied as this is a preference addition only. Hotel confirmation not required (premium partner, request made ≥24h in advance).'
                  check_in_date: '2025-10-02T18:00:00Z'
                  booking_value: 580.0
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_cbm_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need some urgent help. I'm Marcus Wheeler from EnterpriseGlobal, email marcus.wheeler@enterpriseglobal.com. I have a booking BKG-88806706 for tonight in Chicago but I really need to switch to a different hotel in the same city. Is there any way to make this happen? It's pretty urgent.
    user_context: |
        You are Marcus Wheeler, a corporate employee at EnterpriseGlobal, contacting support because you urgently need to change your hotel booking to a different property in Chicago. Your check-in is tonight.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        IMPORTANT DECISION:
        - When the agent informs you that changing hotels would require cancellation and you would lose the full $495 booking value (no refund), decide NOT to proceed with the cancellation. Express that losing $495 is too much and you'll just keep the existing booking instead.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-88806706
              customer_id: CUS-42718935
              hotel_id: HTL-79124683
              check_in_date: '2025-10-01T19:00:00Z'
              check_out_date: '2025-10-03T11:00:00Z'
              booking_value: '495.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: CRP-62185188
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T14:30:00Z'
              updated_at: '2025-09-15T14:30:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts:
            - id: INT-00000007
              corporate_account_id: CRP-62185188
              company_name: EnterpriseGlobal
              account_tier: enterprise
              account_status: active
              contact_name: Victoria Hernandez
              contact_email: travel.admin@enterpriseglobal.com
              contact_phone: +1-617-284-9361
              booking_limit: 50
              credit_limit: '200000.00'
              payment_terms: Net 60
              expiration_date: '2026-12-31T00:00:00Z'
              created_at: '2024-03-15T09:00:00Z'
              updated_at: '2025-08-20T11:30:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-42718935
              email: marcus.wheeler@enterpriseglobal.com
              full_name: Marcus Wheeler
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '2500.00'
              total_bookings_count: 5
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T14:30:00Z'
              created_at: '2024-06-10T08:00:00Z'
              updated_at: '2025-09-15T14:30:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-79124683
              hotel_name: Budget Stay Downtown
              location: Chicago
              partner_tier: budget
              contact_name: Patricia Novak
              contact_email: front.desk@budgetstaydowntown.com
              contact_phone: +1-312-729-4821
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions: []
          zendesk_tickets:
            - id: TCK-54051531
              subject: Pre-arrival inquiry - BKG-88806706
              description: Customer inquiring about early check-in options and hotel amenities for upcoming stay
              status: solved
              priority: normal
              type: question
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: null
              tags:
                - pre-arrival
                - inquiry
              created_at: '2025-09-26T10:00:00Z'
              updated_at: '2025-09-26T15:30:00Z'
              due_at: null
              booking_reference: BKG-88806706
              hotel_id: HTL-79124683
              check_in_date: '2025-10-01T19:00:00Z'
              booking_value: 495.0
              request_type_detail: other
              corporate_account_id: CRP-62185188
              group_booking_id: null
              resolution_action: information-provided
              refund_amount: 0.0
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Marcus Wheeler
              email: marcus.wheeler@enterpriseglobal.com
              role: end-user
              organization_id: null
              phone: +1-312-847-6293
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-88806706
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-79124683
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-62185188
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-42718935
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.wheeler@enterpriseglobal.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-88806706'
                orderby: created_at desc
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Hotel change request - BKG-88806706
                  description: 'Corporate customer from EnterpriseGlobal (Enterprise tier) requesting same-day hotel change. Current booking at budget hotel in Chicago. Time until check-in: 6 hours. Customer has been informed that changing hotels requires cancellation and rebooking. Due to budget hotel policy and <24h timing, cancellation would result in 0% refund ($495 forfeited). Enterprise override does not apply (<48h). Customer informed of options.'
                  status: open
                  priority: urgent
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - corporate-account
                    - check-in-today
                  booking_reference: BKG-88806706
                  hotel_id: HTL-79124683
                  corporate_account_id: CRP-62185188
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  description: 'Corporate customer from EnterpriseGlobal (Enterprise tier) requested same-day hotel change. Current booking at budget hotel. Time until check-in: 6 hours. Customer informed that changing hotels requires cancellation and rebooking. Due to budget hotel policy and <24h timing, cancellation would result in 0% refund ($495). Enterprise override does not apply (<48h). Customer decided to keep existing booking to avoid forfeiting $495.'
                  check_in_date: '2025-10-01T19:00:00Z'
                  booking_value: 495.0
                  request_type_detail: other
                  resolution_action: policy-applied-no-action
                  refund_amount: 0
    """

    validate_database(x)


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
              created_at: '2025-09-29T14:30:00Z'
              updated_at: '2025-09-29T14:30:00Z'
              due_at: null
              booking_reference: BKG-75255341
              hotel_id: HTL-58291746
              check_in_date: '2025-10-02T10:00:00Z'
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
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2024-06-01T10:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-75255341
              booking_reference: BKG-75255341
              customer_id: CUS-92741658
              hotel_id: HTL-58291746
              check_in_date: '2025-10-02T10:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
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
              created_at: '2025-09-15T09:00:00Z'
              updated_at: '2025-09-15T09:00:00Z'
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
              expiration_date: '2026-12-31T00:00:00Z'
              created_at: '2024-03-15T10:00:00Z'
              updated_at: '2025-08-20T14:30:00Z'
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
              last_booking_date: '2025-09-15T09:00:00Z'
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-09-15T09:00:00Z'
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
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-75255341'
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
                  check_in_date: '2025-10-02T10:00:00Z'
                  booking_value: 1120.0
                  request_type_detail: cancel-booking
                  corporate_account_id: CRP-03413164
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_ccn_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to cancel a hotel booking. My name is David Martinez, email david.martinez@innovatetech.com, and I'm with InnovateTech Corp. The booking reference is BKG-87403450 for the Grand Skyline Resort. Unfortunately our project has been postponed so we won't need the room anymore. Can you help me with this cancellation?
    user_context: |
        You are David Martinez, an employee at InnovateTech Corp, contacting support to cancel a hotel booking due to a project postponement.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm the cancellation, confirm it.
        - Your goal is to get the booking cancelled and receive information about any refund.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-87403450
              customer_id: CUS-44291038
              hotel_id: HTL-78234519
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '2250.00'
              room_type: presidential_suite
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: CRP-30305486
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:30:00Z'
              updated_at: '2025-09-15T10:30:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts:
            - id: INT-00000007
              corporate_account_id: CRP-30305486
              company_name: InnovateTech Corp
              account_tier: enterprise
              account_status: active
              contact_name: Sarah Johnson
              contact_email: travel@innovatetech.com
              contact_phone: +1-415-783-7742
              booking_limit: 50
              credit_limit: '200000.00'
              payment_terms: Net 60
              expiration_date: '2026-12-31T23:59:59Z'
              created_at: '2024-06-15T09:00:00Z'
              updated_at: '2025-09-01T14:30:00Z'
          crm_api_customer_profiles:
            - id: CRM-00000006
              customer_id: CUS-44291038
              email: david.martinez@innovatetech.com
              full_name: David Martinez
              vip_tier: standard
              loyalty_program_status: bronze
              lifetime_value: '4500.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:30:00Z'
              created_at: '2024-08-12T11:00:00Z'
              updated_at: '2025-09-15T10:30:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-78234519
              hotel_name: Grand Skyline Resort
              location: Los Angeles, CA
              partner_tier: premium
              contact_name: Michael Chen
              contact_email: reservations@grandskyline.com
              contact_phone: +1-310-843-8912
              escalation_contact: operations@grandskyline.com
              amenities:
                - pool
                - spa
                - fitness_center
                - restaurant
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions: []
          zendesk_tickets: []
          zendesk_users:
            - id: USR-29481753
              name: David Martinez
              email: david.martinez@innovatetech.com
              role: end-user
              organization_id: ORG-98234
              phone: +1-415-629-3847
              verified: true
              active: true
              created_at: '2024-08-12T11:00:00Z'
              updated_at: '2024-08-12T11:00:00Z'
          zendesk_organizations:
            - id: ORG-98234
              name: InnovateTech Corp
              domain_names:
                - innovatetech.com
              details: Enterprise corporate travel client
              notes: Enterprise tier - premium support
              created_at: '2024-06-15T09:00:00Z'
              updated_at: '2024-06-15T09:00:00Z'
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-87403450'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-87403450
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-78234519
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-30305486
            - tool: crm_api_check_vip_status
              parameters:
                customer_id: CUS-44291038
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'david.martinez@innovatetech.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation request - BKG-87403450
                  description: 'Enterprise corporate account holder (InnovateTech Corp) requests cancellation of booking BKG-87403450 due to project postponement. Check-in: 2025-10-05. Booking value: $2,250.00. Presidential suite at Grand Skyline Resort. Time until check-in: ~98 hours (≥48h). Enterprise tier cancellation policy applies: 100% refund with $15 service fee retained. Calculated refund: $2,235.00.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-29481753
                  assignee_id: AG-83945
                  tags:
                    - corporate-account
                    - check-in-upcoming
                  booking_reference: BKG-87403450
                  hotel_id: HTL-78234519
                  check_in_date: '2025-10-05T15:00:00Z'
                  booking_value: 2250.0
                  request_type_detail: cancel-booking
                  corporate_account_id: CRP-30305486
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-87403450
                booking_status: cancelled
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-87403450
                refund_amount: '2235.00'
                reason: cancellation
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  tags:
                    - corporate-account
                    - check-in-upcoming
                  resolution_action: refund-full
                  refund_amount: 2235.0
    """

    validate_database(x)


def test_ccn_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to cancel my hotel reservation.
    user_context: |
        You are Mark Henderson, an employee of RegionalSales Inc., contacting support to cancel your upcoming hotel booking BKG-27570596. You simply want to cancel the reservation and receive whatever refund you're entitled to.

        Only if you are asked about your name — tell the agent your name is Mark Henderson.
        Only if you are asked about your company or organization — tell the agent you are with RegionalSales Inc.
        Only if you are asked about your email address — tell the agent it is m.henderson@regionalsales.com.
        Only if you are asked about your booking reference, confirmation number, or reservation number — tell the agent it is BKG-27570596.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Accept the refund amount the agent provides without negotiation.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-27570596
              customer_id: CUS-00000006
              hotel_id: HTL-00012350
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-08T11:00:00Z'
              booking_value: '520.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: CRP-11544796
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T14:30:00Z'
              updated_at: '2025-09-15T14:30:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: m.henderson@regionalsales.com
              full_name: Mark Henderson
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '1840.25'
              total_bookings_count: 4
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T14:30:00Z'
              created_at: '2024-08-12T09:00:00Z'
              updated_at: '2025-09-15T14:30:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00012350
              hotel_name: Comfort Inn Express
              location: Portland
              partner_tier: budget
              contact_name: Jessica Murray
              contact_email: frontdesk@comfortinnexpress.com
              contact_phone: +1-503-482-7391
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          corporate_api_corporate_accounts:
            - id: INT-00000007
              corporate_account_id: CRP-11544796
              company_name: RegionalSales Inc.
              account_tier: mid_market
              account_status: active
              contact_name: Patricia Warren
              contact_email: p.warren@regionalsales.com
              contact_phone: +1-503-847-6218
              booking_limit: 20
              credit_limit: '50000.00'
              payment_terms: Net 45
              expiration_date: '2026-08-31T00:00:00Z'
              created_at: '2024-09-01T10:00:00Z'
              updated_at: '2025-06-15T14:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Mark Henderson
              email: m.henderson@regionalsales.com
              role: end-user
              organization_id: null
              phone: +1-503-629-4817
              verified: true
              active: true
              created_at: '2024-08-12T09:00:00Z'
              updated_at: '2024-08-12T09:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-27570596'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-27570596
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00012350
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-11544796
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'm.henderson@regionalsales.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation request - BKG-27570596
                  description: 'Corporate account employee from RegionalSales Inc. requesting cancellation of booking BKG-27570596. Check-in: 2025-10-06. Hotel: budget tier. Corporate account: mid_market tier (active). Time until check-in: ~122 hours (2-7 day window). Policy: 75% refund minus $15 service fee.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-27570596
                booking_status: cancelled
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-27570596
                refund_amount: '375.00'
                reason: cancellation
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  tags:
                    - corporate-account
                    - check-in-upcoming
                  booking_reference: BKG-27570596
                  hotel_id: HTL-00012350
                  check_in_date: '2025-10-06T15:00:00Z'
                  booking_value: 520.0
                  request_type_detail: cancel-booking
                  corporate_account_id: CRP-11544796
                  resolution_action: refund-partial
                  refund_amount: 375.0
    """

    validate_database(x)


def test_ccn_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to cancel my hotel booking. My name is Marcus Taylor, email marcus.taylor@smallbizsolutions.com. The booking reference is BKG-54310278. This is a corporate booking through SmallBiz Solutions. My travel plans have changed and I no longer need the room. Can you help me cancel this?
    user_context: |
        You are Marcus Taylor, an employee of SmallBiz Solutions contacting support to cancel a corporate hotel booking because your travel plans have changed. You understand there may be cancellation fees involved.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If informed about no refund due to timing, acknowledge and accept the outcome.
    init:
      external_booking_v1:
        data_patch:
          zendesk_users:
            - id: USR-10000007
              name: Marcus Taylor
              email: marcus.taylor@smallbizsolutions.com
              role: end-user
              organization_id: null
              phone: +1-628-517-3842
              verified: true
              active: true
              created_at: '2025-05-15T00:00:00Z'
              updated_at: '2025-05-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-54310278
              customer_id: CUS-00000006
              hotel_id: HTL-00054321
              check_in_date: '2025-10-02T10:00:00Z'
              check_out_date: '2025-10-03T11:00:00Z'
              booking_value: '340.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 1
              children_count: 0
              booking_status: confirmed
              corporate_account_id: CRP-57192856
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00054321
              hotel_name: Harbor View Business Hotel
              location: San Francisco
              partner_tier: standard
              contact_name: Jennifer Reyes
              contact_email: reservations@harborviewbh.com
              contact_phone: +1-415-892-6734
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - business_center
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: marcus.taylor@smallbizsolutions.com
              full_name: Marcus Taylor
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '340.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-05-15T00:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          corporate_api_corporate_accounts:
            - id: INT-00000007
              corporate_account_id: CRP-57192856
              company_name: SmallBiz Solutions
              account_tier: small_business
              account_status: active
              contact_name: Marcus Taylor
              contact_email: marcus.taylor@smallbizsolutions.com
              contact_phone: +1-628-517-3842
              booking_limit: 5
              credit_limit: '10000.00'
              payment_terms: Net 30
              expiration_date: '2026-12-31T00:00:00Z'
              created_at: '2024-08-15T09:00:00Z'
              updated_at: '2025-08-15T09:00:00Z'
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.taylor@smallbizsolutions.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-54310278'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-54310278
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00054321
            - tool: crm_api_check_vip_status
              parameters:
                customer_id: CUS-00000006
            - tool: corporate_api_get_account_details
              parameters:
                corporate_account_id: CRP-57192856
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation request - BKG-54310278
                  description: 'Corporate customer from SmallBiz Solutions (CRP-57192856) requests cancellation of booking BKG-54310278 due to changed travel plans. Check-in: 2025-10-02. Hotel: standard partner tier. Corporate tier: small_business. Customer VIP tier: standard.'
                  status: open
                  priority: high
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - corporate-account
                    - check-in-24h
                  booking_reference: BKG-54310278
                  hotel_id: HTL-00054321
                  corporate_account_id: CRP-57192856
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-54310278
                booking_status: cancelled
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  check_in_date: '2025-10-02T10:00:00Z'
                  booking_value: 340.0
                  request_type_detail: cancel-booking
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_crf_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I need to cancel my hotel booking. My name is Marcus Wellington, email marcus.wellington@outlook.com, and the booking reference is BKG-42258313. Please process the cancellation for me.
    user_context: |
        You are Marcus Wellington, a customer who needs to cancel your hotel booking at The Regal Towers. Your check-in is today and you understand you may be canceling on short notice. Your goal is to have the booking cancelled.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Accept the cancellation outcome even if informed there is no refund due to the timing.
    init:
      external_booking_v1:
        data_patch:
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: marcus.wellington@outlook.com
              full_name: Marcus Wellington
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '1850.75'
              total_bookings_count: 4
              preferences:
                - quiet room
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2024-06-10T00:00:00Z'
              updated_at: '2025-08-15T12:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-42258313
              customer_id: CUS-00000006
              hotel_id: HTL-00056789
              check_in_date: '2025-10-01T18:00:00Z'
              check_out_date: '2025-10-03T11:00:00Z'
              booking_value: '540.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00056789
              hotel_name: The Regal Towers
              location: Chicago
              partner_tier: premium
              contact_name: Victoria Chen
              contact_email: reservations@regaltowers.com
              contact_phone: +1-312-847-2956
              escalation_contact: manager@regaltowers.com
              amenities:
                - pool
                - gym
                - spa
                - restaurant
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Wellington
              email: marcus.wellington@outlook.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-312-485-7291
              verified: true
              active: true
              created_at: '2024-06-10T00:00:00Z'
              updated_at: '2024-06-10T00:00:00Z'
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
            - tool: crm_api_get_customer_profile
              parameters:
                email: marcus.wellington@outlook.com
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-42258313
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00056789
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.wellington@outlook.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-42258313'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation request - BKG-42258313
                  description: 'Customer requests cancellation of booking BKG-42258313. Hotel: premium partner. Check-in: 2025-10-01T18:00:00Z (today). Time until check-in: 5 hours (<24h). Customer vip_tier: standard. Per premium hotel cancellation policy with <24h notice, 0% refund applies. Processing cancellation.'
                  status: open
                  priority: urgent
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-42258313
                booking_status: cancelled
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  tags:
                    - b2c-customer
                    - check-in-today
                  booking_reference: BKG-42258313
                  hotel_id: HTL-00056789
                  check_in_date: '2025-10-01T18:00:00Z'
                  booking_value: 540.0
                  request_type_detail: cancel-booking
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_crf_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I need to cancel my hotel booking. The booking reference is BKG-83503056. My name is Marcus Wellington and my email is marcus.wellington@promail.net. Please process this cancellation for me.
    user_context: |
        You are Marcus Wellington, a frequent business traveler contacting StayBridge support to cancel your upcoming hotel reservation at The Kensington Suites in Boston. You simply want the cancellation processed.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent confirms the cancellation and refund details, acknowledge and thank them.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-83503056
              customer_id: CUS-00000006
              hotel_id: HTL-00054321
              check_in_date: '2025-10-02T14:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              booking_value: '890.00'
              room_type: executive_suite
              board_type: full_board
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T09:30:00Z'
              updated_at: '2025-09-15T09:30:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: marcus.wellington@promail.net
              full_name: Marcus Wellington
              vip_tier: platinum
              loyalty_program_status: active
              lifetime_value: '28540.75'
              total_bookings_count: 42
              preferences:
                - executive suite
                - quiet floor
              special_notes:
                - frequent business traveler
              complaint_count: 0
              last_booking_date: '2025-09-15T09:30:00Z'
              created_at: '2022-03-10T08:00:00Z'
              updated_at: '2025-09-15T09:30:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00054321
              hotel_name: The Kensington Suites
              location: Boston
              partner_tier: premium
              contact_name: Victoria Harrington
              contact_email: frontdesk@kensingtonsuites.com
              contact_phone: +1-617-428-3150
              escalation_contact: manager@kensingtonsuites.com
              amenities:
                - spa
                - gym
                - restaurant
                - concierge
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2024-05-12T10:00:00Z'
              updated_at: '2024-05-12T10:00:00Z'
          payment_api_transactions: []
          zendesk_tickets: []
          zendesk_users:
            - id: USR-10000007
              name: Marcus Wellington
              email: marcus.wellington@promail.net
              role: end-user
              organization_id: null
              phone: +1-617-924-7183
              verified: true
              active: true
              created_at: '2022-03-10T08:00:00Z'
              updated_at: '2022-03-10T08:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-83503056
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00054321
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-83503056'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.wellington@promail.net'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation request - BKG-83503056
                  description: 'Customer requests cancellation of booking BKG-83503056 at premium partner hotel. Check-in: 2025-10-02T14:00:00Z. Time until check-in: 25 hours. Note: Customer is platinum VIP tier - full refund with service fee waived applies per Section 4.2.3.'
                  status: open
                  priority: high
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-83503056
                booking_status: cancelled
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-83503056
                refund_amount: '890.00'
                reason: cancellation
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                  booking_reference: BKG-83503056
                  hotel_id: HTL-00054321
                  check_in_date: '2025-10-02T14:00:00Z'
                  booking_value: 890.0
                  request_type_detail: cancel-booking
                  resolution_action: refund-full
                  refund_amount: 890.0
    """

    validate_database(x)


def test_crf_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to cancel my hotel booking. My booking reference is BKG-22680182 and my email is marcus.webb@protonmail.com. Please process the cancellation for me.
    user_context: |
        You are Marcus Webb, a customer who needs to cancel your hotel booking that's scheduled for today. You understand you're cancelling on short notice.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent informs you that no refund is available due to the short notice, acknowledge this and accept the cancellation without the refund.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-22680182
              customer_id: CUS-00000006
              hotel_id: HTL-00012350
              check_in_date: '2025-10-01T20:00:00Z'
              check_out_date: '2025-10-03T11:00:00Z'
              booking_value: '340.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 1
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-18T14:30:00Z'
              updated_at: '2025-09-18T14:30:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: marcus.webb@protonmail.com
              full_name: Marcus Webb
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '680.25'
              total_bookings_count: 2
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-18T14:30:00Z'
              created_at: '2025-06-10T09:00:00Z'
              updated_at: '2025-09-18T14:30:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00012350
              hotel_name: Harbor View Hotel
              location: Seattle
              partner_tier: standard
              contact_name: Angela Morrison
              contact_email: reservations@harborviewhotel.com
              contact_phone: +1-206-847-3291
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - business_center
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Webb
              email: marcus.webb@protonmail.com
              role: end-user
              organization_id: null
              phone: +1-206-482-7361
              verified: true
              active: true
              created_at: '2025-06-10T09:00:00Z'
              updated_at: '2025-06-10T09:00:00Z'
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
                booking_reference: BKG-22680182
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00012350
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.webb@protonmail.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-22680182'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation request - BKG-22680182
                  description: 'Customer requests cancellation for booking BKG-22680182. Check-in today 2025-10-01 at 20:00 UTC. Time until check-in: 7 hours (<24 hours). Customer vip_tier: standard. Hotel partner_tier: standard. Per cancellation policy, cancellations within 24 hours of check-in at standard hotels result in 0% refund.'
                  status: open
                  priority: urgent
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-today
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-22680182
                booking_status: cancelled
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  booking_reference: BKG-22680182
                  hotel_id: HTL-00012350
                  check_in_date: '2025-10-01T20:00:00Z'
                  booking_value: 340.0
                  request_type_detail: cancel-booking
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


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
              created_at: '2025-09-28T13:00:00Z'
              updated_at: '2025-09-28T13:00:00Z'
              due_at: null
              booking_reference: BKG-42253584
              hotel_id: HTL-91827364
              check_in_date: '2025-10-02T15:00:00Z'
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
              created_at: '2024-08-20T10:00:00Z'
              updated_at: '2025-09-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-42253584
              booking_reference: BKG-42253584
              customer_id: CUS-55102938
              hotel_id: HTL-91827364
              check_in_date: '2025-10-02T15:00:00Z'
              check_out_date: '2025-10-04T11:00:00Z'
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
              created_at: '2025-09-15T14:30:00Z'
              updated_at: '2025-09-15T14:30:00Z'
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
              last_booking_date: '2025-09-15T14:30:00Z'
              created_at: '2024-08-20T10:00:00Z'
              updated_at: '2025-09-15T14:30:00Z'
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
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
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
              created_at: '2025-09-15T14:30:00Z'
              updated_at: '2025-09-15T14:30:00Z'
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-42253584'
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
                  check_in_date: '2025-10-02T15:00:00Z'
                  booking_value: 410.0
                  request_type_detail: cancel-booking
                  resolution_action: refund-partial
                  refund_amount: 190.0
    """

    validate_database(x)


def test_crf_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to cancel my upcoming hotel reservation.
    user_context: |
        You are Marcus Reilly, a customer who needs to cancel your hotel booking at Central Park Suites in Chicago. You booked a suite with half board for 2 adults and 1 child, checking in on October 3rd.

        Only if you are asked about your booking reference or confirmation number — tell the agent it is BKG-81829922.
        Only if you are asked about your email address — tell the agent it is marcus.reilly@protonmail.net.

        If asked to confirm the cancellation or accept the refund terms (refund with service fee deduction), confirm that you want to proceed.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-81829922
              booking_reference: BKG-81829922
              customer_id: CUS-70841293
              hotel_id: HTL-70841293
              check_in_date: '2025-10-03T14:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              booking_value: '580.00'
              room_type: suite
              board_type: half_board
              adults_count: 2
              children_count: 1
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-70841293
              hotel_name: Central Park Suites
              location: Chicago
              partner_tier: standard
              contact_name: Jennifer Walsh
              contact_email: reservations@centralparksuites.com
              contact_phone: +1-312-847-2951
              escalation_contact: null
              amenities:
                - wifi
                - gym
                - business_center
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-70841293
              customer_id: CUS-70841293
              email: marcus.reilly@protonmail.net
              full_name: Marcus Reilly
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '580.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          zendesk_users:
            - id: USR-70841293
              name: Marcus Reilly
              email: marcus.reilly@protonmail.net
              role: end-user
              organization_id: null
              phone: +1-312-598-4207
              verified: true
              active: true
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          zendesk_tickets:
            - id: TCK-99590010
              subject: Rate inquiry - BKG-81829922
              description: Customer inquiring about rate details for booking BKG-81829922
              status: solved
              priority: normal
              type: question
              requester_id: USR-70841293
              assignee_id: USR-10000002
              organization_id: null
              tags:
                - billing
                - inquiry
              created_at: '2025-09-21T13:00:00Z'
              updated_at: '2025-09-22T10:00:00Z'
              due_at: null
              booking_reference: BKG-81829922
              hotel_id: HTL-70841293
              check_in_date: '2025-10-03T14:00:00Z'
              booking_value: 580.0
              request_type_detail: billing-inquiry
              corporate_account_id: null
              group_booking_id: null
              resolution_action: information-provided
              refund_amount: null
              escalation_reason: null
          payment_api_transactions:
            - id: TXN-70841293
              transaction_id: TXN-70841293
              booking_reference: BKG-81829922
              customer_id: CUS-70841293
              amount: '580.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 4821
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
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
                booking_reference: BKG-81829922
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-70841293
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-70841293
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.reilly@protonmail.net'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-81829922'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation request - BKG-81829922
                  description: 'Customer requests cancellation of booking BKG-81829922. Standard tier customer at standard tier hotel. Booking value: $580.00. Check-in: 2025-10-03. Time until check-in: 49 hours (≥48h). Eligible for 100% refund minus $15 service fee = $565.00 refund.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-70841293
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-81829922
                  hotel_id: HTL-70841293
                  check_in_date: '2025-10-03T14:00:00Z'
                  booking_value: 580.0
                  request_type_detail: cancel-booking
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-81829922
                booking_status: cancelled
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-81829922
                refund_amount: '565.00'
                reason: cancellation
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  resolution_action: refund-full
                  refund_amount: 565.0
    """

    validate_database(x)


def test_crf_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I need to cancel my upcoming hotel reservation. My name is Victoria Chen and my email is victoria.chen@westmail.net. The booking reference is BKG-94396907. Please let me know what I need to do.
    user_context: |
        You are Victoria Chen, a platinum loyalty member contacting StayBridge support to cancel your upcoming hotel booking BKG-94396907. You have a family trip planned but circumstances have changed and you need to cancel.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm the cancellation, confirm that yes, you want to proceed with cancelling the booking.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-94396907
              customer_id: CUS-00000006
              hotel_id: HTL-00052891
              check_in_date: '2025-10-02T16:00:00Z'
              check_out_date: '2025-10-04T11:00:00Z'
              booking_value: '720.00'
              room_type: executive_suite
              board_type: full_board
              adults_count: 2
              children_count: 2
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T09:30:00Z'
              updated_at: '2025-09-15T09:30:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: victoria.chen@westmail.net
              full_name: Victoria Chen
              vip_tier: platinum
              loyalty_program_status: platinum-member
              lifetime_value: '28750.60'
              total_bookings_count: 42
              preferences:
                - quiet room
                - high floor
              special_notes:
                - values personalized service
              complaint_count: 0
              last_booking_date: '2025-09-15T09:30:00Z'
              created_at: '2022-03-10T14:00:00Z'
              updated_at: '2025-09-15T09:30:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00052891
              hotel_name: Riverside Comfort Inn
              location: Chicago
              partner_tier: standard
              contact_name: Martin Howard
              contact_email: reservations@riversidecomfort.com
              contact_phone: +1-312-847-2935
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - breakfast
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Victoria Chen
              email: victoria.chen@westmail.net
              role: end-user
              organization_id: null
              phone: +1-773-582-4691
              verified: true
              active: true
              created_at: '2024-09-05T00:00:00Z'
              updated_at: '2024-09-05T00:00:00Z'
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
                booking_reference: BKG-94396907
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00052891
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'victoria.chen@westmail.net'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-94396907'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation request - BKG-94396907
                  description: Customer requests cancellation for booking BKG-94396907. Platinum customer at standard hotel, 27 hours before check-in. Platinum exception applies - 100% refund with service fee waived.
                  status: open
                  priority: high
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                  booking_reference: BKG-94396907
                  hotel_id: HTL-00052891
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-94396907
                booking_status: cancelled
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-94396907
                refund_amount: '720.00'
                reason: cancellation
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  request_type_detail: cancel-booking
                  resolution_action: refund-full
                  refund_amount: 720.0
                  booking_value: 720.0
                  check_in_date: '2025-10-02T16:00:00Z'
    """

    validate_database(x)


def test_crf_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to cancel my hotel booking. My name is Marcus Weber, email marcus.weber@gmail.com, and the booking reference is BKG-59255562. Please process the cancellation for me.
    user_context: |
        You are Marcus Weber, a customer contacting StayBridge support to cancel your hotel booking BKG-59255562. Your check-in is scheduled for today.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Accept the cancellation outcome, even if no refund is provided due to the timing.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-59255562
              customer_id: CUS-00087654
              hotel_id: HTL-00098765
              check_in_date: '2025-10-01T16:00:00Z'
              check_out_date: '2025-10-02T11:00:00Z'
              booking_value: '195.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 1
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-18T14:30:00Z'
              updated_at: '2025-09-18T14:30:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00098765
              hotel_name: Riverside Economy Suites
              location: Chicago
              partner_tier: budget
              contact_name: Jennifer Walsh
              contact_email: info@riversideeconomy.com
              contact_phone: +1-312-847-5923
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: false
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00087654
              customer_id: CUS-00087654
              email: marcus.weber@gmail.com
              full_name: Marcus Weber
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '195.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-18T14:30:00Z'
              created_at: '2025-09-10T09:15:00Z'
              updated_at: '2025-09-18T14:30:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Weber
              email: marcus.weber@gmail.com
              role: end-user
              organization_id: null
              phone: +1-847-392-6841
              verified: true
              active: true
              created_at: '2025-09-10T09:15:00Z'
              updated_at: '2025-09-10T09:15:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          payment_api_transactions:
            - id: TXN-00000008
              transaction_id: TXN-00000008
              booking_reference: BKG-59255562
              customer_id: CUS-00087654
              amount: '195.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 3847
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-18T14:30:00Z'
              updated_at: '2025-09-18T14:30:00Z'
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-59255562
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00098765
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00087654
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.weber@gmail.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-59255562'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation request - BKG-59255562
                  description: Customer requested cancellation of booking BKG-59255562. Check-in date is today (2025-10-01). Hotel is budget tier. Customer is standard tier. Time until check-in is less than 24 hours, which results in 0% refund per budget hotel cancellation policy.
                  status: open
                  priority: urgent
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-today
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-59255562
                booking_status: cancelled
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  booking_reference: BKG-59255562
                  hotel_id: HTL-00098765
                  check_in_date: '2025-10-01T16:00:00Z'
                  booking_value: 195.0
                  request_type_detail: cancel-booking
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_crf_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to cancel my hotel booking. The booking reference is BKG-58815371. My name is Marcus Chen and my email is marcus.chen@webmail.net. I believe I reached out about this a few days ago but wasn't able to actually cancel at that time. I need to go ahead and cancel now.
    user_context: |
        You are Marcus Chen, a customer who needs to cancel your hotel booking BKG-58815371. You previously inquired about canceling this booking about a week ago but did not complete the cancellation at that time. Now you definitely need to cancel.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent informs you that no refund is available due to the cancellation timing, acknowledge this and confirm you still want to proceed with the cancellation.
        - You may express mild disappointment about the no-refund policy, but do not argue or demand exceptions.
    init:
      external_booking_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-47321046
              subject: Cancellation request for booking BKG-58815371
              description: Customer inquiring about cancelling their upcoming reservation
              status: solved
              priority: normal
              type: task
              requester_id: USR-72149385
              assignee_id: AG-83945
              organization_id: null
              tags:
                - cancellation
                - b2c-customer
              created_at: '2025-09-25T10:30:00Z'
              updated_at: '2025-09-25T14:00:00Z'
              due_at: null
              booking_reference: BKG-58815371
              hotel_id: HTL-47291836
              check_in_date: '2025-10-02T12:00:00Z'
              booking_value: 230.0
              request_type_detail: cancel-booking
              corporate_account_id: null
              group_booking_id: null
              resolution_action: information-provided
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-72149385
              name: Marcus Chen
              email: marcus.chen@webmail.net
              role: end-user
              organization_id: null
              phone: +1-312-459-8721
              verified: true
              active: true
              created_at: '2024-06-20T08:00:00Z'
              updated_at: '2025-09-15T09:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-58815371
              booking_reference: BKG-58815371
              customer_id: CUS-72149385
              hotel_id: HTL-47291836
              check_in_date: '2025-10-02T12:00:00Z'
              check_out_date: '2025-10-03T11:00:00Z'
              booking_value: '230.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T09:00:00Z'
              updated_at: '2025-09-15T09:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-72149385
              customer_id: CUS-72149385
              email: marcus.chen@webmail.net
              full_name: Marcus Chen
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '856.75'
              total_bookings_count: 4
              preferences:
                - early check-in
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T09:00:00Z'
              created_at: '2024-06-20T08:00:00Z'
              updated_at: '2025-09-15T09:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-47291836
              hotel_id: HTL-47291836
              hotel_name: Central Budget Suites
              location: Chicago
              partner_tier: budget
              contact_name: Jennifer Walsh
              contact_email: reservations@centralbudgetsuites.com
              contact_phone: +1-312-847-6293
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2024-03-15T10:00:00Z'
              updated_at: '2024-03-15T10:00:00Z'
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-58815371'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-47321046
                item:
                  status: open
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-58815371
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-72149385
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-47291836
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-58815371
                booking_status: cancelled
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-47321046
                item:
                  status: solved
                  priority: high
                  type: task
                  tags:
                    - b2c-customer
                    - check-in-24h
                  booking_reference: BKG-58815371
                  hotel_id: HTL-47291836
                  check_in_date: '2025-10-02T12:00:00Z'
                  booking_value: 230.0
                  request_type_detail: cancel-booking
                  resolution_action: modification-completed
                  refund_amount: 0.0
    """

    validate_database(x)


def test_crf_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to cancel my hotel booking. My name is Marcus Riley and my email is marcus.riley@protonmail.com. The booking reference is BKG-96325953. Something came up and I won't be able to make it tomorrow.
    user_context: |
        You are Marcus Riley, a customer who needs to cancel your hotel booking due to a change in plans. You booked a room at Harbor View Budget Inn in Seattle for tomorrow.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL GUIDANCE:
        - If the agent asks you to confirm you want to proceed with the cancellation, confirm yes.
        - If the agent informs you about a partial refund or cancellation fee, accept it without dispute - you understand there may be fees for cancelling close to check-in.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-96325953
              customer_id: CUS-00000006
              hotel_id: HTL-00056789
              check_in_date: '2025-10-02T18:00:00Z'
              check_out_date: '2025-10-03T11:00:00Z'
              booking_value: '275.00'
              room_type: deluxe_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 1
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00056789
              hotel_name: Harbor View Budget Inn
              location: Seattle
              partner_tier: budget
              contact_name: Rachel Morrison
              contact_email: manager@harborviewbudget.com
              contact_phone: +1-206-847-3921
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: marcus.riley@protonmail.com
              full_name: Marcus Riley
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '825.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-03-10T10:00:00Z'
              updated_at: '2025-09-15T12:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Riley
              email: marcus.riley@protonmail.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-206-528-4782
              verified: true
              active: true
              created_at: '2025-03-10T10:00:00Z'
              updated_at: '2025-03-10T10:00:00Z'
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
                booking_reference: BKG-96325953
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00056789
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.riley@protonmail.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-96325953'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation request - BKG-96325953
                  description: 'Customer requests cancellation of booking BKG-96325953. Budget partner hotel, standard customer. Check-in: 2025-10-02T18:00:00Z. Time until check-in: 29 hours (24-48h window). Per budget tier 7-day policy: 50% refund minus $15 service fee. Calculated refund amount: $122.50.'
                  status: open
                  priority: high
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-96325953
                  hotel_id: HTL-00056789
                  check_in_date: '2025-10-02T18:00:00Z'
                  booking_value: 275.0
                  request_type_detail: cancel-booking
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-96325953
                booking_status: cancelled
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-96325953
                refund_amount: '122.50'
                reason: cancellation
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  resolution_action: refund-partial
                  refund_amount: 122.5
    """

    validate_database(x)


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
              check_in_date: '2025-10-10T14:00:00Z'
              check_out_date: '2025-10-11T11:00:00Z'
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
              created_at: '2025-09-20T10:00:00Z'
              updated_at: '2025-09-20T10:00:00Z'
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
              last_booking_date: '2025-09-20T10:00:00Z'
              created_at: '2025-06-15T09:00:00Z'
              updated_at: '2025-09-20T10:00:00Z'
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
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
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
              created_at: '2025-06-15T09:00:00Z'
              updated_at: '2025-06-15T09:00:00Z'
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
                filter: booking_reference eq 'BKG-00479748'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.wellington@proton.me'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation request - BKG-00479748
                  description: 'Customer requests cancellation of booking BKG-00479748. Check-in date: 2025-10-10. Booking value: $185.'
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
                  check_in_date: '2025-10-10T14:00:00Z'
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
                  description: 'Customer requests cancellation of booking BKG-00479748. Check-in date: 2025-10-10. Booking value: $185. Customer tier: standard. Hotel tier: budget (7-day cancellation policy). Time until check-in: ~217 hours (≥7 days). Policy applied: 100% refund with $15 service fee retained. Refund amount: $170.00. Cancellation processed successfully. Refund transaction: TXN-00000008.'
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  resolution_action: refund-full
                  refund_amount: 170.0
    """

    validate_database(x)


def test_crf_015(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to cancel my hotel reservation.
    user_context: |
        You are Marcus Reyes, a platinum tier loyalty customer contacting StayBridge support to cancel your upcoming hotel booking. You want to cancel your reservation at the Downtown Budget Hotel scheduled for October 3rd.

        Only if you are asked about your name — tell the agent your name is Marcus Reyes.
        Only if you are asked about your email or email address — tell the agent it is marcus.reyes@gmail.com.
        Only if you are asked about your booking reference, confirmation number, or reservation number — provide BKG-01624565.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm the cancellation, confirm you want to proceed.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-01624565
              customer_id: CUS-00000006
              hotel_id: HTL-00012347
              check_in_date: '2025-10-03T14:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              booking_value: '445.00'
              room_type: suite
              board_type: half_board
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T09:30:00Z'
              updated_at: '2025-09-15T09:30:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: marcus.reyes@gmail.com
              full_name: Marcus Reyes
              vip_tier: platinum
              loyalty_program_status: active
              lifetime_value: '28750.00'
              total_bookings_count: 42
              preferences:
                - suite
                - quiet room
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T09:30:00Z'
              created_at: '2022-03-15T10:00:00Z'
              updated_at: '2025-09-15T09:30:00Z'
          hotel_partner_api_hotels: []
          payment_api_transactions: []
          zendesk_tickets:
            - id: TCK-06098358
              subject: Date inquiry - BKG-01624565
              description: Customer inquiry regarding check-in time confirmation for upcoming reservation
              status: solved
              priority: normal
              type: question
              requester_id: USR-10000007
              assignee_id: USR-10000002
              organization_id: null
              tags:
                - inquiry
                - date-question
              created_at: '2025-09-23T11:15:00Z'
              updated_at: '2025-09-23T14:30:00Z'
              due_at: null
              booking_reference: BKG-01624565
              hotel_id: HTL-00012347
              check_in_date: '2025-10-03T14:00:00Z'
              booking_value: 445.0
              request_type_detail: other
              corporate_account_id: null
              group_booking_id: null
              resolution_action: information-provided
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Marcus Reyes
              email: marcus.reyes@gmail.com
              role: end-user
              organization_id: null
              phone: +1-718-429-7823
              verified: true
              active: true
              created_at: '2025-08-10T14:20:00Z'
              updated_at: '2025-08-10T14:20:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          lookup_bookings: []
          lookup_hotels: []
          lookup_group_bookings: []
          lookup_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-01624565
            - tool: crm_api_check_vip_status
              parameters:
                customer_id: CUS-00000006
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00012347
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-01624565'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.reyes@gmail.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation request - BKG-01624565
                  description: 'Customer requesting cancellation of booking BKG-01624565. Platinum tier VIP customer. Check-in: 2025-10-03 (49 hours from now). Hotel partner tier: budget. Per Platinum Customer Exception (Section 4.2.3), customer is eligible for 100% refund with service fee waived since cancellation is ≥24 hours before check-in.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                  booking_reference: BKG-01624565
                  hotel_id: HTL-00012347
                  check_in_date: '2025-10-03T14:00:00Z'
                  booking_value: 445.0
                  request_type_detail: cancel-booking
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-01624565
                booking_status: cancelled
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-01624565
                refund_amount: '445.00'
                reason: cancellation
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  resolution_action: refund-full
                  refund_amount: 445.0
    """

    validate_database(x)


def test_crf_016(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I need to cancel my hotel booking due to an emergency that came up. My name is Patricia Fernandez, email patricia.fernandez@outlook.com. The booking reference is BKG-41687849. I know the booking was non-refundable, but given the situation, is there any possibility of getting a refund?
    user_context: |
        You are Patricia Fernandez, a customer who needs to cancel a hotel booking due to an unexpected emergency. You are hoping to get some sort of refund even though you booked a non-refundable rate.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If the agent explains the refund terms and asks for confirmation to proceed with cancellation, confirm that you want to proceed.
    init:
      external_booking_v1:
        data_patch:
          zendesk_users:
            - id: USR-10000007
              name: Patricia Fernandez
              email: patricia.fernandez@outlook.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-832-471-9263
              verified: true
              active: true
              created_at: '2024-09-15T00:00:00Z'
              updated_at: '2024-09-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-41687849
              customer_id: CUS-72849103
              hotel_id: HTL-89324716
              check_in_date: '2025-10-12T14:00:00Z'
              check_out_date: '2025-10-13T11:00:00Z'
              booking_value: '260.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-20T10:00:00Z'
              updated_at: '2025-09-20T10:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-72849103
              email: patricia.fernandez@outlook.com
              full_name: Patricia Fernandez
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '780.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-20T10:00:00Z'
              created_at: '2024-09-15T00:00:00Z'
              updated_at: '2025-09-20T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-89324716
              hotel_name: Harbor View Budget Inn
              location: San Francisco
              partner_tier: budget
              contact_name: Kevin O'Brien
              contact_email: front.desk@harborviewbudget.com
              contact_phone: +1-415-672-8134
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          corporate_api_corporate_accounts: []
          payment_api_transactions:
            - id: TXN-00000008
              transaction_id: TXN-00000008
              booking_reference: BKG-41687849
              customer_id: CUS-72849103
              amount: '260.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7821
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-20T10:00:00Z'
              updated_at: '2025-09-20T10:00:00Z'
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'patricia.fernandez@outlook.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-41687849'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-41687849
            - tool: crm_api_check_vip_status
              parameters:
                customer_id: CUS-72849103
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-89324716
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation request - BKG-41687849
                  description: 'Customer requested cancellation due to emergency. Booking at budget tier hotel with check-in 2025-10-12 (11 days away). Standard VIP tier customer. Refund eligible: $245 (100% minus $15 service fee).'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-41687849
                  hotel_id: HTL-89324716
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-41687849
                booking_status: cancelled
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-41687849
                refund_amount: '245.00'
                reason: cancellation
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  description: 'Customer requested cancellation due to emergency. Booking at budget tier hotel with check-in 2025-10-12 (11 days away, ≥7 days). Standard VIP tier customer. Applied budget tier 7-day policy: 100% refund minus $15 service fee. Cancellation processed, booking status updated to cancelled. Refund of $245 processed successfully.'
                  check_in_date: '2025-10-12T14:00:00Z'
                  booking_value: 260.0
                  request_type_detail: cancel-booking
                  resolution_action: refund-full
                  refund_amount: 245.0
    """

    validate_database(x)


def test_crf_017(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to cancel my booking BKG-91216558. My name is Victoria Sterling and my email is victoria.sterling@protonmail.com. I actually contacted support about this yesterday but I don't think it was processed. Can you please cancel this reservation for me?
    user_context: |
        You are Victoria Sterling, a platinum-tier customer requesting to cancel your hotel booking. You contacted support yesterday about the same cancellation but it wasn't completed, and you're following up now.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm the cancellation, confirm yes.
        - If informed there is no refund due to timing, you may express mild disappointment but accept the outcome politely.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-91216558
              booking_reference: BKG-91216558
              customer_id: CUS-48271635
              hotel_id: HTL-73928461
              check_in_date: '2025-10-01T17:00:00Z'
              check_out_date: '2025-10-03T11:00:00Z'
              booking_value: '950.00'
              room_type: presidential_suite
              board_type: all_inclusive
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          zendesk_tickets:
            - id: '52398680'
              subject: Cancellation request for booking BKG-91216558
              description: Customer requests to cancel their upcoming reservation
              status: open
              priority: normal
              type: task
              requester_id: USR-48271635
              assignee_id: AG-83945
              organization_id: null
              tags:
                - cancellation
              created_at: '2025-09-30T10:00:00Z'
              updated_at: '2025-09-30T10:00:00Z'
              due_at: null
              booking_reference: BKG-91216558
              hotel_id: HTL-73928461
              check_in_date: '2025-10-01T17:00:00Z'
              booking_value: 950.0
              request_type_detail: cancel-booking
              corporate_account_id: null
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          crm_api_customer_profiles:
            - id: CUS-48271635
              customer_id: CUS-48271635
              email: victoria.sterling@protonmail.com
              full_name: Victoria Sterling
              vip_tier: platinum
              loyalty_program_status: platinum-elite
              lifetime_value: '28500.00'
              total_bookings_count: 42
              preferences:
                - quiet room
                - high floor
              special_notes:
                - prefers late check-out when available
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2022-06-15T00:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-73928461
              hotel_id: HTL-73928461
              hotel_name: Harbor View Inn
              location: San Francisco
              partner_tier: standard
              contact_name: Marcus Williams
              contact_email: contact@harborviewinn.com
              contact_phone: +1-415-628-3917
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions:
            - id: TXN-48271635
              transaction_id: TXN-48271635
              booking_reference: BKG-91216558
              customer_id: CUS-48271635
              amount: '950.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7823
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          zendesk_users:
            - id: USR-48271635
              name: Victoria Sterling
              email: victoria.sterling@protonmail.com
              role: end-user
              organization_id: null
              phone: null
              verified: true
              active: true
              created_at: '2022-06-15T00:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-91216558
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-91216558'
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-48271635
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-73928461
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-91216558
                booking_status: cancelled
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '52398680'
                item:
                  status: solved
                  priority: urgent
                  type: task
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-today
                    - repeat-issue
                    - vip-customer
                  description: 'Cancellation request for platinum customer. Check-in: 2025-10-01 (today, 4 hours away). Hotel: standard tier. Platinum exception does NOT apply (requires ≥24h, only 4h until check-in). Standard hotel <24h policy: 0% refund. Cancellation processed, booking status updated to cancelled. No refund issued.'
                  booking_reference: BKG-91216558
                  hotel_id: HTL-73928461
                  check_in_date: '2025-10-01T17:00:00Z'
                  booking_value: 950.0
                  request_type_detail: cancel-booking
                  resolution_action: modification-completed
                  refund_amount: 0.0
    """

    validate_database(x)


def test_crf_018(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, my name is Margaret Hartley and I have a booking coming up at The Riverside Grand Hotel. My booking reference is BKG-00257872 and my email is margaret.hartley@outlook.com. I'm not sure yet if I'll need to cancel, but I wanted to understand what my options would be and how much I'd get back if I did decide to cancel. Can you help me understand the cancellation policy for my booking?
    user_context: |
        You are Margaret Hartley, a VIP customer contacting support to inquire about cancellation options for your upcoming hotel booking. You are NOT requesting to cancel - you simply want to understand what your options and potential refund would be if you decided to cancel later.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        IMPORTANT:
        - If the agent asks if you want to proceed with cancellation, politely decline - you just wanted the information for now.
        - You are only seeking information about the cancellation policy and potential refund amount, not actually canceling.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00257872
              booking_reference: BKG-00257872
              customer_id: CUS-74829163
              hotel_id: HTL-83926471
              check_in_date: '2025-10-15T14:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '380.00'
              room_type: deluxe_room
              board_type: half_board
              adults_count: 2
              children_count: 1
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-74829163
              customer_id: CUS-74829163
              email: margaret.hartley@outlook.com
              full_name: Margaret Hartley
              vip_tier: vip
              loyalty_program_status: active
              lifetime_value: '8750.50'
              total_bookings_count: 14
              preferences:
                - quiet room
                - high floor
              special_notes:
                - prefers email communication
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-03-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-83926471
              hotel_id: HTL-83926471
              hotel_name: The Riverside Grand Hotel
              location: Chicago
              partner_tier: premium
              contact_name: Jennifer Walsh
              contact_email: contact@riversidegrand.com
              contact_phone: +1-312-849-7263
              escalation_contact: manager@riversidegrand.com
              amenities:
                - pool
                - spa
                - restaurant
                - gym
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
          zendesk_tickets:
            - id: TCK-98259526
              subject: Booking modification inquiry - BKG-00257872
              description: Customer inquiring about modifying room type for booking BKG-00257872
              status: solved
              priority: normal
              type: question
              requester_id: USR-74829163
              assignee_id: AG-83945
              organization_id: null
              tags:
                - b2c-customer
                - modification-inquiry
              created_at: '2025-09-28T10:00:00Z'
              updated_at: '2025-09-28T15:00:00Z'
              due_at: null
              booking_reference: BKG-00257872
              hotel_id: HTL-83926471
              check_in_date: '2025-10-15T14:00:00Z'
              booking_value: 380.0
              request_type_detail: modify-room-type
              corporate_account_id: null
              group_booking_id: null
              resolution_action: information-provided
              refund_amount: 0.0
              escalation_reason: null
          zendesk_users:
            - id: USR-74829163
              name: Margaret Hartley
              email: margaret.hartley@outlook.com
              role: end-user
              organization_id: null
              phone: +1-312-478-9216
              verified: true
              active: true
              created_at: '2024-03-15T10:00:00Z'
              updated_at: '2024-03-15T10:00:00Z'
          payment_api_transactions:
            - id: TXN-74829163
              transaction_id: TXN-74829163
              booking_reference: BKG-00257872
              customer_id: CUS-74829163
              amount: '380.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 8421
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
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
                booking_reference: BKG-00257872
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-74829163
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-83926471
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-00257872'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'margaret.hartley@outlook.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Cancellation options inquiry - BKG-00257872
                  description: Customer inquiring about cancellation options and refund amounts for booking BKG-00257872. VIP tier customer with booking at premium hotel, check-in 2025-10-15. Will provide policy information and refund calculation.
                  status: open
                  priority: normal
                  type: question
                  requester_id: USR-74829163
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                  booking_reference: BKG-00257872
                  hotel_id: HTL-83926471
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  description: 'Customer inquired about cancellation options for booking BKG-00257872. Booking details: Premium hotel, check-in 2025-10-15, booking value $380.00, VIP tier customer. Calculated refund per policy: With 14 days notice (≥24 hours at premium hotel), customer eligible for 100% refund minus $15 service fee = $365.00. Explained cancellation windows and refund timeline. No cancellation was requested, information provided only.'
                  booking_reference: BKG-00257872
                  hotel_id: HTL-83926471
                  check_in_date: '2025-10-15T14:00:00Z'
                  booking_value: 380.0
                  request_type_detail: other
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_crf_021(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I have a billing issue with my recent booking. My name is Marcus Wellington, email marcus.wellington@protonmail.com, and my booking reference is BKG-23091307. When I completed the booking, the checkout page showed $390 as the total price, but I was charged $490 on my credit card. I took a screenshot of the checkout page as proof showing the $390 price. There's clearly been some kind of system error here. I'd like this resolved - either cancel my booking with a full refund, or correct the price and refund me the $100 difference.
    user_context: |
        You are Marcus Wellington, a customer who experienced a pricing error when booking. The checkout page displayed $390 but you were charged $490. You have a screenshot as evidence.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        IMPORTANT:
        - If the agent presents options between cancellation with full refund OR price correction (keeping the booking with a $100 refund), choose the price correction option. You want to keep the booking and just receive the $100 difference back.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-38472915
              booking_reference: BKG-23091307
              customer_id: CUS-74829156
              hotel_id: HTL-45921608
              check_in_date: '2025-10-04T14:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              booking_value: '490.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-28T10:00:00Z'
              updated_at: '2025-09-28T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-74829156
              customer_id: CUS-74829156
              email: marcus.wellington@protonmail.com
              full_name: Marcus Wellington
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '490.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-28T10:00:00Z'
              created_at: '2025-09-15T08:00:00Z'
              updated_at: '2025-09-28T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-62938471
              hotel_id: HTL-45921608
              hotel_name: Riverside Comfort Inn
              location: Portland
              partner_tier: standard
              contact_name: Jennifer Morrison
              contact_email: frontdesk@riversidecomfort.com
              contact_phone: +1-503-847-2194
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - breakfast
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
          payment_api_transactions:
            - id: TXN-84729153
              transaction_id: TXN-84729153
              booking_reference: BKG-23091307
              customer_id: CUS-74829156
              amount: '490.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7821
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-28T10:00:00Z'
              updated_at: '2025-09-28T10:00:00Z'
          zendesk_users:
            - id: USR-38294715
              name: Marcus Wellington
              email: marcus.wellington@protonmail.com
              role: end-user
              organization_id: null
              phone: +1-503-621-8473
              verified: true
              active: true
              created_at: '2025-09-15T08:00:00Z'
              updated_at: '2025-09-15T08:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          lookup_bookings: []
          lookup_hotels: []
          lookup_group_bookings: []
          lookup_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-23091307'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-23091307
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-74829156
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-45921608
            - tool: payment_api_get_transaction_history
              parameters:
                booking_reference: BKG-23091307
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.wellington@protonmail.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Billing discrepancy - BKG-23091307
                  description: Customer reports pricing discrepancy on booking BKG-23091307. Checkout page displayed $390 but customer was charged $490. Customer has screenshot evidence. System logs confirm pricing error occurred during booking. No modification history present. Customer requests either cancellation with full refund or price correction.
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-38294715
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-23091307
                  hotel_id: HTL-45921608
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-23091307
                refund_amount: '100.00'
                reason: billing_overcharge_correction
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  description: Customer reports pricing discrepancy on booking BKG-23091307. Checkout page displayed $390 but customer was charged $490. Customer has screenshot evidence. System logs confirm pricing error occurred during booking. No modification history present. Customer chose price correction option. Refund of $100 processed (TXN-00000009) to correct price to $390. Booking remains confirmed.
                  booking_reference: BKG-23091307
                  hotel_id: HTL-45921608
                  check_in_date: '2025-10-04T14:00:00Z'
                  booking_value: 490.0
                  request_type_detail: billing-inquiry
                  resolution_action: refund-partial
                  refund_amount: 100.0
                  escalation_reason: system-error
    """

    validate_database(x)


def test_gbi_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Patricia Chen, the group coordinator for booking GRP-86527858. My email is patricia.chen@corporateevents.net. I need to set up split billing for our group reservation. We have 8 rooms checking in on October 15th, and I'd like each room to be charged separately to the individual guests' credit cards. Each person will provide their own payment method when they check in. Can you help me arrange this?
    user_context: |
        You are Patricia Chen, a group coordinator for a corporate event. You are contacting support to request split billing setup for your group booking GRP-86527858.

        Your goal: Get split billing configured so each of the 8 rooms in your group can be charged to individual guest credit cards at check-in.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm the split billing arrangement details, confirm that each guest will pay for their own room individually at check-in.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-86527858
              coordinator_name: Patricia Chen
              coordinator_email: patricia.chen@corporateevents.net
              coordinator_phone: +1-408-529-7834
              total_rooms: 8
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-19T11:00:00Z'
              hotel_id: HTL-00045678
              booking_references:
                - BKG-00091001
                - BKG-00091002
                - BKG-00091003
                - BKG-00091004
                - BKG-00091005
                - BKG-00091006
                - BKG-00091007
                - BKG-00091008
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00045678
              hotel_name: Riverside Conference Hotel
              location: San Francisco
              partner_tier: standard
              contact_name: Michael Rodriguez
              contact_email: frontdesk@riversideconf.com
              contact_phone: +1-415-892-3647
              escalation_contact: null
              amenities:
                - wifi
                - conference_room
                - parking
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00067890
              email: patricia.chen@corporateevents.net
              full_name: Patricia Chen
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '2450.00'
              total_bookings_count: 4
              preferences:
                - early check-in
                - conference room proximity
              special_notes:
                - coordinates group bookings for corporate events
              complaint_count: 0
              last_booking_date: '2025-08-15T14:00:00Z'
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-08-15T14:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-00091001
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-19T11:00:00Z'
              booking_value: '600.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-86527858
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000007
              booking_reference: BKG-00091002
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-19T11:00:00Z'
              booking_value: '600.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-86527858
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000008
              booking_reference: BKG-00091003
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-19T11:00:00Z'
              booking_value: '600.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-86527858
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000009
              booking_reference: BKG-00091004
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-19T11:00:00Z'
              booking_value: '600.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-86527858
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000010
              booking_reference: BKG-00091005
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-19T11:00:00Z'
              booking_value: '600.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-86527858
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000011
              booking_reference: BKG-00091006
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-19T11:00:00Z'
              booking_value: '600.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-86527858
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000012
              booking_reference: BKG-00091007
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-19T11:00:00Z'
              booking_value: '600.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-86527858
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000013
              booking_reference: BKG-00091008
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-19T11:00:00Z'
              booking_value: '600.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-86527858
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Patricia Chen
              email: patricia.chen@corporateevents.net
              role: end-user
              organization_id: ORG-10000003
              phone: +1-408-529-7834
              verified: true
              active: true
              created_at: '2024-06-01T00:00:00Z'
              updated_at: '2024-06-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          payment_api_transactions: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-86527858
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00045678
            - tool: crm_api_get_customer_profile
              parameters:
                email: patricia.chen@corporateevents.net
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00091001
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-86527858'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'patricia.chen@corporateevents.net'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Split billing setup request - GRP-86527858
                  description: 'Group coordinator requests split billing arrangement for group booking GRP-86527858. Configuration needed: 8 rooms total, each room to be charged to individual guest credit cards at check-in. Guests will provide their own payment methods upon arrival. Medium group (8 rooms) at standard partner hotel. Check-in: 2025-10-15. Requires hotel partner configuration per Section 4.7.5.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                  booking_reference: BKG-00091001
                  hotel_id: HTL-00045678
                  check_in_date: '2025-10-15T15:00:00Z'
                  booking_value: 4800.0
                  request_type_detail: add-special-request
                  group_booking_id: GRP-86527858
                  refund_amount: 0
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-00045678
                booking_reference: BKG-00091001
                issue_type: hotel-confirmation-required
                description: Split billing configuration request for group booking GRP-86527858. Group coordinator requests individual billing setup where each of the 8 rooms will be charged to separate guest credit cards at check-in. Guests will provide their own payment methods upon arrival. Please confirm hotel can accommodate split billing arrangement and advise of any setup requirements.
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: hold
                  escalation_reason: hotel-confirmation-required
                  description: 'Group coordinator requests split billing arrangement for group booking GRP-86527858. Configuration needed: 8 rooms total, each room to be charged to individual guest credit cards at check-in. Guests will provide their own payment methods upon arrival. Medium group (8 rooms) at standard partner hotel. Check-in: 2025-10-15. ESCALATION: Escalated to hotel partner per Section 4.7.5 for billing configuration. Escalation ticket: ZDSK-00000013. Status: HOLD - awaiting hotel partner confirmation of split billing setup capability and any associated requirements. [hotel-partner-escalation applied]'
    """

    validate_database(x)


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
              created_at: '2025-09-28T13:00:00Z'
              updated_at: '2025-09-29T10:00:00Z'
              due_at: null
              booking_reference: null
              hotel_id: HTL-88776655
              check_in_date: '2025-10-10T15:00:00Z'
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
              created_at: '2025-08-15T09:00:00Z'
              updated_at: '2025-08-15T09:00:00Z'
          zendesk_ticket_comments: []
          zendesk_articles: []
          zendesk_organizations: []
          zendesk_comments: []
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-54973001
              customer_id: CUS-54973001
              hotel_id: HTL-88776655
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
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
              created_at: '2025-08-15T09:00:00Z'
              updated_at: '2025-08-15T09:00:00Z'
          booking_api_hotel_inventory: []
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-54973348
              coordinator_name: Patricia Morrison
              coordinator_email: patricia.morrison@eventsplus.com
              coordinator_phone: +1-415-782-6391
              total_rooms: 12
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
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
              created_at: '2025-08-15T09:00:00Z'
              updated_at: '2025-08-15T09:00:00Z'
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
              last_booking_date: '2025-08-15T09:00:00Z'
              created_at: '2025-08-15T09:00:00Z'
              updated_at: '2025-08-15T09:00:00Z'
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
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-54973348'
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
                  description: 'Customer request: Group coordinator for GRP-54973348 requests master account billing setup - all 12 room charges and incidentals to be billed to single company credit card. Company payment details provided.


                    Key data: Group booking GRP-54973348, 12 rooms at HTL-88776655 (premium partner), check-in 2025-10-10, total booking value $4,800.00.


                    Action taken: Escalated to hotel partner for billing configuration (escalation reference: ZDSK-00000001).


                    Status: hold - Awaiting hotel partner confirmation of master account billing setup.


                    Note: hotel-partner-escalation flag applies.'
                  booking_reference: BKG-54973001
                  hotel_id: HTL-88776655
                  check_in_date: '2025-10-10T15:00:00Z'
                  booking_value: 4800.0
                  request_type_detail: add-special-request
                  group_booking_id: GRP-54973348
                  escalation_reason: hotel-confirmation-required
    """

    validate_database(x)


def test_gbm_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm the coordinator for a group booking and need to change our check-in date. My email is rachel.nguyen@gmail.com and the group booking ID is GRP-58441986. We have 4 rooms booked with check-in on October 10th, but we need to move everything to October 15th instead. Can you help me update all 4 rooms to the new date?
    user_context: |
        You are Rachel Nguyen, a group coordinator contacting StayBridge support to change the check-in date for your group booking from October 10 to October 15 for all 4 rooms.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If the agent asks for confirmation to proceed with the modification, confirm.
        If the agent mentions an additional charge due to rate differences for the new dates, accept it.
    init:
      external_booking_v1:
        data_patch:
          zendesk_users:
            - id: USR-10000007
              name: Rachel Nguyen
              email: rachel.nguyen@gmail.com
              role: end-user
              organization_id: null
              phone: +1-312-459-8721
              verified: true
              active: true
              created_at: '2024-09-10T00:00:00Z'
              updated_at: '2024-09-10T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-58441986
              coordinator_name: Rachel Nguyen
              coordinator_email: rachel.nguyen@gmail.com
              coordinator_phone: +1-312-459-8721
              total_rooms: 4
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              hotel_id: HTL-00005678
              booking_references:
                - BKG-00001001
                - BKG-00001002
                - BKG-00001003
                - BKG-00001004
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-00001001
              customer_id: CUS-00001234
              hotel_id: HTL-00005678
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '200.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-58441986
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000007
              booking_reference: BKG-00001002
              customer_id: CUS-00001234
              hotel_id: HTL-00005678
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '200.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-58441986
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000008
              booking_reference: BKG-00001003
              customer_id: CUS-00001234
              hotel_id: HTL-00005678
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '200.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-58441986
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000009
              booking_reference: BKG-00001004
              customer_id: CUS-00001234
              hotel_id: HTL-00005678
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '200.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-58441986
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-00005678
              room_type: standard_room
              board_type: with_breakfast
              date: '2025-10-15T00:00:00Z'
              available_count: 8
              price_per_night: '110.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-00005678
              room_type: standard_room
              board_type: with_breakfast
              date: '2025-10-16T00:00:00Z'
              available_count: 8
              price_per_night: '110.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00005678
              hotel_id: HTL-00005678
              hotel_name: Chicago Lakefront Inn
              location: Chicago
              partner_tier: standard
              contact_name: Jennifer Walsh
              contact_email: contact@chicagolakefrontinn.com
              contact_phone: +1-312-847-2953
              escalation_contact: null
              amenities:
                - wifi
                - gym
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00001234
              customer_id: CUS-00001234
              email: rachel.nguyen@gmail.com
              full_name: Rachel Nguyen
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '2500.00'
              total_bookings_count: 5
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-06-01T00:00:00Z'
              updated_at: '2025-09-15T12:00:00Z'
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'rachel.nguyen@gmail.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-58441986'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Group date modification request - GRP-58441986
                  description: Group coordinator requests to change check-in date from 2025-10-10 to 2025-10-15 for all 4 rooms in group booking GRP-58441986.
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - group-coordinator
                    - check-in-upcoming
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-58441986
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00005678
            - tool: crm_api_get_customer_profile
              parameters:
                email: rachel.nguyen@gmail.com
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00005678
                check_in_date: '2025-10-15T15:00:00Z'
                check_out_date: '2025-10-17T11:00:00Z'
                room_type: standard_room
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: booking_api_modify_group_booking
              parameters:
                group_booking_id: GRP-58441986
                modification_details:
                  check_in_date: '2025-10-15T15:00:00Z'
                  check_out_date: '2025-10-17T11:00:00Z'
                cascade_to_individual_bookings: true
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-00001001
                charge_amount: '80.00'
                reason: price_difference
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  booking_reference: BKG-00001001
                  hotel_id: HTL-00005678
                  check_in_date: '2025-10-15T15:00:00Z'
                  booking_value: 880.0
                  request_type_detail: modify-dates
                  group_booking_id: GRP-58441986
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_gbm_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Jennifer Martinez, the group coordinator for booking GRP-90913341. I need to upgrade all 3 rooms from standard to deluxe rooms. I actually submitted this same request a couple of days ago but haven't heard anything back yet. Can you help me get this sorted out? My email is jennifer.martinez@eventplanning.org.
    user_context: |
        You are Jennifer Martinez, a group coordinator contacting support to follow up on a room type upgrade request for your group booking. You previously submitted this request a couple of days ago and are following up because it hasn't been completed yet.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If asked to confirm or approve charges/fees for the modification, accept and confirm them.
        - Your goal is to have all 3 rooms upgraded from standard_room to deluxe_room.
    init:
      external_booking_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-23281206
              subject: Room type modification request - GRP-90913341
              description: Request to change room type from standard_room to deluxe_room for all rooms in group booking
              status: pending
              priority: normal
              type: task
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: null
              tags:
                - group-coordinator
              created_at: '2025-09-29T10:00:00Z'
              updated_at: '2025-09-29T10:00:00Z'
              due_at: null
              booking_reference: BKG-00090001
              hotel_id: HTL-00055555
              check_in_date: '2025-10-05T15:00:00Z'
              booking_value: 600.0
              request_type_detail: modify-room-type
              corporate_account_id: null
              group_booking_id: GRP-90913341
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Jennifer Martinez
              email: jennifer.martinez@eventplanning.org
              role: end-user
              organization_id: null
              phone: +1-404-527-8341
              verified: true
              active: true
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-90913341
              coordinator_name: Jennifer Martinez
              coordinator_email: jennifer.martinez@eventplanning.org
              coordinator_phone: +1-404-527-8341
              total_rooms: 3
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              hotel_id: HTL-00055555
              booking_references:
                - BKG-00090001
                - BKG-00090002
                - BKG-00090003
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-00090001
              customer_id: CUS-00088888
              hotel_id: HTL-00055555
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '200.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-90913341
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000007
              booking_reference: BKG-00090002
              customer_id: CUS-00088888
              hotel_id: HTL-00055555
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '200.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-90913341
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000008
              booking_reference: BKG-00090003
              customer_id: CUS-00088888
              hotel_id: HTL-00055555
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '200.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-90913341
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00055555
              hotel_id: HTL-00055555
              hotel_name: Riverside Plaza Hotel
              location: Chicago
              partner_tier: premium
              contact_name: Victoria Chen
              contact_email: manager@riversideplaza.com
              contact_phone: +1-312-847-6239
              escalation_contact: director@riversideplaza.com
              amenities:
                - pool
                - spa
                - gym
                - restaurant
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00088888
              email: marcus.wilson@datatech.net
              full_name: Marcus Wilson
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '2500.00'
              total_bookings_count: 5
              preferences:
                - quiet room
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-01T14:00:00Z'
              created_at: '2024-05-10T10:00:00Z'
              updated_at: '2025-09-01T14:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-00055555
              room_type: deluxe_room
              board_type: without_breakfast
              date: '2025-10-05T00:00:00Z'
              available_count: 5
              price_per_night: '130.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-00055555
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-05T00:00:00Z'
              available_count: 5
              price_per_night: '150.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000008
              hotel_id: HTL-00055555
              room_type: deluxe_room
              board_type: half_board
              date: '2025-10-05T00:00:00Z'
              available_count: 5
              price_per_night: '180.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000009
              hotel_id: HTL-00055555
              room_type: deluxe_room
              board_type: without_breakfast
              date: '2025-10-06T00:00:00Z'
              available_count: 5
              price_per_night: '130.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000010
              hotel_id: HTL-00055555
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-06T00:00:00Z'
              available_count: 5
              price_per_night: '150.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000011
              hotel_id: HTL-00055555
              room_type: deluxe_room
              board_type: half_board
              date: '2025-10-06T00:00:00Z'
              available_count: 5
              price_per_night: '180.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-90913341'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-23281206
                item:
                  status: open
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-90913341
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00090001
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00055555
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00088888
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00055555
                check_in_date: '2025-10-05T15:00:00Z'
                check_out_date: '2025-10-07T11:00:00Z'
                room_type: deluxe_room
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00090001
                room_type: deluxe_room
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00090002
                room_type: deluxe_room
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00090003
                room_type: deluxe_room
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-00090001
                charge_amount: '337.50'
                reason: group_modification_fee_and_price_difference
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-23281206
                item:
                  status: solved
                  priority: normal
                  type: task
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                  booking_reference: BKG-00090001
                  hotel_id: HTL-00055555
                  check_in_date: '2025-10-05T15:00:00Z'
                  booking_value: 900.0
                  request_type_detail: modify-room-type
                  group_booking_id: GRP-90913341
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_gbm_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Margaret Chen and I'm coordinating a group booking for our team. My email is margaret.chen@techcorp.io and our group booking reference is GRP-79740344. We'd like to add breakfast to all 5 rooms in our booking. Can you help me with that?
    user_context: |
        You are Margaret Chen, a group coordinator contacting support to add breakfast to all 5 rooms in your group booking GRP-79740344. Your check-in is on October 3rd.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-79740344
              coordinator_name: Margaret Chen
              coordinator_email: margaret.chen@techcorp.io
              coordinator_phone: +1-312-847-2918
              total_rooms: 5
              check_in_date: '2025-10-03T14:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              hotel_id: HTL-55566677
              booking_references:
                - BKG-00010001
                - BKG-00010002
                - BKG-00010003
                - BKG-00010004
                - BKG-00010005
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-55566677
              hotel_id: HTL-55566677
              hotel_name: Riverside Budget Inn
              location: Chicago
              partner_tier: budget
              contact_name: Thomas Wright
              contact_email: manager@riversidebudgetinn.com
              contact_phone: +1-312-493-7621
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-00010001
              customer_id: CUS-00044455
              hotel_id: HTL-55566677
              check_in_date: '2025-10-03T14:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              room_type: standard_room
              board_type: without_breakfast
              booking_value: '200.00'
              booking_status: confirmed
              group_booking_id: GRP-79740344
              corporate_account_id: null
              adults_count: 2
              children_count: 0
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000007
              booking_reference: BKG-00010002
              customer_id: CUS-00044455
              hotel_id: HTL-55566677
              check_in_date: '2025-10-03T14:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              room_type: standard_room
              board_type: without_breakfast
              booking_value: '200.00'
              booking_status: confirmed
              group_booking_id: GRP-79740344
              corporate_account_id: null
              adults_count: 2
              children_count: 0
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000008
              booking_reference: BKG-00010003
              customer_id: CUS-00044455
              hotel_id: HTL-55566677
              check_in_date: '2025-10-03T14:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              room_type: standard_room
              board_type: without_breakfast
              booking_value: '200.00'
              booking_status: confirmed
              group_booking_id: GRP-79740344
              corporate_account_id: null
              adults_count: 2
              children_count: 0
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000009
              booking_reference: BKG-00010004
              customer_id: CUS-00044455
              hotel_id: HTL-55566677
              check_in_date: '2025-10-03T14:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              room_type: standard_room
              board_type: without_breakfast
              booking_value: '200.00'
              booking_status: confirmed
              group_booking_id: GRP-79740344
              corporate_account_id: null
              adults_count: 2
              children_count: 0
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000010
              booking_reference: BKG-00010005
              customer_id: CUS-00044455
              hotel_id: HTL-55566677
              check_in_date: '2025-10-03T14:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              room_type: standard_room
              board_type: without_breakfast
              booking_value: '200.00'
              booking_status: confirmed
              group_booking_id: GRP-79740344
              corporate_account_id: null
              adults_count: 2
              children_count: 0
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-55566677
              room_type: standard_room
              board_type: without_breakfast
              date: '2025-10-03T00:00:00Z'
              available_count: 5
              price_per_night: '100.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-55566677
              room_type: standard_room
              board_type: with_breakfast
              date: '2025-10-03T00:00:00Z'
              available_count: 5
              price_per_night: '120.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000008
              hotel_id: HTL-55566677
              room_type: standard_room
              board_type: half_board
              date: '2025-10-03T00:00:00Z'
              available_count: 5
              price_per_night: '140.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000009
              hotel_id: HTL-55566677
              room_type: standard_room
              board_type: full_board
              date: '2025-10-03T00:00:00Z'
              available_count: 5
              price_per_night: '160.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000010
              hotel_id: HTL-55566677
              room_type: standard_room
              board_type: without_breakfast
              date: '2025-10-04T00:00:00Z'
              available_count: 5
              price_per_night: '100.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000011
              hotel_id: HTL-55566677
              room_type: standard_room
              board_type: with_breakfast
              date: '2025-10-04T00:00:00Z'
              available_count: 5
              price_per_night: '120.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000012
              hotel_id: HTL-55566677
              room_type: standard_room
              board_type: half_board
              date: '2025-10-04T00:00:00Z'
              available_count: 5
              price_per_night: '140.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000013
              hotel_id: HTL-55566677
              room_type: standard_room
              board_type: full_board
              date: '2025-10-04T00:00:00Z'
              available_count: 5
              price_per_night: '160.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-00012001
              name: Margaret Chen
              email: margaret.chen@techcorp.io
              role: end-user
              organization_id: null
              phone: +1-312-847-2918
              verified: true
              active: true
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00044455
              email: margaret.chen@techcorp.io
              full_name: Margaret Chen
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '1000.00'
              total_bookings_count: 5
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
          lookup_bookings: []
          lookup_hotels: []
          lookup_group_bookings: []
          lookup_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-79740344
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-55566677
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00010001
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-55566677
                check_in_date: '2025-10-03T14:00:00Z'
                check_out_date: '2025-10-05T11:00:00Z'
                room_type: standard_room
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'margaret.chen@techcorp.io'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-00010001'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Group board type modification - GRP-79740344
                  description: 'Group coordinator requests adding breakfast to all 5 rooms in group booking GRP-79740344. Hotel: HTL-55566677 (budget tier). Check-in: 2025-10-03T14:00:00Z. Modification: without_breakfast to with_breakfast. Time until check-in: 49 hours. Small group (5 rooms), no escalation required.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-00012001
                  assignee_id: AG-83945
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                  booking_reference: BKG-00010001
                  hotel_id: HTL-55566677
                  group_booking_id: GRP-79740344
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00010001
                board_type: with_breakfast
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00010002
                board_type: with_breakfast
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00010003
                board_type: with_breakfast
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00010004
                board_type: with_breakfast
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00010005
                board_type: with_breakfast
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-00010001
                charge_amount: '387.50'
                reason: group_modification_fee
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  check_in_date: '2025-10-03T14:00:00Z'
                  booking_value: 1200.0
                  request_type_detail: modify-board-type
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_gbm_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Rachel Morrison, the coordinator for group booking GRP-49947174. My email is rachel.morrison@eventworks.net. We need to reduce our group from 5 rooms to 3 rooms - so please cancel 2 of the rooms. Can you help with this?
    user_context: |
        You are Rachel Morrison, a group coordinator contacting support to reduce your group booking from 5 rooms to 3 rooms (cancelling 2 rooms). Your group booking ID is GRP-49947174 and your email is rachel.morrison@eventworks.net.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm the cancellation, confirm it.
        - You do not have a specific preference for which rooms to cancel - let the agent decide.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-00045001
              customer_id: CUS-00034567
              hotel_id: HTL-00087432
              check_in_date: '2025-10-02T16:00:00Z'
              check_out_date: '2025-10-04T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-49947174
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000007
              booking_reference: BKG-00045002
              customer_id: CUS-00034567
              hotel_id: HTL-00087432
              check_in_date: '2025-10-02T16:00:00Z'
              check_out_date: '2025-10-04T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-49947174
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000008
              booking_reference: BKG-00045003
              customer_id: CUS-00034567
              hotel_id: HTL-00087432
              check_in_date: '2025-10-02T16:00:00Z'
              check_out_date: '2025-10-04T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-49947174
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000009
              booking_reference: BKG-00045004
              customer_id: CUS-00034567
              hotel_id: HTL-00087432
              check_in_date: '2025-10-02T16:00:00Z'
              check_out_date: '2025-10-04T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-49947174
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000010
              booking_reference: BKG-00045005
              customer_id: CUS-00034567
              hotel_id: HTL-00087432
              check_in_date: '2025-10-02T16:00:00Z'
              check_out_date: '2025-10-04T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-49947174
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-49947174
              coordinator_name: Rachel Morrison
              coordinator_email: rachel.morrison@eventworks.net
              coordinator_phone: +1-646-738-4291
              total_rooms: 5
              check_in_date: '2025-10-02T16:00:00Z'
              check_out_date: '2025-10-04T11:00:00Z'
              hotel_id: HTL-00087432
              booking_references:
                - BKG-00045001
                - BKG-00045002
                - BKG-00045003
                - BKG-00045004
                - BKG-00045005
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-00034567
              customer_id: CUS-00034567
              email: rachel.morrison@eventworks.net
              full_name: Rachel Morrison
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '2500.00'
              total_bookings_count: 8
              preferences:
                - early check-in
              special_notes:
                - group event coordinator
              complaint_count: 1
              last_booking_date: '2025-09-15T14:00:00Z'
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-09-15T14:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00087432
              hotel_name: The Paramount Suites
              location: Chicago
              partner_tier: premium
              contact_name: Victoria Henderson
              contact_email: reservations@paramountsuites.com
              contact_phone: +1-312-847-6102
              escalation_contact: manager@paramountsuites.com
              amenities:
                - pool
                - gym
                - spa
                - restaurant
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions: []
          zendesk_tickets: []
          zendesk_users:
            - id: USR-00078234
              name: Rachel Morrison
              email: rachel.morrison@eventworks.net
              role: end-user
              organization_id: null
              phone: +1-646-738-4291
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-49947174
            - tool: crm_api_get_customer_profile
              parameters:
                email: rachel.morrison@eventworks.net
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00087432
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00045001
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00045002
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-00045001'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'rachel.morrison@eventworks.net'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Group cancellation request - GRP-49947174
                  description: 'Group coordinator requests to cancel 2 rooms from group booking GRP-49947174 (reduce from 5 to 3 rooms). Customer VIP tier: standard. Hotel: HTL-00087432 (premium tier). Check-in: 2025-10-02T16:00:00Z (27 hours away). Rooms selected for cancellation in ascending order: BKG-00045001, BKG-00045002. Cancellation policy: premium hotel 24-hour policy, 100% refund minus $15 service fee per room. Refund per room: $305.00. Total refund: $610.00.'
                  status: open
                  priority: high
                  type: task
                  requester_id: USR-00078234
                  assignee_id: AG-83945
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                  booking_reference: BKG-00045001
                  hotel_id: HTL-00087432
                  group_booking_id: GRP-49947174
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00045001
                booking_status: cancelled
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-00045001
                refund_amount: '305.00'
                reason: cancellation
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00045002
                booking_status: cancelled
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-00045002
                refund_amount: '305.00'
                reason: cancellation
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  description: 'Group coordinator requests to cancel 2 rooms from group booking GRP-49947174 (reduce from 5 to 3 rooms). Customer VIP tier: standard. Hotel: HTL-00087432 (premium tier). Check-in: 2025-10-02T16:00:00Z (27 hours away). Rooms selected for cancellation in ascending order: BKG-00045001, BKG-00045002. Cancellation policy: premium hotel 24-hour policy, 100% refund minus $15 service fee per room. RESOLUTION: Successfully cancelled 2 rooms. Refund per room: $305.00 ($320 - $15 service fee). Total refund processed: $610.00. Transaction IDs: TXN-00000008, TXN-00000009. Expected to appear on card in 3-5 business days + 5-10 days. Remaining group: 3 rooms (BKG-00045003, BKG-00045004, BKG-00045005).'
                  check_in_date: '2025-10-02T16:00:00Z'
                  booking_value: 960.0
                  request_type_detail: cancel-booking
                  resolution_action: refund-partial
                  refund_amount: 610.0
    """

    validate_database(x)


def test_gbm_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I need to change the check-in date for my group booking.
    user_context: |
        You are Patricia Williams, a group coordinator contacting StayBridge support to change the check-in date for your group booking. You want to move the entire stay by 2 days while maintaining the same duration.

        Only if you are asked about your name or who you are — tell the agent you are Patricia Williams, the coordinator for this group booking.
        Only if you are asked about the booking reference or booking number — provide the group booking number GRP-64887719.
        Only if you are asked about your email or contact information — provide patricia.williams@eventplanning.net.
        Only if you are asked about the hotel or property name — tell the agent it's the Riverside Conference Hotel.
        Only if you are asked about the number of rooms or size of the group — tell the agent there are 10 rooms booked.
        Only if you are asked about the current dates or original dates — the current check-in is October 12th, 2025 and check-out is October 15th, 2025.
        Only if you are asked about the new dates or what dates you want — you want to change check-in to October 14th, 2025 and check-out to October 17th, 2025.
        Only if you are asked about the duration or length of stay — it's a 3-night stay and you want to keep the same duration.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If asked to confirm the date change, confirm that you want to proceed with changing check-in to October 14, 2025 for all 10 rooms.
        If the agent asks about the check-out date or stay length, confirm that you want to shift the entire stay by 2 days to maintain the same 3-night duration - new dates should be October 14-17, 2025.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-64887719
              coordinator_name: Patricia Williams
              coordinator_email: patricia.williams@eventplanning.net
              coordinator_phone: +1-312-847-6293
              total_rooms: 10
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-15T11:00:00Z'
              hotel_id: HTL-00087654
              booking_references:
                - BKG-64887701
                - BKG-64887702
                - BKG-64887703
                - BKG-64887704
                - BKG-64887705
                - BKG-64887706
                - BKG-64887707
                - BKG-64887708
                - BKG-64887709
                - BKG-64887710
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00087654
              hotel_id: HTL-00087654
              hotel_name: Riverside Conference Hotel
              location: Chicago
              partner_tier: standard
              contact_name: Michael Brennan
              contact_email: frontdesk@riversideconf.com
              contact_phone: +1-312-492-7815
              escalation_contact: null
              amenities:
                - wifi
                - conference_room
                - parking
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-64887701
              customer_id: CUS-00087654
              hotel_id: HTL-00087654
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-15T11:00:00Z'
              booking_value: '540.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-64887719
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000007
              booking_reference: BKG-64887702
              customer_id: CUS-00087654
              hotel_id: HTL-00087654
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-15T11:00:00Z'
              booking_value: '540.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-64887719
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000008
              booking_reference: BKG-64887703
              customer_id: CUS-00087654
              hotel_id: HTL-00087654
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-15T11:00:00Z'
              booking_value: '540.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-64887719
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000009
              booking_reference: BKG-64887704
              customer_id: CUS-00087654
              hotel_id: HTL-00087654
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-15T11:00:00Z'
              booking_value: '540.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-64887719
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000010
              booking_reference: BKG-64887705
              customer_id: CUS-00087654
              hotel_id: HTL-00087654
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-15T11:00:00Z'
              booking_value: '540.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-64887719
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000011
              booking_reference: BKG-64887706
              customer_id: CUS-00087654
              hotel_id: HTL-00087654
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-15T11:00:00Z'
              booking_value: '540.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-64887719
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000012
              booking_reference: BKG-64887707
              customer_id: CUS-00087654
              hotel_id: HTL-00087654
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-15T11:00:00Z'
              booking_value: '540.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-64887719
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000013
              booking_reference: BKG-64887708
              customer_id: CUS-00087654
              hotel_id: HTL-00087654
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-15T11:00:00Z'
              booking_value: '540.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-64887719
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000014
              booking_reference: BKG-64887709
              customer_id: CUS-00087654
              hotel_id: HTL-00087654
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-15T11:00:00Z'
              booking_value: '540.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-64887719
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000015
              booking_reference: BKG-64887710
              customer_id: CUS-00087654
              hotel_id: HTL-00087654
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-15T11:00:00Z'
              booking_value: '540.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-64887719
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-00087654
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-14T00:00:00Z'
              available_count: 15
              price_per_night: '180.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-00087654
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-15T00:00:00Z'
              available_count: 15
              price_per_night: '180.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000008
              hotel_id: HTL-00087654
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-16T00:00:00Z'
              available_count: 15
              price_per_night: '180.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000009
              hotel_id: HTL-00087654
              room_type: deluxe_room
              board_type: without_breakfast
              date: '2025-10-14T00:00:00Z'
              available_count: 15
              price_per_night: '160.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000010
              hotel_id: HTL-00087654
              room_type: deluxe_room
              board_type: half_board
              date: '2025-10-14T00:00:00Z'
              available_count: 15
              price_per_night: '210.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00087654
              email: patricia.williams@eventplanning.net
              full_name: Patricia Williams
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '2850.00'
              total_bookings_count: 8
              preferences:
                - conference rooms
                - early check-in
              special_notes:
                - coordinates group events
              complaint_count: 0
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2024-06-15T10:00:00Z'
              updated_at: '2025-09-01T12:00:00Z'
          zendesk_tickets:
            - id: TCK-06594013
              subject: Group booking date change request
              description: Coordinator requesting date modification for group booking
              status: solved
              priority: normal
              type: task
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: null
              tags:
                - check-in-upcoming
                - group-coordinator
              created_at: '2025-09-27T10:00:00Z'
              updated_at: '2025-09-28T14:00:00Z'
              due_at: null
              booking_reference: BKG-64887701
              hotel_id: HTL-00087654
              check_in_date: '2025-10-12T15:00:00Z'
              booking_value: 5400.0
              request_type_detail: modify-dates
              corporate_account_id: null
              group_booking_id: GRP-64887719
              resolution_action: information-provided
              refund_amount: 0
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Patricia Williams
              email: patricia.williams@eventplanning.net
              role: end-user
              organization_id: null
              phone: +1-312-847-6293
              verified: true
              active: true
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          zendesk_organizations: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-64887719
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00087654
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-64887701
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00087654
                check_in_date: '2025-10-14T15:00:00Z'
                check_out_date: '2025-10-17T11:00:00Z'
                room_type: deluxe_room
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: crm_api_get_customer_profile
              parameters:
                email: patricia.williams@eventplanning.net
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-64887719'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-06594013
                item:
                  status: open
            - tool: booking_api_modify_group_booking
              parameters:
                group_booking_id: GRP-64887719
                modification_details:
                  check_in_date: '2025-10-14T15:00:00Z'
                  check_out_date: '2025-10-17T11:00:00Z'
                cascade_to_individual_bookings: true
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'patricia.williams@eventplanning.net'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-06594013
                item:
                  status: solved
                  priority: normal
                  type: task
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                  booking_reference: BKG-64887701
                  hotel_id: HTL-00087654
                  check_in_date: '2025-10-14T15:00:00Z'
                  booking_value: 5400.0
                  request_type_detail: modify-dates
                  group_booking_id: GRP-64887719
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


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
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          booking_api_bookings:
            - id: BKG-00001001
              booking_reference: BKG-00001001
              customer_id: CUS-00045678
              hotel_id: HTL-00056789
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001002
              booking_reference: BKG-00001002
              customer_id: CUS-00045679
              hotel_id: HTL-00056789
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001003
              booking_reference: BKG-00001003
              customer_id: CUS-00045680
              hotel_id: HTL-00056789
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001004
              booking_reference: BKG-00001004
              customer_id: CUS-00045681
              hotel_id: HTL-00056789
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001005
              booking_reference: BKG-00001005
              customer_id: CUS-00045682
              hotel_id: HTL-00056789
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001006
              booking_reference: BKG-00001006
              customer_id: CUS-00045683
              hotel_id: HTL-00056789
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001007
              booking_reference: BKG-00001007
              customer_id: CUS-00045684
              hotel_id: HTL-00056789
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001008
              booking_reference: BKG-00001008
              customer_id: CUS-00045685
              hotel_id: HTL-00056789
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
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
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
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
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
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
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2025-03-15T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
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
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2025-04-20T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
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
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
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
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
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
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
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
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
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
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          zendesk_users:
            - id: USR-00001001
              name: Rachel Morrison
              email: rachel.morrison@eventpro.com
              role: end-user
              organization_id: null
              phone: +1-617-425-8391
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-00056789
              room_type: suite
              board_type: with_breakfast
              date: '2025-10-06T00:00:00Z'
              available_count: 7
              price_per_night: '350.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-00056789
              room_type: suite
              board_type: with_breakfast
              date: '2025-10-07T00:00:00Z'
              available_count: 7
              price_per_night: '350.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000008
              hotel_id: HTL-00056789
              room_type: suite
              board_type: with_breakfast
              date: '2025-10-08T00:00:00Z'
              available_count: 7
              price_per_night: '350.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000009
              hotel_id: HTL-00056789
              room_type: suite
              board_type: without_breakfast
              date: '2025-10-06T00:00:00Z'
              available_count: 7
              price_per_night: '320.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000010
              hotel_id: HTL-00056789
              room_type: suite
              board_type: without_breakfast
              date: '2025-10-07T00:00:00Z'
              available_count: 7
              price_per_night: '320.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000011
              hotel_id: HTL-00056789
              room_type: suite
              board_type: without_breakfast
              date: '2025-10-08T00:00:00Z'
              available_count: 7
              price_per_night: '320.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000012
              hotel_id: HTL-00056789
              room_type: suite
              board_type: half_board
              date: '2025-10-06T00:00:00Z'
              available_count: 7
              price_per_night: '400.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000013
              hotel_id: HTL-00056789
              room_type: suite
              board_type: half_board
              date: '2025-10-07T00:00:00Z'
              available_count: 7
              price_per_night: '400.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000014
              hotel_id: HTL-00056789
              room_type: suite
              board_type: half_board
              date: '2025-10-08T00:00:00Z'
              available_count: 7
              price_per_night: '400.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
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
                filter: email eq 'rachel.morrison@eventpro.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-99049027'
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00056789
                check_in_date: '2025-10-06T15:00:00Z'
                check_out_date: '2025-10-09T11:00:00Z'
                room_type: suite
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Room type upgrade request - GRP-99049027
                  description: 'Group coordinator requests upgrading 5 of 8 rooms from standard_room to suite for group booking GRP-99049027. Check-in: 2025-10-06. Premium hotel property. Rooms selected in ascending booking reference order: BKG-00001001 through BKG-00001005.'
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
                  check_in_date: '2025-10-06T15:00:00Z'
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
                  description: 'Group coordinator requests upgrading 5 of 8 rooms from standard_room to suite for group booking GRP-99049027. Check-in: 2025-10-06. Premium hotel property. Room selection method: ascending booking reference order. Modified rooms: BKG-00001001, BKG-00001002, BKG-00001003, BKG-00001004, BKG-00001005. All modifications completed successfully. Group modification fee: $62.50 (medium group, premium hotel 0.5× multiplier). Price difference for upgrades: $2,250.00. Total charged: $2,312.50. Transaction ID: TXN-00000008.'
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_gbm_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Sarah Thompson, the group coordinator for booking GRP-87429671. I reached out a few days ago about adding early check-in for all 12 rooms in our group - we're checking in on October 5th. Just wanted to follow up on this request. My email is sarah.thompson@eventplanning.com.
    user_context: |
        You are Sarah Thompson, a group coordinator contacting support to follow up on an early check-in request for your group booking GRP-87429671 (12 rooms). You want early check-in added for all rooms.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If the agent informs you of a fee (around $300 for early check-in) and asks for confirmation or acceptance, confirm that you accept the fee and want to proceed.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-87429671
              coordinator_name: Sarah Thompson
              coordinator_email: sarah.thompson@eventplanning.com
              coordinator_phone: +1-503-892-4176
              total_rooms: 12
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              hotel_id: HTL-45892010
              booking_references:
                - BKG-78451201
                - BKG-78451202
                - BKG-78451203
                - BKG-78451204
                - BKG-78451205
                - BKG-78451206
                - BKG-78451207
                - BKG-78451208
                - BKG-78451209
                - BKG-78451210
                - BKG-78451211
                - BKG-78451212
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-45892010
              hotel_name: Riverside Inn & Suites
              location: Portland, Oregon
              partner_tier: budget
              contact_name: Mike Reynolds
              contact_email: mike.reynolds@riversideinn.com
              contact_phone: +1-503-847-6290
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-34521098
              customer_id: CUS-34521098
              email: sarah.thompson@eventplanning.com
              full_name: Sarah Thompson
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '4250.00'
              total_bookings_count: 8
              preferences:
                - ground floor
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          zendesk_users:
            - id: USR-28847201
              name: Sarah Thompson
              email: sarah.thompson@eventplanning.com
              role: end-user
              organization_id: null
              phone: +1-503-892-4176
              verified: true
              active: true
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2024-06-01T10:00:00Z'
          zendesk_tickets:
            - id: '75655125'
              subject: Early check-in request - Group GRP-87429671
              description: 'Group coordinator requesting early check-in for all 12 rooms in group booking GRP-87429671. Check-in date: 2025-10-05.'
              status: pending
              priority: normal
              type: task
              requester_id: USR-28847201
              assignee_id: AG-83945
              organization_id: null
              tags:
                - group-coordinator
                - special-request
              created_at: '2025-09-28T10:00:00Z'
              updated_at: '2025-09-28T10:00:00Z'
              due_at: null
              booking_reference: BKG-78451201
              hotel_id: HTL-45892010
              check_in_date: '2025-10-05T15:00:00Z'
              booking_value: 3360.0
              request_type_detail: add-special-request
              corporate_account_id: null
              group_booking_id: GRP-87429671
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-78451201
              customer_id: CUS-34521098
              hotel_id: HTL-45892010
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '280.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-87429671
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000007
              booking_reference: BKG-78451202
              customer_id: CUS-34521098
              hotel_id: HTL-45892010
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '280.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-87429671
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000008
              booking_reference: BKG-78451203
              customer_id: CUS-34521098
              hotel_id: HTL-45892010
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '280.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-87429671
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000009
              booking_reference: BKG-78451204
              customer_id: CUS-34521098
              hotel_id: HTL-45892010
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '280.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-87429671
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000010
              booking_reference: BKG-78451205
              customer_id: CUS-34521098
              hotel_id: HTL-45892010
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '280.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-87429671
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000011
              booking_reference: BKG-78451206
              customer_id: CUS-34521098
              hotel_id: HTL-45892010
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '280.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-87429671
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000012
              booking_reference: BKG-78451207
              customer_id: CUS-34521098
              hotel_id: HTL-45892010
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '280.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-87429671
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000013
              booking_reference: BKG-78451208
              customer_id: CUS-34521098
              hotel_id: HTL-45892010
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '280.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-87429671
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000014
              booking_reference: BKG-78451209
              customer_id: CUS-34521098
              hotel_id: HTL-45892010
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '280.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-87429671
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000015
              booking_reference: BKG-78451210
              customer_id: CUS-34521098
              hotel_id: HTL-45892010
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '280.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-87429671
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000016
              booking_reference: BKG-78451211
              customer_id: CUS-34521098
              hotel_id: HTL-45892010
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '280.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-87429671
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000017
              booking_reference: BKG-78451212
              customer_id: CUS-34521098
              hotel_id: HTL-45892010
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '280.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-87429671
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          lookup_bookings: []
          lookup_hotels: []
          lookup_group_bookings: []
          lookup_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-87429671
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-45892010
            - tool: crm_api_get_customer_profile
              parameters:
                email: sarah.thompson@eventplanning.com
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'sarah.thompson@eventplanning.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-87429671'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '75655125'
                item:
                  status: open
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-78451201
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-45892010
                booking_reference: BKG-78451201
                issue_type: hotel-confirmation-required
                description: 'Group booking GRP-87429671 (12 rooms, medium group) requesting early check-in for all rooms on 2025-10-05. Total rooms: 12. Customer (Sarah Thompson) has accepted early check-in fee of $300 ($25/room). Awaiting hotel confirmation to proceed with adding early check-in to all 12 bookings.'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '75655125'
                item:
                  status: hold
                  priority: normal
                  type: task
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                    - hotel-partner-escalation
                  description: 'Group coordinator Sarah Thompson requesting early check-in for all 12 rooms in group GRP-87429671. Check-in: 2025-10-05. Customer vip_tier: standard. Hotel: Riverside Inn & Suites (budget tier). Customer accepted $300 early check-in fee ($25/room × 12 rooms). Escalated to hotel partner for confirmation due to group booking at budget hotel within 7 days of check-in. Awaiting hotel response. Escalation tracking: ZDSK-00000001.'
                  booking_reference: BKG-78451201
                  hotel_id: HTL-45892010
                  check_in_date: '2025-10-05T15:00:00Z'
                  booking_value: 3360.0
                  group_booking_id: GRP-87429671
                  request_type_detail: add-special-request
                  resolution_action: escalated-hotel
                  refund_amount: 0
                  escalation_reason: hotel-confirmation-required
    """

    validate_database(x)


def test_gbm_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Margaret Chen, the group coordinator for booking GRP-72423884. My email is margaret.chen@nexusevents.com. We urgently need to extend our stay by one additional night - so change the check-out date for all 15 rooms in the group. Our check-in is tomorrow and I need to get this sorted as quickly as possible. Can you help with this?
    user_context: |
        You are Margaret Chen, a group coordinator for a corporate event, contacting support to extend the check-out date by 1 night for all 15 rooms in your group booking GRP-72423884. Check-in is tomorrow so you're feeling some urgency. You understand that changes may involve fees and approval processes.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent explains that hotel approval is required and provides fee information, acknowledge and confirm you understand you'll need to wait for the hotel's response.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-72423884
              coordinator_name: Margaret Chen
              coordinator_email: margaret.chen@nexusevents.com
              coordinator_phone: +1-408-295-3847
              total_rooms: 15
              check_in_date: '2025-10-02T18:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              hotel_id: HTL-00045678
              booking_references:
                - BKG-00072001
                - BKG-00072002
                - BKG-00072003
                - BKG-00072004
                - BKG-00072005
                - BKG-00072006
                - BKG-00072007
                - BKG-00072008
                - BKG-00072009
                - BKG-00072010
                - BKG-00072011
                - BKG-00072012
                - BKG-00072013
                - BKG-00072014
                - BKG-00072015
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-00072001
              customer_id: CUS-00034567
              hotel_id: HTL-00045678
              check_in_date: '2025-10-02T18:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '600.00'
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-72423884
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00045678
              hotel_name: Riverside Business Hotel
              location: Chicago
              partner_tier: standard
              contact_name: Jennifer Walsh
              contact_email: frontdesk@riversidebusiness.com
              contact_phone: +1-312-847-9162
              escalation_contact: manager@riversidebusiness.com
              amenities:
                - wifi
                - business_center
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00034567
              email: thomas.greene@techfirm.com
              full_name: Thomas Greene
              vip_tier: standard
              loyalty_program_status: active
              lifetime_value: '2450.00'
              total_bookings_count: 8
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Margaret Chen
              email: margaret.chen@nexusevents.com
              role: end-user
              organization_id: ORG-10000005
              phone: +1-408-295-3847
              verified: true
              active: true
              created_at: '2025-08-15T00:00:00Z'
              updated_at: '2025-08-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
          lookup_bookings: []
          lookup_hotels: []
          lookup_group_bookings: []
          lookup_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-72423884
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00072001
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00045678
            - tool: crm_api_check_vip_status
              parameters:
                customer_id: CUS-00034567
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-72423884'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'margaret.chen@nexusevents.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Group booking date extension request - GRP-72423884
                  description: 'Group coordinator requests to extend check-out by 1 night for all 15 rooms in group GRP-72423884. Original check-out: 2025-10-05. Requested check-out: 2025-10-06. Hotel: HTL-00045678 (standard tier). Time until check-in: 29 hours. Medium group modification within 48 hours requires mandatory hotel partner approval per Section 4.7.2. Pending estimated charges: modification fee $750 (15 rooms × $50 × 1.0) plus price difference for additional night.'
                  status: open
                  priority: high
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                  booking_reference: BKG-00072001
                  hotel_id: HTL-00045678
                  group_booking_id: GRP-72423884
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-00045678
                booking_reference: BKG-00072001
                issue_type: hotel-confirmation-required
                description: 'Group booking GRP-72423884 (15 rooms) requests check-out date extension from 2025-10-05 to 2025-10-06 for all rooms. Check-in is 2025-10-02 (29 hours away). Mandatory hotel approval required per medium group modification policy. Please confirm availability and approve date extension for all 15 rooms. Room type: standard_room. Board type: with_breakfast.'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: hold
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                    - hotel-partner-escalation
                  check_in_date: '2025-10-02T18:00:00Z'
                  booking_value: 9000.0
                  request_type_detail: modify-dates
                  escalation_reason: hotel-confirmation-required
                  refund_amount: 0
    """

    validate_database(x)


def test_gbm_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Rachel Martinez, the coordinator for group booking GRP-67468071. My email is rachel.martinez@eventgroup.org. I reached out about a day ago to request changing the meal plan from breakfast included to half-board for all 6 rooms in our group, but I haven't heard back yet. Can you please help move this along? Our check-in is coming up on October 3rd and I need to get this sorted.
    user_context: |
        You are Rachel Martinez, a group coordinator following up on a board type modification request for group booking GRP-67468071.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent informs you about fees, escalation to hotel, or wait times, acknowledge this and thank them for the update.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00001001
              booking_reference: BKG-00001001
              customer_id: CUS-00012345
              hotel_id: HTL-00045678
              check_in_date: '2025-10-03T10:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              booking_value: '200.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-67468071
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00001002
              booking_reference: BKG-00001002
              customer_id: CUS-00012345
              hotel_id: HTL-00045678
              check_in_date: '2025-10-03T10:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              booking_value: '200.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-67468071
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00001003
              booking_reference: BKG-00001003
              customer_id: CUS-00012345
              hotel_id: HTL-00045678
              check_in_date: '2025-10-03T10:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              booking_value: '200.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-67468071
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00001004
              booking_reference: BKG-00001004
              customer_id: CUS-00012345
              hotel_id: HTL-00045678
              check_in_date: '2025-10-03T10:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              booking_value: '200.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-67468071
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00001005
              booking_reference: BKG-00001005
              customer_id: CUS-00012345
              hotel_id: HTL-00045678
              check_in_date: '2025-10-03T10:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              booking_value: '200.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-67468071
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00001006
              booking_reference: BKG-00001006
              customer_id: CUS-00012345
              hotel_id: HTL-00045678
              check_in_date: '2025-10-03T10:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              booking_value: '200.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-67468071
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-67468071
              coordinator_name: Rachel Martinez
              coordinator_email: rachel.martinez@eventgroup.org
              coordinator_phone: +1-415-738-2841
              total_rooms: 6
              check_in_date: '2025-10-03T10:00:00Z'
              check_out_date: '2025-10-05T11:00:00Z'
              hotel_id: HTL-00045678
              booking_references:
                - BKG-00001001
                - BKG-00001002
                - BKG-00001003
                - BKG-00001004
                - BKG-00001005
                - BKG-00001006
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-00012345
              customer_id: CUS-00012345
              email: rachel.martinez@eventgroup.org
              full_name: Rachel Martinez
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '2450.75'
              total_bookings_count: 8
              preferences:
                - early check-in
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-03-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00045678
              hotel_name: Budget Stay Express
              location: Chicago
              partner_tier: budget
              contact_name: Thomas Wright
              contact_email: contact@budgetstayexpress.com
              contact_phone: +1-312-847-5923
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions: []
          zendesk_tickets:
            - id: '54516808'
              subject: Board type modification request for group booking
              description: Request to change board type from with_breakfast to half_board for group booking GRP-67468071
              status: open
              priority: normal
              type: task
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: ORG-10000005
              tags:
                - group-coordinator
                - board-type-change
              created_at: '2025-09-30T13:00:00Z'
              updated_at: '2025-09-30T13:00:00Z'
              due_at: null
              booking_reference: BKG-00001001
              hotel_id: HTL-00045678
              check_in_date: '2025-10-03T10:00:00Z'
              booking_value: 1200.0
              request_type_detail: modify-board-type
              corporate_account_id: null
              group_booking_id: GRP-67468071
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Rachel Martinez
              email: rachel.martinez@eventgroup.org
              role: end-user
              organization_id: ORG-10000005
              phone: +1-415-738-2841
              verified: true
              active: true
              created_at: '2025-03-15T00:00:00Z'
              updated_at: '2025-03-15T00:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-67468071
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00001001
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00045678
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00012345
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'rachel.martinez@eventgroup.org'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-00001001'
                orderby: created_at desc
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-00045678
                booking_reference: BKG-00001001
                issue_type: hotel-confirmation-required
                description: 'Group booking GRP-67468071 modification request: change board type from with_breakfast to half_board for all 6 rooms. Medium group (6 rooms) at budget tier hotel with check-in 45 hours away. Requires mandatory hotel approval per medium group modification policy. If approved, modification fee of $450 will apply ($50 base × 6 rooms × 1.5 budget multiplier).'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '54516808'
                item:
                  status: hold
                  priority: high
                  type: task
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                    - hotel-partner-escalation
                  booking_reference: BKG-00001001
                  hotel_id: HTL-00045678
                  check_in_date: '2025-10-03T10:00:00Z'
                  booking_value: 1200.0
                  request_type_detail: modify-board-type
                  group_booking_id: GRP-67468071
                  escalation_reason: hotel-confirmation-required
                  refund_amount: 0
    """

    validate_database(x)


def test_gbm_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I need to change the check-in date for my group booking.
    user_context: |
        You are Marcus Reynolds, a group coordinator for a corporate event. You need to change the check-in date for your group booking. You want to keep the same stay duration (2 nights).

        Only if you are asked about your booking reference or confirmation number — tell the agent it is GRP-76038597.
        Only if you are asked about your name — tell the agent your name is Marcus Reynolds.
        Only if you are asked about your email or contact information — tell the agent your email is marcus.reynolds@tradeconnect.org.
        Only if you are asked about the number of rooms — tell the agent you have 20 rooms booked.
        Only if you are asked about the current check-in date — tell the agent it is currently October 15th.
        Only if you are asked about the new desired check-in date — tell the agent you need to move it to October 20th.
        Only if you are asked about whether this change is for the entire group — confirm yes, the date change is for the entire group.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If asked to confirm the checkout date shift, confirm you want checkout on October 22 (maintaining 2-night stay).
        - If informed about additional charges or price differences, accept and confirm you agree to proceed.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-76038597
              coordinator_name: Marcus Reynolds
              coordinator_email: marcus.reynolds@tradeconnect.org
              coordinator_phone: +1-415-847-2938
              total_rooms: 20
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              hotel_id: HTL-00012345
              booking_references:
                - BKG-00001001
                - BKG-00001002
                - BKG-00001003
                - BKG-00001004
                - BKG-00001005
                - BKG-00001006
                - BKG-00001007
                - BKG-00001008
                - BKG-00001009
                - BKG-00001010
                - BKG-00001011
                - BKG-00001012
                - BKG-00001013
                - BKG-00001014
                - BKG-00001015
                - BKG-00001016
                - BKG-00001017
                - BKG-00001018
                - BKG-00001019
                - BKG-00001020
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00098765
              customer_id: CUS-00098765
              email: marcus.reynolds@tradeconnect.org
              full_name: Marcus Reynolds
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '12000.00'
              total_bookings_count: 5
              preferences:
                - business amenities
                - meeting rooms
              special_notes:
                - group coordinator for corporate events
              complaint_count: 0
              last_booking_date: '2025-08-15T14:00:00Z'
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-09-01T12:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-00012345
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-20T00:00:00Z'
              available_count: 25
              price_per_night: '225.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-00012345
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-21T00:00:00Z'
              available_count: 25
              price_per_night: '225.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Reynolds
              email: marcus.reynolds@tradeconnect.org
              role: end-user
              organization_id: ORG-10000005
              phone: +1-415-847-2938
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          booking_api_bookings:
            - id: BKG-00001001
              booking_reference: BKG-00001001
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001002
              booking_reference: BKG-00001002
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001003
              booking_reference: BKG-00001003
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001004
              booking_reference: BKG-00001004
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001005
              booking_reference: BKG-00001005
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001006
              booking_reference: BKG-00001006
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001007
              booking_reference: BKG-00001007
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001008
              booking_reference: BKG-00001008
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001009
              booking_reference: BKG-00001009
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001010
              booking_reference: BKG-00001010
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001011
              booking_reference: BKG-00001011
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001012
              booking_reference: BKG-00001012
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001013
              booking_reference: BKG-00001013
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001014
              booking_reference: BKG-00001014
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001015
              booking_reference: BKG-00001015
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001016
              booking_reference: BKG-00001016
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001017
              booking_reference: BKG-00001017
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001018
              booking_reference: BKG-00001018
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001019
              booking_reference: BKG-00001019
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00001020
              booking_reference: BKG-00001020
              customer_id: CUS-00098765
              hotel_id: HTL-00012345
              check_in_date: '2025-10-15T15:00:00Z'
              check_out_date: '2025-10-17T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-76038597
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00012345
              hotel_id: HTL-00012345
              hotel_name: Grand Plaza Hotel
              location: New York
              partner_tier: premium
              contact_name: Marcus Whitfield
              contact_email: manager@grandplaza.com
              contact_phone: +1-212-738-4501
              escalation_contact: director@grandplaza.com
              amenities:
                - pool
                - gym
                - spa
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-76038597
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00012345
            - tool: crm_api_get_customer_profile
              parameters:
                email: marcus.reynolds@tradeconnect.org
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00012345
                check_in_date: '2025-10-20T15:00:00Z'
                check_out_date: '2025-10-22T11:00:00Z'
                room_type: deluxe_room
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-76038597'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.reynolds@tradeconnect.org'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Group date modification request - GRP-76038597
                  description: 'Group coordinator requests date change for 20-room group booking. Original dates: 2025-10-15 to 2025-10-17. Requested new dates: 2025-10-20 to 2025-10-22. Premium partner hotel - large group exception applies (>7 days before check-in). No escalation required. Modification fee: $0.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                  booking_reference: BKG-00001001
                  hotel_id: HTL-00012345
                  group_booking_id: GRP-76038597
            - tool: booking_api_modify_group_booking
              parameters:
                group_booking_id: GRP-76038597
                modification_details:
                  check_in_date: '2025-10-20T15:00:00Z'
                  check_out_date: '2025-10-22T11:00:00Z'
                cascade_to_individual_bookings: true
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-00001001
                charge_amount: '1000.00'
                reason: price_difference
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  description: 'Group coordinator requests date change for 20-room group booking. Original dates: 2025-10-15 to 2025-10-17. Requested new dates: 2025-10-20 to 2025-10-22. Premium partner hotel - large group exception applies (>7 days before check-in). No escalation required. Modification fee: $0. Modification completed successfully for all 20 rooms. Price difference of $1,000 charged (TXN-00000008). Final group booking value: $9,000.'
                  check_in_date: '2025-10-20T15:00:00Z'
                  booking_value: 9000.0
                  request_type_detail: modify-dates
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_gbm_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Margaret Chen, the group coordinator for booking GRP-70348247. My email is margaret.chen@eventplanners.org. We have 18 rooms booked for October 10th and I'd like to upgrade 10 of those rooms from standard to deluxe rooms. Can you help me with this modification?
    user_context: |
        You are Margaret Chen, a group coordinator contacting support to request a room type upgrade for your group booking.

        CONTEXT:
        - Group booking ID: GRP-70348247
        - You want to upgrade 10 of the 18 rooms from standard room to deluxe room
        - Check-in date: October 10, 2025
        - Hotel: Riverside Conference Center in Chicago

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent explains that hotel approval is needed and the request is being escalated, acknowledge this and accept waiting for the hotel's response.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-70001001
              booking_reference: BKG-70001001
              customer_id: CUS-45678901
              hotel_id: HTL-67891234
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-13T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_value: '450.00'
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-70348247
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
          booking_api_group_bookings:
            - id: GRP-70348247
              group_booking_id: GRP-70348247
              coordinator_name: Margaret Chen
              coordinator_email: margaret.chen@eventplanners.org
              coordinator_phone: +1-617-284-9153
              total_rooms: 18
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-13T11:00:00Z'
              hotel_id: HTL-67891234
              booking_references:
                - BKG-70001001
                - BKG-70001002
                - BKG-70001003
                - BKG-70001004
                - BKG-70001005
                - BKG-70001006
                - BKG-70001007
                - BKG-70001008
                - BKG-70001009
                - BKG-70001010
                - BKG-70001011
                - BKG-70001012
                - BKG-70001013
                - BKG-70001014
                - BKG-70001015
                - BKG-70001016
                - BKG-70001017
                - BKG-70001018
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-70001001
              hotel_id: HTL-67891234
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-10T00:00:00Z'
              available_count: 12
              price_per_night: '200.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-70001002
              hotel_id: HTL-67891234
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-11T00:00:00Z'
              available_count: 12
              price_per_night: '200.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-70001003
              hotel_id: HTL-67891234
              room_type: deluxe_room
              board_type: with_breakfast
              date: '2025-10-12T00:00:00Z'
              available_count: 12
              price_per_night: '200.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-45678901
              customer_id: CUS-45678901
              email: margaret.chen@eventplanners.org
              full_name: Margaret Chen
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '12500.00'
              total_bookings_count: 5
              preferences:
                - conference facilities
                - late breakfast
              special_notes:
                - Group event coordinator - corporate events
              complaint_count: 0
              last_booking_date: '2025-09-15T14:00:00Z'
              created_at: '2024-06-20T10:00:00Z'
              updated_at: '2025-09-15T14:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-67891234
              hotel_id: HTL-67891234
              hotel_name: Riverside Conference Center
              location: Chicago
              partner_tier: standard
              contact_name: Thomas Reynolds
              contact_email: reservations@riversidecc.com
              contact_phone: +1-312-847-2916
              escalation_contact: manager@riversidecc.com
              amenities:
                - wifi
                - conference_room
                - restaurant
                - gym
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
          payment_api_transactions: []
          zendesk_tickets:
            - id: TCK-71093248
              subject: Billing Question - Group Booking GRP-70348247
              description: Question about group booking invoice charges and payment breakdown
              status: solved
              priority: normal
              type: question
              requester_id: USR-70348001
              assignee_id: AG-83945
              organization_id: null
              tags:
                - billing
                - group-booking
              created_at: '2025-09-26T10:00:00Z'
              updated_at: '2025-09-27T14:00:00Z'
              due_at: null
              booking_reference: BKG-70001001
              hotel_id: HTL-67891234
              check_in_date: '2025-10-10T15:00:00Z'
              booking_value: 8100.0
              request_type_detail: billing-inquiry
              corporate_account_id: null
              group_booking_id: GRP-70348247
              resolution_action: information-provided
              refund_amount: 0
              escalation_reason: null
          zendesk_users:
            - id: USR-70348001
              name: Margaret Chen
              email: margaret.chen@eventplanners.org
              role: end-user
              organization_id: null
              phone: +1-617-284-9153
              verified: true
              active: true
              created_at: '2024-06-20T10:00:00Z'
              updated_at: '2024-06-20T10:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-70348247
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-67891234
            - tool: crm_api_get_customer_profile
              parameters:
                email: margaret.chen@eventplanners.org
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-67891234
                check_in_date: '2025-10-10T15:00:00Z'
                check_out_date: '2025-10-13T11:00:00Z'
                room_type: deluxe_room
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-70001001
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'margaret.chen@eventplanners.org'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-70348247'
                orderby: created_at desc
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Room type modification request - GRP-70348247
                  description: 'Group coordinator requests room type upgrade from standard_room to deluxe_room for 10 of 18 rooms in group booking GRP-70348247. Hotel: HTL-67891234 (standard tier). Check-in: 2025-10-10. Total rooms in group: 18 (large group, ≥16 rooms). Modification requires hotel partner approval per large group policy.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-70348001
                  assignee_id: AG-83945
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                  booking_reference: BKG-70001001
                  hotel_id: HTL-67891234
                  check_in_date: '2025-10-10T15:00:00Z'
                  booking_value: 4500.0
                  request_type_detail: modify-room-type
                  group_booking_id: GRP-70348247
                  refund_amount: 0
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-67891234
                booking_reference: BKG-70001001
                issue_type: large-group-booking
                description: 'Room type modification request for large group (18 rooms). Coordinator requests upgrading 10 rooms from standard_room to deluxe_room. Check-in: 2025-10-10 (9 days away). Modification fee: $0. Pending hotel approval before executing changes.'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: hold
                  description: 'Group coordinator requests room type upgrade from standard_room to deluxe_room for 10 of 18 rooms in group booking GRP-70348247. Hotel: HTL-67891234 (standard tier). Check-in: 2025-10-10. Total rooms in group: 18 (large group, ≥16 rooms). Modification requires hotel partner approval per large group policy.


                    Escalated to hotel partner. Escalation ticket: ZDSK-00000014. Awaiting hotel confirmation to proceed with modification. No modification fee applies (request made ≥7 days before check-in).'
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                    - hotel-partner-escalation
                  escalation_reason: large-group-booking
    """

    validate_database(x)


def test_gbm_014(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Rebecca Martinez, the group coordinator for booking GRP-27484677. I urgently need to change our check-in date from October 4th to October 5th for all 16 rooms - our conference schedule has changed and we need this resolved quickly. I actually reached out about this a couple days ago but haven't heard back with a resolution. My email is rebecca.martinez@eventgroup.com. Can you please help expedite this?
    user_context: |
        You are Rebecca Martinez, a group coordinator who needs to change the check-in date for your 16-room group booking from October 4 to October 5 due to a conference schedule change. You previously contacted support about this 2 days ago but the issue is still unresolved.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-27484677
              coordinator_name: Rebecca Martinez
              coordinator_email: rebecca.martinez@eventgroup.com
              coordinator_phone: +1-415-892-7341
              total_rooms: 16
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              hotel_id: HTL-00027484
              booking_references:
                - BKG-00027001
                - BKG-00027002
                - BKG-00027003
                - BKG-00027004
                - BKG-00027005
                - BKG-00027006
                - BKG-00027007
                - BKG-00027008
                - BKG-00027009
                - BKG-00027010
                - BKG-00027011
                - BKG-00027012
                - BKG-00027013
                - BKG-00027014
                - BKG-00027015
                - BKG-00027016
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00027484
              hotel_name: Downtown Conference Center Hotel
              location: San Francisco
              partner_tier: standard
              contact_name: Michael Rivera
              contact_email: reservations@downtownconference.com
              contact_phone: +1-415-723-8456
              escalation_contact: manager@downtownconference.com
              amenities:
                - wifi
                - conference_room
                - parking
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00027484
              customer_id: CUS-00027484
              email: rebecca.martinez@eventgroup.com
              full_name: Rebecca Martinez
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '2450.75'
              total_bookings_count: 8
              preferences:
                - early check-in
                - conference facilities
              special_notes:
                - group coordinator for corporate events
              complaint_count: 0
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2024-06-15T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          zendesk_tickets:
            - id: '37826398'
              subject: Date modification request - GRP-27484677
              description: Coordinator requests check-in date change from October 4 to October 5 for all 16 rooms due to conference schedule change.
              status: pending
              priority: normal
              type: task
              requester_id: USR-00027484
              assignee_id: null
              organization_id: null
              tags:
                - group-coordinator
                - date-change
              created_at: '2025-09-29T10:00:00Z'
              updated_at: '2025-09-29T10:00:00Z'
              due_at: null
              booking_reference: BKG-00027001
              hotel_id: HTL-00027484
              check_in_date: '2025-10-05T15:00:00Z'
              booking_value: 4800.0
              request_type_detail: modify-dates
              corporate_account_id: null
              group_booking_id: GRP-27484677
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-00027484
              name: Rebecca Martinez
              email: rebecca.martinez@eventgroup.com
              role: end-user
              organization_id: null
              phone: +1-415-892-7341
              verified: true
              active: true
              created_at: '2024-06-15T10:00:00Z'
              updated_at: '2024-06-15T10:00:00Z'
          booking_api_bookings:
            - id: BKG-00100001
              booking_reference: BKG-00027001
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100002
              booking_reference: BKG-00027002
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100003
              booking_reference: BKG-00027003
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100004
              booking_reference: BKG-00027004
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100005
              booking_reference: BKG-00027005
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100006
              booking_reference: BKG-00027006
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100007
              booking_reference: BKG-00027007
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100008
              booking_reference: BKG-00027008
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100009
              booking_reference: BKG-00027009
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100010
              booking_reference: BKG-00027010
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100011
              booking_reference: BKG-00027011
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100012
              booking_reference: BKG-00027012
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100013
              booking_reference: BKG-00027013
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100014
              booking_reference: BKG-00027014
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100015
              booking_reference: BKG-00027015
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00100016
              booking_reference: BKG-00027016
              customer_id: CUS-00027484
              hotel_id: HTL-00027484
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-07T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-27484677
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          lookup_bookings: []
          lookup_hotels: []
          lookup_group_bookings: []
          lookup_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-27484677
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00027484
            - tool: crm_api_get_customer_profile
              parameters:
                email: rebecca.martinez@eventgroup.com
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-00027001'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'rebecca.martinez@eventgroup.com'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '37826398'
                item:
                  status: open
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-00027484
                booking_reference: BKG-00027001
                issue_type: large-group-booking
                description: Group coordinator requests check-in date change from 2025-10-04 to 2025-10-05 for all 16 rooms in group GRP-27484677 due to conference schedule change. Large group modification (≥16 rooms) requires hotel partner approval per policy. If approved, modification fee will be $400.00 (16 rooms × $25 × 1.0 standard tier multiplier). Please confirm availability and approval for this date change.
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '37826398'
                item:
                  status: hold
                  priority: normal
                  type: task
                  assignee_id: AG-83945
                  description: 'Group coordinator requests check-in date change from 2025-10-04 to 2025-10-05 for all 16 rooms. Group booking GRP-27484677, 16 rooms at standard partner hotel. Large group modification requires mandatory hotel approval per policy Section 4.7.2. Escalated to hotel partner. Escalation reference: ZDSK-00000001. Pending hotel approval for date change. If approved, modification fee: $400.00 (16 rooms × $25 base fee × 1.0 standard multiplier). Waiting on: Hotel partner approval.'
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                    - hotel-partner-escalation
                  booking_reference: BKG-00027001
                  hotel_id: HTL-00027484
                  check_in_date: '2025-10-05T15:00:00Z'
                  booking_value: 4800.0
                  request_type_detail: modify-dates
                  group_booking_id: GRP-27484677
                  refund_amount: 0
                  escalation_reason: large-group-booking
    """

    validate_database(x)


def test_gbm_015(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I'm the coordinator for a group booking and need to make a change. My name is Sarah Johnson, email sarah.johnson@eventcorp.net. Our group booking ID is GRP-21465840. We have 5 rooms booked but I need to upgrade 2 of them from deluxe rooms to suites. The other 3 rooms should stay as they are. Can you help with this?
    user_context: |
        You are Sarah Johnson, a group coordinator for a corporate event. You're contacting support to upgrade 2 of the 5 rooms in your group booking from deluxe rooms to suites. You don't have a preference for which specific 2 rooms get upgraded - you're fine with the agent selecting them.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent confirms any charges or fees for the modification, accept and confirm you agree to proceed.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-21465840
              coordinator_name: Sarah Johnson
              coordinator_email: sarah.johnson@eventcorp.net
              coordinator_phone: +1-312-847-3921
              total_rooms: 5
              check_in_date: '2025-10-07T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              hotel_id: HTL-00045678
              booking_references:
                - BKG-00001001
                - BKG-00001002
                - BKG-00001003
                - BKG-00001004
                - BKG-00001005
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00045678
              hotel_id: HTL-00045678
              hotel_name: Riverside Grand Hotel
              location: Chicago
              partner_tier: premium
              contact_name: Victoria Blake
              contact_email: manager@riversidegrand.com
              contact_phone: +1-312-594-7823
              escalation_contact: director@riversidegrand.com
              amenities:
                - pool
                - gym
                - spa
                - restaurant
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00067890
              customer_id: CUS-00067890
              email: sarah.johnson@eventcorp.net
              full_name: Sarah Johnson
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '4500.00'
              total_bookings_count: 8
              preferences:
                - early check-in
                - high floor
              special_notes:
                - frequent group coordinator
              complaint_count: 0
              last_booking_date: '2025-09-15T14:00:00Z'
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-09-15T14:00:00Z'
            - id: CUS-00067892
              customer_id: CUS-00067892
              email: michael.torres@eventcorp.net
              full_name: Michael Torres
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '1250.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2025-03-10T09:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: CUS-00067893
              customer_id: CUS-00067893
              email: jennifer.martinez@eventcorp.net
              full_name: Jennifer Martinez
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '850.00'
              total_bookings_count: 2
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2025-05-20T14:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: CUS-00067894
              customer_id: CUS-00067894
              email: david.wong@eventcorp.net
              full_name: David Wong
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '680.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2025-07-12T11:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: CUS-00067895
              customer_id: CUS-00067895
              email: rachel.kim@eventcorp.net
              full_name: Rachel Kim
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '1100.00'
              total_bookings_count: 2
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2025-04-08T16:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-00001001
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-07T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              booking_value: '340.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-21465840
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-00000007
              booking_reference: BKG-00001002
              customer_id: CUS-00067892
              hotel_id: HTL-00045678
              check_in_date: '2025-10-07T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              booking_value: '340.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-21465840
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-00000008
              booking_reference: BKG-00001003
              customer_id: CUS-00067893
              hotel_id: HTL-00045678
              check_in_date: '2025-10-07T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              booking_value: '340.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-21465840
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-00000009
              booking_reference: BKG-00001004
              customer_id: CUS-00067894
              hotel_id: HTL-00045678
              check_in_date: '2025-10-07T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              booking_value: '340.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-21465840
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-00000010
              booking_reference: BKG-00001005
              customer_id: CUS-00067895
              hotel_id: HTL-00045678
              check_in_date: '2025-10-07T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              booking_value: '340.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-21465840
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000101
              hotel_id: HTL-00045678
              room_type: suite
              board_type: with_breakfast
              date: '2025-10-07T00:00:00Z'
              available_count: 4
              price_per_night: '280.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000102
              hotel_id: HTL-00045678
              room_type: suite
              board_type: with_breakfast
              date: '2025-10-08T00:00:00Z'
              available_count: 4
              price_per_night: '280.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000103
              hotel_id: HTL-00045678
              room_type: suite
              board_type: without_breakfast
              date: '2025-10-07T00:00:00Z'
              available_count: 4
              price_per_night: '250.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000104
              hotel_id: HTL-00045678
              room_type: suite
              board_type: without_breakfast
              date: '2025-10-08T00:00:00Z'
              available_count: 4
              price_per_night: '250.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000105
              hotel_id: HTL-00045678
              room_type: suite
              board_type: half_board
              date: '2025-10-07T00:00:00Z'
              available_count: 4
              price_per_night: '320.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000106
              hotel_id: HTL-00045678
              room_type: suite
              board_type: half_board
              date: '2025-10-08T00:00:00Z'
              available_count: 4
              price_per_night: '320.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000107
              hotel_id: HTL-00045678
              room_type: suite
              board_type: full_board
              date: '2025-10-07T00:00:00Z'
              available_count: 4
              price_per_night: '380.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000108
              hotel_id: HTL-00045678
              room_type: suite
              board_type: full_board
              date: '2025-10-08T00:00:00Z'
              available_count: 4
              price_per_night: '380.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Sarah Johnson
              email: sarah.johnson@eventcorp.net
              role: end-user
              organization_id: ORG-10000005
              phone: +1-312-847-3921
              verified: true
              active: true
              created_at: '2024-08-01T00:00:00Z'
              updated_at: '2024-08-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-21465840
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00045678
            - tool: crm_api_get_customer_profile
              parameters:
                email: sarah.johnson@eventcorp.net
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00001001
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00001002
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00045678
                check_in_date: '2025-10-07T15:00:00Z'
                check_out_date: '2025-10-09T11:00:00Z'
                room_type: suite
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-00001001'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'sarah.johnson@eventcorp.net'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Room type modification request - Group GRP-21465840
                  description: 'Group coordinator requests to change room type from deluxe_room to suite for 2 rooms in group booking GRP-21465840. Rooms selected in ascending order: BKG-00001001 and BKG-00001002. Check-in: 2025-10-07 (6 days from now). Premium hotel partner.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                  booking_reference: BKG-00001001
                  hotel_id: HTL-00045678
                  check_in_date: '2025-10-07T15:00:00Z'
                  group_booking_id: GRP-21465840
                  request_type_detail: modify-room-type
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00001001
                room_type: suite
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00001002
                room_type: suite
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-00001001
                charge_amount: '465.00'
                reason: group_modification_fee
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  description: 'Group coordinator requests to change room type from deluxe_room to suite for 2 rooms in group booking GRP-21465840. Rooms selected in ascending order: BKG-00001001 and BKG-00001002. Check-in: 2025-10-07 (6 days from now). Premium hotel partner. Resolution: Successfully modified 2 rooms from deluxe_room to suite. Group modification fee: $25.00 (base $25 × 2 rooms × 0.5 premium multiplier). Price difference: $440.00. Total charged: $465.00. Transaction ID: TXN-00000008.'
                  booking_value: 1120.0
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_gbm_016(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Patricia Morgan, the group coordinator for booking GRP-44997278. My email is patricia.morgan@travelsync.com. I need to upgrade the meal plan for 3 of our 10 rooms from without breakfast to full board. The other 7 rooms should stay as they are. Can you help me with this?
    user_context: |
        You are Patricia Morgan, a group coordinator contacting support to request a partial board type modification for your group booking. You want to change 3 out of 10 rooms from without_breakfast to full_board. You do not have a preference for which specific rooms get upgraded - you're fine with any 3 rooms being selected.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent informs you about charges for the upgrade, acknowledge and accept them.
        - If asked to confirm the modification, confirm it.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-44997278
              coordinator_name: Patricia Morgan
              coordinator_email: patricia.morgan@travelsync.com
              coordinator_phone: +1-617-482-7391
              total_rooms: 10
              check_in_date: '2025-10-09T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              hotel_id: HTL-00044997
              booking_references:
                - BKG-00100001
                - BKG-00100002
                - BKG-00100003
                - BKG-00100004
                - BKG-00100005
                - BKG-00100006
                - BKG-00100007
                - BKG-00100008
                - BKG-00100009
                - BKG-00100010
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
          booking_api_bookings:
            - id: BKG-00100001
              booking_reference: BKG-00100001
              customer_id: CUS-00055001
              hotel_id: HTL-00044997
              check_in_date: '2025-10-09T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '450.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-44997278
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-00100002
              booking_reference: BKG-00100002
              customer_id: CUS-00055002
              hotel_id: HTL-00044997
              check_in_date: '2025-10-09T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '450.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-44997278
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-00100003
              booking_reference: BKG-00100003
              customer_id: CUS-00055003
              hotel_id: HTL-00044997
              check_in_date: '2025-10-09T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '450.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-44997278
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-00100004
              booking_reference: BKG-00100004
              customer_id: CUS-00055004
              hotel_id: HTL-00044997
              check_in_date: '2025-10-09T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '450.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-44997278
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-00100005
              booking_reference: BKG-00100005
              customer_id: CUS-00055005
              hotel_id: HTL-00044997
              check_in_date: '2025-10-09T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '450.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-44997278
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-00100006
              booking_reference: BKG-00100006
              customer_id: CUS-00055006
              hotel_id: HTL-00044997
              check_in_date: '2025-10-09T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '450.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-44997278
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-00100007
              booking_reference: BKG-00100007
              customer_id: CUS-00055007
              hotel_id: HTL-00044997
              check_in_date: '2025-10-09T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '450.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-44997278
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-00100008
              booking_reference: BKG-00100008
              customer_id: CUS-00055008
              hotel_id: HTL-00044997
              check_in_date: '2025-10-09T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '450.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-44997278
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-00100009
              booking_reference: BKG-00100009
              customer_id: CUS-00055009
              hotel_id: HTL-00044997
              check_in_date: '2025-10-09T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '450.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-44997278
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-00100010
              booking_reference: BKG-00100010
              customer_id: CUS-00055010
              hotel_id: HTL-00044997
              check_in_date: '2025-10-09T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '450.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-44997278
              modification_history: []
              special_requests: []
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-00044997
              room_type: standard_room
              board_type: full_board
              date: '2025-10-09T00:00:00Z'
              available_count: 5
              price_per_night: '200.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-00044997
              room_type: standard_room
              board_type: full_board
              date: '2025-10-10T00:00:00Z'
              available_count: 5
              price_per_night: '200.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000008
              hotel_id: HTL-00044997
              room_type: standard_room
              board_type: full_board
              date: '2025-10-11T00:00:00Z'
              available_count: 5
              price_per_night: '200.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000009
              hotel_id: HTL-00044997
              room_type: standard_room
              board_type: without_breakfast
              date: '2025-10-09T00:00:00Z'
              available_count: 10
              price_per_night: '150.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000010
              hotel_id: HTL-00044997
              room_type: standard_room
              board_type: without_breakfast
              date: '2025-10-10T00:00:00Z'
              available_count: 10
              price_per_night: '150.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000011
              hotel_id: HTL-00044997
              room_type: standard_room
              board_type: without_breakfast
              date: '2025-10-11T00:00:00Z'
              available_count: 10
              price_per_night: '150.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00044997
              hotel_id: HTL-00044997
              hotel_name: Standard City Hotel
              location: Boston
              partner_tier: standard
              contact_name: Katherine Wells
              contact_email: info@standardcityhotel.com
              contact_phone: +1-617-389-4210
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00055001
              email: patricia.morgan@travelsync.com
              full_name: Patricia Morgan
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '2850.75'
              total_bookings_count: 8
              preferences:
                - early check-in
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-01T14:00:00Z'
              created_at: '2024-03-10T10:00:00Z'
              updated_at: '2025-09-01T14:00:00Z'
            - id: CUS-00000007
              customer_id: CUS-00055002
              email: mark.sullivan@travelsync.com
              full_name: Mark Sullivan
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '1250.00'
              total_bookings_count: 4
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2024-05-20T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: CUS-00000008
              customer_id: CUS-00055003
              email: jennifer.brooks@travelsync.com
              full_name: Jennifer Brooks
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '980.50'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2024-06-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: CUS-00000009
              customer_id: CUS-00055004
              email: robert.chang@travelsync.com
              full_name: Robert Chang
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '750.00'
              total_bookings_count: 2
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2024-07-01T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: CUS-00000010
              customer_id: CUS-00055005
              email: amanda.foster@travelsync.com
              full_name: Amanda Foster
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '620.00'
              total_bookings_count: 2
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2024-07-10T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: CUS-00000011
              customer_id: CUS-00055006
              email: kevin.martinez@travelsync.com
              full_name: Kevin Martinez
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '540.00'
              total_bookings_count: 2
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2024-07-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: CUS-00000012
              customer_id: CUS-00055007
              email: stephanie.nguyen@travelsync.com
              full_name: Stephanie Nguyen
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '480.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2024-08-01T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: CUS-00000013
              customer_id: CUS-00055008
              email: brian.wilson@travelsync.com
              full_name: Brian Wilson
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '450.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2024-08-05T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: CUS-00000014
              customer_id: CUS-00055009
              email: michelle.taylor@travelsync.com
              full_name: Michelle Taylor
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '450.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2024-08-10T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: CUS-00000015
              customer_id: CUS-00055010
              email: daniel.lee@travelsync.com
              full_name: Daniel Lee
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '450.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2024-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Patricia Morgan
              email: patricia.morgan@travelsync.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-617-482-7391
              verified: true
              active: true
              created_at: '2024-03-10T00:00:00Z'
              updated_at: '2024-03-10T00:00:00Z'
          zendesk_tickets:
            - id: TCK-75588675
              subject: Board type modification request - GRP-44997278
              description: Group coordinator requested partial board type modification for group booking.
              status: solved
              priority: normal
              type: task
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: ORG-10000002
              tags:
                - check-in-upcoming
                - group-coordinator
              created_at: '2025-09-28T10:00:00Z'
              updated_at: '2025-09-28T14:00:00Z'
              due_at: null
              booking_reference: BKG-00100001
              hotel_id: HTL-00044997
              check_in_date: '2025-10-09T15:00:00Z'
              booking_value: 450.0
              request_type_detail: modify-board-type
              corporate_account_id: null
              group_booking_id: GRP-44997278
              resolution_action: information-provided
              refund_amount: 0
              escalation_reason: null
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-44997278
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00100001
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00044997
            - tool: crm_api_get_customer_profile
              parameters:
                email: patricia.morgan@travelsync.com
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'patricia.morgan@travelsync.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-44997278'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-75588675
                item:
                  status: open
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00044997
                check_in_date: '2025-10-09T15:00:00Z'
                check_out_date: '2025-10-12T11:00:00Z'
                room_type: standard_room
                board_type: full_board
                adults_count: 2
                children_count: 0
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00100001
                board_type: full_board
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00100002
                board_type: full_board
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-00100003
                board_type: full_board
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-00100001
                charge_amount: '450.00'
                reason: price_difference
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-75588675
                item:
                  status: solved
                  priority: normal
                  type: task
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                  description: 'Group coordinator requested board type change from without_breakfast to full_board for 3 of 10 rooms in group booking GRP-44997278. Customer tier: standard. Hotel tier: standard. Time until check-in: 8 days (≥7 days). Room selection: First 3 bookings in ascending order (BKG-00100001, BKG-00100002, BKG-00100003) per policy. Group modification fee: $0 (≥7 days). Price difference charged: $450.00 (TXN-00000008). All 3 rooms successfully modified to full_board.'
                  booking_reference: BKG-00100001
                  hotel_id: HTL-00044997
                  check_in_date: '2025-10-09T15:00:00Z'
                  booking_value: 1800.0
                  request_type_detail: modify-board-type
                  group_booking_id: GRP-44997278
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_gbm_017(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I'm Rachel Henderson, the coordinator for group booking GRP-33963605. My email is rachel.henderson@eventsco.com. I need to change the check-in date for only 4 of our 8 rooms - some of our team members need to arrive a day earlier, on October 5th instead of October 6th. The other 4 rooms should stay on the original October 6th check-in date. Can you help me with this?
    user_context: |
        You are Rachel Henderson, a group coordinator for an events company. You have an 8-room group booking at City Budget Inn and need to modify the check-in date for only 4 of the rooms to arrive one day earlier (October 5 instead of October 6). The remaining 4 rooms should keep the original check-in date.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If the agent informs you that hotel approval is required or that there will be fees, acknowledge this and confirm you understand the process. You are willing to pay the applicable fees if the modification is approved.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-33963605
              coordinator_name: Rachel Henderson
              coordinator_email: rachel.henderson@eventsco.com
              coordinator_phone: +1-312-847-6294
              total_rooms: 8
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              hotel_id: HTL-00045678
              booking_references:
                - BKG-00055001
                - BKG-00055002
                - BKG-00055003
                - BKG-00055004
                - BKG-00055005
                - BKG-00055006
                - BKG-00055007
                - BKG-00055008
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00045678
              hotel_id: HTL-00045678
              hotel_name: City Budget Inn
              location: Chicago
              partner_tier: budget
              contact_name: Thomas Wright
              contact_email: frontdesk@citybudgetinn.com
              contact_phone: +1-312-492-7183
              escalation_contact: manager@citybudgetinn.com
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2024-06-15T10:00:00Z'
              updated_at: '2024-06-15T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00067890
              customer_id: CUS-00067890
              email: rachel.henderson@eventsco.com
              full_name: Rachel Henderson
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '2500.00'
              total_bookings_count: 8
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Rachel Henderson
              email: rachel.henderson@eventsco.com
              role: end-user
              organization_id: null
              phone: +1-312-847-6294
              verified: true
              active: true
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-00055001
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '450.00'
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-33963605
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000007
              booking_reference: BKG-00055002
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '450.00'
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-33963605
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000008
              booking_reference: BKG-00055003
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '450.00'
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-33963605
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000009
              booking_reference: BKG-00055004
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '450.00'
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-33963605
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000010
              booking_reference: BKG-00055005
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '450.00'
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-33963605
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000011
              booking_reference: BKG-00055006
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '450.00'
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-33963605
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000012
              booking_reference: BKG-00055007
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '450.00'
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-33963605
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000013
              booking_reference: BKG-00055008
              customer_id: CUS-00067890
              hotel_id: HTL-00045678
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '450.00'
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-33963605
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          booking_api_hotel_inventory:
            - id: INV-00000006
              hotel_id: HTL-00045678
              room_type: standard_room
              board_type: with_breakfast
              date: '2025-10-05T00:00:00Z'
              available_count: 6
              price_per_night: '150.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000007
              hotel_id: HTL-00045678
              room_type: standard_room
              board_type: with_breakfast
              date: '2025-10-06T00:00:00Z'
              available_count: 6
              price_per_night: '150.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000008
              hotel_id: HTL-00045678
              room_type: standard_room
              board_type: with_breakfast
              date: '2025-10-07T00:00:00Z'
              available_count: 6
              price_per_night: '150.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000009
              hotel_id: HTL-00045678
              room_type: standard_room
              board_type: with_breakfast
              date: '2025-10-08T00:00:00Z'
              available_count: 6
              price_per_night: '150.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000010
              hotel_id: HTL-00045678
              room_type: standard_room
              board_type: without_breakfast
              date: '2025-10-05T00:00:00Z'
              available_count: 6
              price_per_night: '130.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000011
              hotel_id: HTL-00045678
              room_type: standard_room
              board_type: without_breakfast
              date: '2025-10-06T00:00:00Z'
              available_count: 6
              price_per_night: '130.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000012
              hotel_id: HTL-00045678
              room_type: standard_room
              board_type: without_breakfast
              date: '2025-10-07T00:00:00Z'
              available_count: 6
              price_per_night: '130.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000013
              hotel_id: HTL-00045678
              room_type: standard_room
              board_type: without_breakfast
              date: '2025-10-08T00:00:00Z'
              available_count: 6
              price_per_night: '130.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000014
              hotel_id: HTL-00045678
              room_type: standard_room
              board_type: half_board
              date: '2025-10-05T00:00:00Z'
              available_count: 6
              price_per_night: '175.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000015
              hotel_id: HTL-00045678
              room_type: standard_room
              board_type: half_board
              date: '2025-10-06T00:00:00Z'
              available_count: 6
              price_per_night: '175.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000016
              hotel_id: HTL-00045678
              room_type: standard_room
              board_type: half_board
              date: '2025-10-07T00:00:00Z'
              available_count: 6
              price_per_night: '175.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
            - id: INV-00000017
              hotel_id: HTL-00045678
              room_type: standard_room
              board_type: half_board
              date: '2025-10-08T00:00:00Z'
              available_count: 6
              price_per_night: '175.00'
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-33963605
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00045678
            - tool: crm_api_get_customer_profile
              parameters:
                email: rachel.henderson@eventsco.com
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'rachel.henderson@eventsco.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-33963605'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00055001
            - tool: booking_api_check_hotel_availability
              parameters:
                hotel_id: HTL-00045678
                check_in_date: '2025-10-05T15:00:00Z'
                check_out_date: '2025-10-09T11:00:00Z'
                room_type: standard_room
                board_type: with_breakfast
                adults_count: 2
                children_count: 0
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Group date modification request - GRP-33963605
                  description: 'Group coordinator requests check-in date change for 4 of 8 rooms from October 6, 2025 to October 5, 2025. Hotel: City Budget Inn (HTL-00045678). Budget tier property - escalation required for medium group modification within 7 days of check-in. Rooms to be modified (ascending order selection): BKG-00055001, BKG-00055002, BKG-00055003, BKG-00055004. Remaining 4 rooms keep original check-in date of October 6. Estimated modification fee: $150.00. Estimated price difference for additional night: $600.00. Availability confirmed for new dates. Awaiting hotel partner approval.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - check-in-upcoming
                    - group-coordinator
                  booking_reference: BKG-00055001
                  hotel_id: HTL-00045678
                  check_in_date: '2025-10-06T15:00:00Z'
                  booking_value: 1800.0
                  request_type_detail: modify-dates
                  group_booking_id: GRP-33963605
                  escalation_reason: hotel-confirmation-required
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-00045678
                booking_reference: BKG-00055001
                issue_type: hotel-confirmation-required
                description: 'Group booking GRP-33963605: Coordinator requests to change check-in date for 4 of 8 rooms from October 6, 2025 to October 5, 2025. Rooms: BKG-00055001, BKG-00055002, BKG-00055003, BKG-00055004. Room type: standard_room with breakfast. Remaining 4 rooms keep original check-in. Please confirm if this partial group modification is approved. Estimated modification fee: $150.00. Price difference for additional night (4 rooms): $600.00.'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: hold
                  tags:
                    - check-in-upcoming
                    - group-coordinator
                    - hotel-partner-escalation
                  description: 'Group coordinator requests check-in date change for 4 of 8 rooms from October 6, 2025 to October 5, 2025. Hotel: City Budget Inn (HTL-00045678). Budget tier property - escalation required for medium group modification within 7 days of check-in. Rooms to be modified (ascending order selection): BKG-00055001, BKG-00055002, BKG-00055003, BKG-00055004. Remaining 4 rooms keep original check-in date of October 6. Estimated modification fee: $150.00. Estimated price difference for additional night: $600.00. Availability confirmed for new dates. Awaiting hotel partner approval. Escalated to hotel partner. Escalation ticket ID: ZDSK-00000013. Awaiting hotel confirmation/approval. Hotel contact: manager@citybudgetinn.com, +1-312-492-7183.'
    """

    validate_database(x)


def test_gbm_018(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I'm Jennifer Martinez, the coordinator for group booking GRP-76627028. My email is jennifer.martinez@eventplanners.org. We have 15 rooms booked for our event checking in on October 4th, and I'd like to add a special request for connecting rooms for 6 of those rooms. Some of our attendees are traveling with family and would really appreciate being placed in rooms that connect. Can you help me set that up?
    user_context: |
        You are Jennifer Martinez, a group coordinator for a corporate event. You're contacting StayBridge support to add connecting room requests for 6 of the 15 rooms in your group booking GRP-76627028.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - You do not have specific room numbers or booking references in mind - you're fine with the agent selecting which 6 rooms to apply the request to.
        - You understand that connecting rooms are subject to availability and cannot be guaranteed.
        - If the agent confirms completion, thank them for their help.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-76627001
              booking_reference: BKG-76627001
              customer_id: CUS-76627002
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-76627002
              booking_reference: BKG-76627002
              customer_id: CUS-76627003
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-76627003
              booking_reference: BKG-76627003
              customer_id: CUS-76627004
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-76627004
              booking_reference: BKG-76627004
              customer_id: CUS-76627005
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-76627005
              booking_reference: BKG-76627005
              customer_id: CUS-76627006
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-76627006
              booking_reference: BKG-76627006
              customer_id: CUS-76627007
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-76627007
              booking_reference: BKG-76627007
              customer_id: CUS-76627008
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-76627008
              booking_reference: BKG-76627008
              customer_id: CUS-76627009
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-76627009
              booking_reference: BKG-76627009
              customer_id: CUS-76627010
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-76627010
              booking_reference: BKG-76627010
              customer_id: CUS-76627011
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-76627011
              booking_reference: BKG-76627011
              customer_id: CUS-76627012
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-76627012
              booking_reference: BKG-76627012
              customer_id: CUS-76627013
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-76627013
              booking_reference: BKG-76627013
              customer_id: CUS-76627014
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-76627014
              booking_reference: BKG-76627014
              customer_id: CUS-76627015
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-76627015
              booking_reference: BKG-76627015
              customer_id: CUS-76627016
              hotel_id: HTL-00012345
              group_booking_id: GRP-76627028
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              booking_value: '300.00'
              booking_status: confirmed
              adults_count: 2
              children_count: 0
              corporate_account_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_group_bookings:
            - id: GRP-76627028
              group_booking_id: GRP-76627028
              coordinator_name: Jennifer Martinez
              coordinator_email: jennifer.martinez@eventplanners.org
              coordinator_phone: +1-408-392-7184
              total_rooms: 15
              check_in_date: '2025-10-04T15:00:00Z'
              check_out_date: '2025-10-06T11:00:00Z'
              hotel_id: HTL-00012345
              booking_references:
                - BKG-76627001
                - BKG-76627002
                - BKG-76627003
                - BKG-76627004
                - BKG-76627005
                - BKG-76627006
                - BKG-76627007
                - BKG-76627008
                - BKG-76627009
                - BKG-76627010
                - BKG-76627011
                - BKG-76627012
                - BKG-76627013
                - BKG-76627014
                - BKG-76627015
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-76627001
              customer_id: CUS-76627001
              email: jennifer.martinez@eventplanners.org
              full_name: Jennifer Martinez
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '12500.00'
              total_bookings_count: 8
              preferences:
                - early check-in
              special_notes:
                - coordinates corporate events
              complaint_count: 0
              last_booking_date: '2025-09-20T14:00:00Z'
              created_at: '2024-06-15T10:00:00Z'
              updated_at: '2025-09-20T10:00:00Z'
            - id: CUS-76627002
              customer_id: CUS-76627002
              email: michael.tanaka@westcoast.com
              full_name: Michael Tanaka
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '600.00'
              total_bookings_count: 2
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-08-01T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: CUS-76627003
              customer_id: CUS-76627003
              email: rachel.foster@innovatech.io
              full_name: Rachel Foster
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '450.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-09-10T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: CUS-76627004
              customer_id: CUS-76627004
              email: steven.brooks@brightsystems.net
              full_name: Steven Brooks
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '300.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-09-12T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: CUS-76627005
              customer_id: CUS-76627005
              email: amanda.reyes@cloudven.com
              full_name: Amanda Reyes
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '300.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-09-12T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: CUS-76627006
              customer_id: CUS-76627006
              email: kevin.nakamura@peaklogic.com
              full_name: Kevin Nakamura
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '300.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-09-12T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: CUS-76627007
              customer_id: CUS-76627007
              email: patricia.allen@vistacorp.org
              full_name: Patricia Allen
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '300.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-09-12T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels: []
          payment_api_transactions: []
          zendesk_tickets:
            - id: TCK-95171870
              subject: Pre-booking inquiry for group GRP-76627028
              description: Coordinator inquiring about room availability and pricing for upcoming group event
              status: solved
              priority: normal
              type: question
              requester_id: USR-76627001
              assignee_id: AG-83945
              organization_id: null
              tags:
                - group-coordinator
                - inquiry
              created_at: '2025-09-23T10:00:00Z'
              updated_at: '2025-09-24T14:00:00Z'
              due_at: null
              booking_reference: null
              hotel_id: HTL-00012345
              check_in_date: '2025-10-04T15:00:00Z'
              booking_value: null
              request_type_detail: other
              corporate_account_id: null
              group_booking_id: GRP-76627028
              resolution_action: information-provided
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-76627001
              name: Jennifer Martinez
              email: jennifer.martinez@eventplanners.org
              role: end-user
              organization_id: null
              phone: +1-408-392-7184
              verified: true
              active: true
              created_at: '2024-06-15T00:00:00Z'
              updated_at: '2024-06-15T00:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-76627028
            - tool: crm_api_get_customer_profile
              parameters:
                email: jennifer.martinez@eventplanners.org
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00012345
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'jennifer.martinez@eventplanners.org'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-76627028'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Special request - connecting rooms for group GRP-76627028
                  description: 'Group coordinator requesting connecting rooms for 6 of 15 rooms in group booking GRP-76627028. Check-in: 2025-10-04. Hotel is premium tier - no hotel confirmation required. Rooms selected in ascending booking reference order per policy: BKG-76627001 through BKG-76627006. Connecting rooms are best effort, subject to availability.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-76627001
                  assignee_id: AG-83945
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                  group_booking_id: GRP-76627028
                  hotel_id: HTL-00012345
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-76627001
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-76627002
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-76627003
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-76627004
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-76627005
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-76627006
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-76627001
                special_requests:
                  - connecting rooms
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-76627002
                special_requests:
                  - connecting rooms
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-76627003
                special_requests:
                  - connecting rooms
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-76627004
                special_requests:
                  - connecting rooms
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-76627005
                special_requests:
                  - connecting rooms
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-76627006
                special_requests:
                  - connecting rooms
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  request_type_detail: add-special-request
                  resolution_action: modification-completed
                  booking_reference: BKG-76627001
                  hotel_id: HTL-00012345
                  check_in_date: '2025-10-04T15:00:00Z'
                  booking_value: 1800.0
                  group_booking_id: GRP-76627028
                  refund_amount: 0
                  tags:
                    - group-coordinator
                    - check-in-upcoming
    """

    validate_database(x)


def test_gsr_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Rachel Morrison, the coordinator for our group booking GRP-26217459. We have 12 rooms booked for a corporate retreat. I need to request a meeting room for 15 people on October 9th from 9 AM to 5 PM. We'll need a projector and whiteboard for our sessions. My email is rachel.morrison@nexustech.io. Can you help arrange this?
    user_context: |
        You are Rachel Morrison, a group coordinator for a corporate retreat. You are contacting support to request a meeting room at the hotel where your group is staying. Your group booking reference is GRP-26217459 with 12 rooms. You need a meeting room for 15 attendees on October 9, 2025 from 9 AM to 5 PM, with a projector and whiteboard.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-26217459
              coordinator_name: Rachel Morrison
              coordinator_email: rachel.morrison@nexustech.io
              coordinator_phone: +1-617-482-3791
              total_rooms: 12
              check_in_date: '2025-10-08T15:00:00Z'
              check_out_date: '2025-10-10T11:00:00Z'
              hotel_id: HTL-00045678
              booking_references:
                - BKG-00045001
                - BKG-00045002
                - BKG-00045003
                - BKG-00045004
                - BKG-00045005
                - BKG-00045006
                - BKG-00045007
                - BKG-00045008
                - BKG-00045009
                - BKG-00045010
                - BKG-00045011
                - BKG-00045012
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00045678
              hotel_name: Lakeside Conference Center
              location: Boston
              partner_tier: premium
              contact_name: Victoria Chen
              contact_email: reservations@lakesideconf.com
              contact_phone: +1-617-394-8521
              escalation_contact: manager@lakesideconf.com
              amenities:
                - wifi
                - pool
                - gym
                - restaurant
                - meeting_rooms
                - parking
                - business_center
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Rachel Morrison
              email: rachel.morrison@nexustech.io
              role: end-user
              organization_id: null
              phone: +1-617-482-3791
              verified: true
              active: true
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-00045001
              booking_reference: BKG-00045001
              customer_id: CUS-00045001
              hotel_id: HTL-00045678
              check_in_date: '2025-10-08T15:00:00Z'
              check_out_date: '2025-10-10T11:00:00Z'
              booking_value: 300.0
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-26217459
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-26217459
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00045678
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'rachel.morrison@nexustech.io'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-26217459'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Meeting room request - GRP-26217459
                  description: 'Group coordinator requests meeting room for 15 people on 2025-10-09 from 9:00 AM to 5:00 PM. Equipment required: projector, whiteboard. Group booking for corporate retreat with 12 rooms. Awaiting hotel partner confirmation.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - group-coordinator
                    - check-in-upcoming
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-00045678
                booking_reference: BKG-00045001
                issue_type: hotel-confirmation-required
                description: 'Meeting room request for group GRP-26217459 (12 rooms, corporate retreat). Request: Room for 15 attendees on 2025-10-09 from 9:00 AM to 5:00 PM. Equipment needed: projector, whiteboard. Please confirm availability and any applicable fees.'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: hold
                  description: 'Group coordinator requests meeting room for 15 people on 2025-10-09 from 9:00 AM to 5:00 PM. Equipment required: projector, whiteboard. Group booking for corporate retreat with 12 rooms. Escalated to hotel partner for confirmation. Escalation tracking ID: ZDSK-00000014. Awaiting hotel response. [Note: hotel-partner-escalation flag applies]'
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                    - hotel-partner-escalation
                  booking_reference: BKG-00045001
                  hotel_id: HTL-00045678
                  check_in_date: '2025-10-08T15:00:00Z'
                  booking_value: 3600.0
                  request_type_detail: add-special-request
                  group_booking_id: GRP-26217459
                  escalation_reason: hotel-confirmation-required
                  refund_amount: 0
    """

    validate_database(x)


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
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
          booking_api_bookings:
            - id: BKG-45781001
              booking_reference: BKG-45781001
              customer_id: CUS-89234567
              hotel_id: HTL-78451236
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-45781002
              booking_reference: BKG-45781002
              customer_id: CUS-89234568
              hotel_id: HTL-78451236
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-45781003
              booking_reference: BKG-45781003
              customer_id: CUS-89234569
              hotel_id: HTL-78451236
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-45781004
              booking_reference: BKG-45781004
              customer_id: CUS-89234570
              hotel_id: HTL-78451236
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-45781005
              booking_reference: BKG-45781005
              customer_id: CUS-89234571
              hotel_id: HTL-78451236
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-45781006
              booking_reference: BKG-45781006
              customer_id: CUS-89234572
              hotel_id: HTL-78451236
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-45781007
              booking_reference: BKG-45781007
              customer_id: CUS-89234573
              hotel_id: HTL-78451236
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
            - id: BKG-45781008
              booking_reference: BKG-45781008
              customer_id: CUS-89234574
              hotel_id: HTL-78451236
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
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
              created_at: '2025-08-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
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
              last_booking_date: '2025-08-15T10:00:00Z'
              created_at: '2023-06-15T10:00:00Z'
              updated_at: '2025-08-15T10:00:00Z'
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
              created_at: '2024-05-10T10:00:00Z'
              updated_at: '2024-05-10T10:00:00Z'
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
              created_at: '2025-09-27T10:00:00Z'
              updated_at: '2025-09-28T14:30:00Z'
              due_at: null
              booking_reference: BKG-45781001
              hotel_id: HTL-78451236
              check_in_date: '2025-10-06T15:00:00Z'
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
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
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
                filter: email eq 'patricia.morgan@conferences.org'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-61586578'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Group catering request - GRP-61586578
                  description: 'Group coordinator requests catering services for welcome dinner for 20 people on evening of 2025-10-06. Requirements: private dining area with set menu. Group booking GRP-61586578 has 8 rooms checking in 2025-10-06 at standard partner hotel.'
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
                description: 'Group booking GRP-61586578 (8 rooms, check-in 2025-10-06). Coordinator requests catering services for welcome dinner for 20 guests on evening of 2025-10-06. Requirements: private dining area with set menu service. Please confirm availability, capacity for private dining, menu options, and provide pricing.'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: hold
                  description: 'Group coordinator requests catering services for welcome dinner for 20 people on evening of 2025-10-06. Requirements: private dining area with set menu. Group booking GRP-61586578 has 8 rooms checking in 2025-10-06 at standard partner hotel. Escalated to hotel partner for confirmation - escalation ticket ZDSK-00000001. Awaiting hotel confirmation of catering availability and pricing. [hotel-partner-escalation tag applied]'
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                    - hotel-partner-escalation
                  booking_reference: BKG-45781001
                  hotel_id: HTL-78451236
                  group_booking_id: GRP-61586578
                  check_in_date: '2025-10-06T15:00:00Z'
                  booking_value: 4200.0
                  request_type_detail: add-special-request
                  escalation_reason: hotel-confirmation-required
                  refund_amount: 0
    """

    validate_database(x)


def test_gsr_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Sarah Mitchell, the group coordinator for booking GRP-11724005. My email is sarah.mitchell@horizonlogistics.com. I need to arrange airport transportation for our entire group - we have 12 guests total arriving on the same flight at 2 PM on October 10th (the check-in date). We'd like a shuttle or van service from the airport to the hotel. Can you help set this up?
    user_context: |
        You are Sarah Mitchell, a group coordinator contacting StayBridge support to arrange airport transportation for your group booking GRP-11724005. You have 12 guests arriving on a single flight at 2 PM on October 10th and need shuttle/van service from the airport to Comfort Stay Inn in Chicago.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent confirms they've escalated the request or are working on it, acknowledge and thank them.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-11724005
              coordinator_name: Sarah Mitchell
              coordinator_email: sarah.mitchell@horizonlogistics.com
              coordinator_phone: +1-312-847-6429
              total_rooms: 6
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              hotel_id: HTL-88774521
              booking_references:
                - BKG-00011001
                - BKG-00011002
                - BKG-00011003
                - BKG-00011004
                - BKG-00011005
                - BKG-00011006
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-88774521
              hotel_name: Comfort Stay Inn
              location: Chicago
              partner_tier: budget
              contact_name: Robert Chen
              contact_email: manager@comfortstayinn.com
              contact_phone: +1-312-847-6290
              escalation_contact: null
              amenities:
                - free_parking
                - wifi
                - breakfast
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-34567890
              customer_id: CUS-34567890
              email: sarah.mitchell@horizonlogistics.com
              full_name: Sarah Mitchell
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '2500.00'
              total_bookings_count: 5
              preferences:
                - early check-in
              special_notes:
                - coordinates group bookings
              complaint_count: 0
              last_booking_date: '2025-08-15T12:00:00Z'
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-08-15T12:00:00Z'
          zendesk_users:
            - id: USR-00012847
              name: Sarah Mitchell
              email: sarah.mitchell@horizonlogistics.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-312-847-6429
              verified: true
              active: true
              created_at: '2024-09-15T10:00:00Z'
              updated_at: '2024-09-15T10:00:00Z'
          booking_api_bookings:
            - id: BKG-00011001
              booking_reference: BKG-00011001
              customer_id: CUS-34567890
              hotel_id: HTL-88774521
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-11724005
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00011002
              booking_reference: BKG-00011002
              customer_id: CUS-78234561
              hotel_id: HTL-88774521
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-11724005
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00011003
              booking_reference: BKG-00011003
              customer_id: CUS-78234562
              hotel_id: HTL-88774521
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-11724005
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00011004
              booking_reference: BKG-00011004
              customer_id: CUS-78234563
              hotel_id: HTL-88774521
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-11724005
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00011005
              booking_reference: BKG-00011005
              customer_id: CUS-78234564
              hotel_id: HTL-88774521
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-11724005
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00011006
              booking_reference: BKG-00011006
              customer_id: CUS-78234565
              hotel_id: HTL-88774521
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-11724005
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_articles: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
          lookup_bookings: []
          lookup_hotels: []
          lookup_group_bookings: []
          lookup_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-11724005
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-88774521
            - tool: crm_api_get_customer_profile
              parameters:
                email: sarah.mitchell@horizonlogistics.com
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-11724005'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'sarah.mitchell@horizonlogistics.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Airport transportation request - GRP-11724005
                  description: Group coordinator requesting airport shuttle/van service for 12 guests. Group of 6 rooms at Comfort Stay Inn. All guests arriving on same flight at 2 PM on 2025-10-10 (check-in date). Transportation needed from airport to hotel.
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-00012847
                  assignee_id: AG-83945
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                  booking_reference: BKG-00011001
                  hotel_id: HTL-88774521
                  check_in_date: '2025-10-10T15:00:00Z'
                  booking_value: 1800.0
                  request_type_detail: add-special-request
                  group_booking_id: GRP-11724005
                  refund_amount: 0.0
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-88774521
                booking_reference: BKG-00011001
                issue_type: hotel-confirmation-required
                description: Group transportation request for GRP-11724005. Group coordinator requests airport shuttle/van service for 12 guests arriving on same flight at 2 PM on 2025-10-10. Need confirmation if hotel can arrange transportation and associated costs.
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: hold
                  description: 'Group coordinator requesting airport shuttle/van service for 12 guests. Group of 6 rooms at Comfort Stay Inn. All guests arriving on same flight at 2 PM on 2025-10-10 (check-in date). Transportation needed from airport to hotel. ESCALATION: Escalated to hotel partner for transportation arrangement confirmation. Escalation ticket: ZDSK-00000013. Awaiting hotel response on availability and pricing.'
                  tags:
                    - group-coordinator
                    - check-in-upcoming
                    - hotel-partner-escalation
                  escalation_reason: hotel-confirmation-required
    """

    validate_database(x)


def test_gsr_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I'm Marcus Wellington, the coordinator for a group booking we have coming up - group ID GRP-04556238. My email is marcus.wellington@techfirm.org. I reached out a couple of days ago about some special requests for our group and wanted to follow up. We need: 1) a meeting room that can accommodate 20 people on October 13th, 2) lunch catering for that meeting, and 3) airport pickup arranged for 5 VIP guests who will be arriving separately. Can you check on the status of these requests or help me get them arranged?
    user_context: |
        You are Marcus Wellington, a group coordinator for a group booking (GRP-04556238) with 15 rooms at the Metropolitan Grand Hotel. Your check-in is October 12th. You contacted support 2 days ago about three special requests (meeting room, catering, airport pickup) but haven't heard back yet, so you're following up. You want all three requests arranged before your group arrives.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-69222196
              subject: Group special requests - GRP-04556238
              description: Group coordinator requesting meeting room, catering, and airport transportation for group booking
              status: pending
              priority: normal
              type: task
              requester_id: USR-00012345
              assignee_id: null
              organization_id: null
              tags:
                - group-coordinator
                - special-requests
              created_at: '2025-09-29T13:00:00Z'
              updated_at: '2025-09-29T13:00:00Z'
              due_at: null
              booking_reference: BKG-00100001
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              booking_value: null
              request_type_detail: null
              corporate_account_id: null
              group_booking_id: GRP-04556238
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-00012345
              name: Marcus Wellington
              email: marcus.wellington@techfirm.org
              role: end-user
              organization_id: null
              phone: +1-312-528-4190
              verified: true
              active: true
              created_at: '2024-06-15T00:00:00Z'
              updated_at: '2024-06-15T00:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-04556238
              coordinator_name: Marcus Wellington
              coordinator_email: marcus.wellington@techfirm.org
              coordinator_phone: +1-312-528-4190
              total_rooms: 15
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              hotel_id: HTL-00098765
              booking_references:
                - BKG-00100001
                - BKG-00100002
                - BKG-00100003
                - BKG-00100004
                - BKG-00100005
                - BKG-00100006
                - BKG-00100007
                - BKG-00100008
                - BKG-00100009
                - BKG-00100010
                - BKG-00100011
                - BKG-00100012
                - BKG-00100013
                - BKG-00100014
                - BKG-00100015
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00098765
              hotel_name: Metropolitan Grand Hotel
              location: Chicago
              partner_tier: premium
              contact_name: Victoria Chambers
              contact_email: reservations@metropolitangrand.com
              contact_phone: +1-312-847-5200
              escalation_contact: manager@metropolitangrand.com
              amenities:
                - pool
                - gym
                - spa
                - restaurant
                - meeting_rooms
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-00100001
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000007
              booking_reference: BKG-00100002
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000008
              booking_reference: BKG-00100003
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000009
              booking_reference: BKG-00100004
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000010
              booking_reference: BKG-00100005
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000011
              booking_reference: BKG-00100006
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000012
              booking_reference: BKG-00100007
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000013
              booking_reference: BKG-00100008
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000014
              booking_reference: BKG-00100009
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000015
              booking_reference: BKG-00100010
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000016
              booking_reference: BKG-00100011
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000017
              booking_reference: BKG-00100012
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000018
              booking_reference: BKG-00100013
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000019
              booking_reference: BKG-00100014
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
            - id: BKG-00000020
              booking_reference: BKG-00100015
              customer_id: CUS-00054321
              hotel_id: HTL-00098765
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-14T11:00:00Z'
              booking_value: '320.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-04556238
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          booking_api_hotel_inventory: []
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00054321
              email: marcus.wellington@techfirm.org
              full_name: Marcus Wellington
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '12500.00'
              total_bookings_count: 8
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-06-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: group_booking_id eq 'GRP-04556238'
            - tool: zendesk_get_item
              parameters:
                table: tickets
                id: TCK-69222196
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-69222196
                item:
                  status: open
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-04556238
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00098765
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00100001
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00054321
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-00098765
                booking_reference: BKG-00100001
                issue_type: hotel-confirmation-required
                description: 'Group booking GRP-04556238 (15 rooms, check-in 2025-10-12). Coordinator requests: (1) Meeting room for 20 people on 2025-10-13, (2) Lunch catering for the meeting attendees, (3) Airport pickup/transportation for 5 VIP guests arriving separately. Please confirm availability and pricing for all requests.'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-69222196
                item:
                  status: hold
                  priority: normal
                  type: task
                  assignee_id: AG-83945
                  tags:
                    - check-in-upcoming
                    - group-coordinator
                    - hotel-partner-escalation
                  description: 'Group coordinator for GRP-04556238 (15 rooms, premium hotel, check-in 2025-10-12). Requests: (1) Meeting room for 20 people on 2025-10-13, (2) Lunch catering for meeting, (3) Airport pickup for 5 VIP guests. Customer tier: standard. Total group value: $4,800.00. Escalated to hotel partner for confirmation - escalation reference ZDSK-00000013. Awaiting hotel response on availability and pricing for all three requests.'
                  booking_reference: BKG-00100001
                  hotel_id: HTL-00098765
                  check_in_date: '2025-10-12T15:00:00Z'
                  booking_value: 4800.0
                  request_type_detail: add-special-request
                  group_booking_id: GRP-04556238
                  escalation_reason: hotel-confirmation-required
                  refund_amount: 0
    """

    validate_database(x)


def test_hdr_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, this is Patricia Hernandez from Oceanview Resort, hotel ID HTL-93792374. I'm reaching out about a date discrepancy we've noticed for booking BKG-74074821. Our hotel system shows the guest's check-in date as October 8th, but we received information that your StayBridge system has it listed as October 7th. The guest is arriving soon and we need to clarify which date is correct so we can prepare accordingly. Can you please look into this?
    user_context: |
        You are Patricia Hernandez, a hotel partner representative from Oceanview Resort contacting StayBridge support about a booking date discrepancy. You believe there may be a mismatch between your hotel's records and StayBridge's system for booking BKG-74074821.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent confirms that StayBridge records are correct and you need to update your hotel system, acknowledge this and thank them for the clarification.
    init:
      external_booking_v1:
        data_patch:
          zendesk_users:
            - id: USR-10000007
              name: Patricia Hernandez
              email: front.desk@oceanviewresort.com
              role: end-user
              organization_id: null
              phone: +1-954-628-7342
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-74074821
              customer_id: CUS-00000006
              hotel_id: HTL-93792374
              check_in_date: '2025-10-07T15:00:00Z'
              check_out_date: '2025-10-10T11:00:00Z'
              booking_value: '450.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history:
                - '2025-09-26T10:00:00Z: check_in_date: 2025-10-08T15:00:00Z -> 2025-10-07T15:00:00Z'
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-26T10:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-93792374
              hotel_name: Oceanview Resort
              location: Fort Lauderdale
              partner_tier: premium
              contact_name: Patricia Hernandez
              contact_email: front.desk@oceanviewresort.com
              contact_phone: +1-954-628-7342
              escalation_contact: manager@oceanviewresort.com
              amenities:
                - pool
                - beach
                - spa
                - restaurant
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: marcus.webb@gmail.com
              full_name: Marcus Webb
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '450.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-74074821'
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-93792374
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'front.desk@oceanviewresort.com'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-74074821
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Booking date discrepancy inquiry - BKG-74074821
                  description: Hotel partner from Oceanview Resort reported date discrepancy for booking BKG-74074821. Hotel system shows check-in October 8, 2025 while StayBridge system shows October 7, 2025. Investigation confirms modification_history records date change from Oct 8 to Oct 7 made on September 26, 2025. StayBridge records are correct and authoritative.
                  status: open
                  priority: low
                  type: question
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - hotel-partner
                  booking_reference: BKG-74074821
                  hotel_id: HTL-93792374
                  booking_value: 450.0
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  description: Hotel partner from Oceanview Resort reported date discrepancy for booking BKG-74074821. Hotel system shows check-in October 8, 2025 while StayBridge system shows October 7, 2025. Investigation confirms modification_history records date change from Oct 8 to Oct 7 made on September 26, 2025. StayBridge records are correct and authoritative. Advised hotel partner to update their system records to reflect correct check-in date of October 7, 2025.
                  request_type_detail: other
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_hdr_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Patricia Gonzalez from City Center Hotel, hotel ID HTL-75946474. I'm following up on a date discrepancy issue I reported a few days ago for booking BKG-36713695. Your system shows the guest checked out on September 22nd, but according to our records the guest extended their stay directly with us and actually checked out on September 24th. We have documentation showing the guest requested the extension at our front desk. I'd like to get this corrected in your system so the billing matches the actual stay dates. Can you help resolve this?
    user_context: |
        You are Patricia Gonzalez, a hotel partner representative from City Center Hotel contacting StayBridge support about a checkout date discrepancy for booking BKG-36713695. You believe the checkout date should be September 24th instead of September 22nd because the guest arranged a 2-night extension directly with your hotel. You reported this issue a few days ago but haven't received a resolution yet.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent explains that StayBridge data is authoritative and the extended stay billing should be handled directly between your hotel and the guest, acknowledge and accept this explanation.
    init:
      external_booking_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-94406409
              subject: Date discrepancy for booking BKG-36713695
              description: Hotel partner reports checkout date mismatch - StayBridge shows 2025-09-22, hotel records show 2025-09-24
              status: pending
              priority: low
              type: question
              requester_id: USR-74829156
              assignee_id: AG-83945
              organization_id: null
              tags:
                - hotel-partner
              created_at: '2025-09-28T10:00:00Z'
              updated_at: '2025-09-28T10:00:00Z'
              due_at: null
              booking_reference: BKG-36713695
              hotel_id: HTL-75946474
              check_in_date: '2025-09-20T15:00:00Z'
              booking_value: 400.0
              request_type_detail: other
              corporate_account_id: null
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-36713695
              customer_id: CUS-83941627
              hotel_id: HTL-75946474
              check_in_date: '2025-09-20T15:00:00Z'
              check_out_date: '2025-09-22T11:00:00Z'
              booking_value: '400.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-22T11:00:00Z'
          zendesk_users:
            - id: USR-74829156
              name: Patricia Gonzalez
              email: patricia.gonzalez@citycenterhotel.com
              role: end-user
              organization_id: null
              phone: +1-312-847-5629
              verified: true
              active: true
              created_at: '2024-08-15T10:00:00Z'
              updated_at: '2024-08-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-75946474
              hotel_name: City Center Hotel
              location: Chicago
              partner_tier: standard
              contact_name: Patricia Gonzalez
              contact_email: patricia.gonzalez@citycenterhotel.com
              contact_phone: +1-312-847-5629
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - gym
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2024-05-10T10:00:00Z'
              updated_at: '2024-05-10T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-83941627
              customer_id: CUS-83941627
              email: james.morrison@gmail.com
              full_name: James Morrison
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '800.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
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
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-36713695'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-94406409
                item:
                  status: open
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-36713695
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-94406409
                item:
                  status: solved
                  type: question
                  priority: low
                  tags:
                    - hotel-partner
                  booking_reference: BKG-36713695
                  hotel_id: HTL-75946474
                  booking_value: 400.0
                  request_type_detail: other
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_hdr_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, this is Jennifer Martinez calling from Grand Plaza Hotel, hotel ID HTL-09521456. We have a discrepancy issue with booking BKG-23285884. Your StayBridge system shows this booking was for 3 adults, but when the guest checked in, only 1 person arrived. We had to hold a larger room for this reservation unnecessarily, and we'd like to request a charge adjustment to account for this. Can you help us resolve this?
    user_context: |
        You are Jennifer Martinez, a representative from Grand Plaza Hotel (hotel ID: HTL-09521456, premium partner tier), contacting StayBridge support about a guest count discrepancy for booking BKG-23285884. Your hotel's records show only 1 guest arrived, but the StayBridge system shows 3 adults were booked. You want a charge adjustment because you held a larger room unnecessarily.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent explains that the booking modification was legitimate and charge adjustments cannot be processed by StayBridge, acknowledge understanding but express mild disappointment. You may ask for clarification if needed but ultimately accept the resolution.
    init:
      external_booking_v1:
        data_patch:
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-09521456
              hotel_name: Grand Plaza Hotel
              location: Chicago
              partner_tier: premium
              contact_name: Jennifer Martinez
              contact_email: contact@grandplazahotel.com
              contact_phone: +1-312-847-6392
              escalation_contact: gm@grandplazahotel.com
              amenities:
                - pool
                - gym
                - spa
                - restaurant
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Grand Plaza Hotel Chicago
              email: contact@grandplazahotel.com
              role: end-user
              organization_id: null
              phone: +1-312-847-6392
              verified: true
              active: true
              created_at: '2025-03-15T00:00:00Z'
              updated_at: '2025-03-15T00:00:00Z'
          zendesk_tickets:
            - id: TCK-24745171
              subject: Booking verification request - BKG-23285884
              description: Hotel requested verification of booking details for BKG-23285884
              status: solved
              priority: normal
              type: question
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: null
              tags:
                - hotel-partner
                - verification
              created_at: '2025-09-25T14:30:00Z'
              updated_at: '2025-09-26T10:00:00Z'
              due_at: null
              booking_reference: BKG-23285884
              hotel_id: HTL-09521456
              check_in_date: null
              booking_value: 450.0
              request_type_detail: other
              corporate_account_id: null
              group_booking_id: null
              resolution_action: information-provided
              refund_amount: null
              escalation_reason: null
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-23285884
              customer_id: CUS-00000006
              hotel_id: HTL-09521456
              check_in_date: '2025-09-28T15:00:00Z'
              check_out_date: '2025-10-02T11:00:00Z'
              booking_value: '450.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 3
              children_count: 0
              booking_status: checked_in
              corporate_account_id: null
              group_booking_id: null
              modification_history:
                - '2025-09-17T14:30:00Z: adults_count: 1 -> 3'
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-17T14:30:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: michael.harrison@gmail.com
              full_name: Michael Harrison
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '450.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          payment_api_transactions:
            - id: TXN-00000008
              transaction_id: TXN-00000008
              booking_reference: BKG-23285884
              customer_id: CUS-00000006
              amount: '450.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 3847
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          booking_api_hotel_inventory: []
          booking_api_group_bookings: []
          corporate_api_corporate_accounts: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-09521456
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'contact@grandplazahotel.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-23285884'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-23285884
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Guest count discrepancy inquiry - BKG-23285884
                  description: Hotel partner Grand Plaza Hotel reports guest count mismatch for booking BKG-23285884. StayBridge system shows 3 adults; hotel reports only 1 guest arrived. Hotel is requesting charge adjustment for holding larger room. Modification history confirms adults_count was changed from 1 to 3 on 2025-09-17.
                  status: open
                  priority: low
                  type: question
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - hotel-partner
                  booking_reference: BKG-23285884
                  hotel_id: HTL-09521456
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  tags:
                    - hotel-partner
                  booking_reference: BKG-23285884
                  hotel_id: HTL-09521456
                  booking_value: 450.0
                  request_type_detail: other
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_hdr_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Marcus Bennett from Budget Stay Express, hotel ID HTL-51370985. I'm reaching out about a room type discrepancy for booking BKG-93174612. Our hotel system shows this booking as a suite, but StayBridge shows it as a deluxe_room. The guest was charged for a deluxe_room. I actually contacted you folks about this same issue a couple days ago but still haven't received clarification. The guest is checking in tomorrow so we really need to know which room type is correct. Can you help?
    user_context: |
        You are Marcus Bennett, a hotel partner representative from Budget Stay Express contacting StayBridge support about a room type discrepancy for booking BKG-93174612. Your hotel's internal system shows the booking as a suite, but StayBridge shows deluxe_room. You need clarification on which is correct so you can prepare the right room for the guest's check-in tomorrow.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        Accept the resolution once the agent explains the findings and advises what action your hotel should take.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-71839245
              booking_reference: BKG-93174612
              customer_id: CUS-38472916
              hotel_id: HTL-51370985
              check_in_date: '2025-10-02T15:00:00Z'
              check_out_date: '2025-10-04T11:00:00Z'
              booking_value: '250.00'
              room_type: deluxe_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history:
                - '2025-09-27T14:30:00Z: room_type: suite -> deluxe_room'
              special_requests: []
              created_at: '2025-09-20T09:00:00Z'
              updated_at: '2025-09-27T14:30:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-38472916
              customer_id: CUS-38472916
              email: kevin.marshall@outlook.com
              full_name: Kevin Marshall
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '750.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-20T09:00:00Z'
              created_at: '2025-05-10T14:00:00Z'
              updated_at: '2025-09-20T09:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-83927461
              hotel_id: HTL-51370985
              hotel_name: Budget Stay Express
              location: Portland
              partner_tier: budget
              contact_name: Marcus Bennett
              contact_email: manager@budgetstayexpress.com
              contact_phone: +1-503-842-7163
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: false
              created_at: '2025-03-15T10:00:00Z'
              updated_at: '2025-03-15T10:00:00Z'
          payment_api_transactions:
            - id: TXN-47829163
              transaction_id: TXN-47829163
              booking_reference: BKG-93174612
              customer_id: CUS-38472916
              amount: '250.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7821
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-20T09:15:00Z'
              updated_at: '2025-09-20T09:15:00Z'
          zendesk_tickets:
            - id: TCK-00471138
              subject: Room type discrepancy for booking BKG-93174612
              description: Hotel partner reporting room type mismatch - StayBridge shows deluxe_room but hotel system shows suite. Requesting clarification before guest check-in.
              status: open
              priority: normal
              type: question
              requester_id: USR-47291836
              assignee_id: null
              organization_id: null
              tags:
                - hotel-partner
                - room-discrepancy
              created_at: '2025-09-29T11:30:00Z'
              updated_at: '2025-09-29T11:30:00Z'
              due_at: null
              booking_reference: BKG-93174612
              hotel_id: HTL-51370985
              check_in_date: '2025-10-02T15:00:00Z'
              booking_value: 250.0
              request_type_detail: other
              corporate_account_id: null
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-47291836
              name: Marcus Bennett
              email: manager@budgetstayexpress.com
              role: end-user
              organization_id: null
              phone: +1-503-842-7163
              verified: true
              active: true
              created_at: '2025-03-15T10:00:00Z'
              updated_at: '2025-03-15T10:00:00Z'
            - id: USR-62938471
              name: Jennifer Walsh
              email: jennifer.walsh@staybridge.com
              role: agent
              organization_id: null
              phone: +1-503-718-4593
              verified: true
              active: true
              created_at: '2024-06-01T09:00:00Z'
              updated_at: '2024-06-01T09:00:00Z'
            - id: AG-83945
              name: StayBridge Support Agent
              email: support.agent@staybridge.com
              role: agent
              organization_id: null
              phone: null
              verified: true
              active: true
              created_at: '2024-01-15T09:00:00Z'
              updated_at: '2024-01-15T09:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-93174612
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-51370985
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-93174612'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-00471138
                item:
                  status: solved
                  priority: low
                  type: question
                  tags:
                    - hotel-partner
                    - repeat-issue
                  assignee_id: AG-83945
                  booking_reference: BKG-93174612
                  hotel_id: HTL-51370985
                  check_in_date: '2025-10-02T15:00:00Z'
                  booking_value: 250.0
                  request_type_detail: other
                  resolution_action: information-provided
                  refund_amount: 0
                  description: 'Hotel partner from Budget Stay Express reported room type discrepancy - their system shows suite while StayBridge shows deluxe_room. Booking data retrieved confirms current room_type is deluxe_room. Modification_history confirms legitimate change from suite to deluxe_room on 2025-09-27. StayBridge data is authoritative. Guest was correctly charged for deluxe_room. No system error. Hotel advised to update their records to reflect deluxe_room assignment. No escalation required per verifiable discrepancy exception. Resolution: Information provided to hotel partner.'
    """

    validate_database(x)


def test_hdr_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Sarah Mitchell from Riverside Inn, hotel ID HTL-26758692. We're seeing some concerning data discrepancies for booking BKG-61796405 between our hotel system and StayBridge. Our records show check-in date as October 5th, 4 guests, and a standard room - but we suspect these might not match your system. This looks like it could be a system synchronization error affecting multiple fields. Can you help investigate and confirm what the correct booking details should be?
    user_context: |
        You are Sarah Mitchell, a hotel partner representative from Riverside Inn contacting StayBridge support about data discrepancies for booking BKG-61796405.

        CONTEXT:
        - Your hotel system shows: check-in October 5th, 4 guests, standard room
        - You believe there may be a system synchronization error
        - You want StayBridge to investigate and clarify the correct booking details

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent provides verified StayBridge booking data and explains it is authoritative, acknowledge and accept the information.
    init:
      external_booking_v1:
        data_patch:
          zendesk_users:
            - id: USR-10000007
              name: Sarah Mitchell
              email: operations@riversideinn.com
              role: end-user
              organization_id: ORG-10000006
              phone: +1-503-482-7139
              verified: true
              active: true
              created_at: '2025-01-01T00:00:00Z'
              updated_at: '2025-01-01T00:00:00Z'
          zendesk_organizations:
            - id: ORG-10000006
              name: Riverside Inn
              domain_names:
                - riversideinn.com
              details: Hotel partner - budget tier
              notes: Portland, OR location
              created_at: '2025-01-01T00:00:00Z'
              updated_at: '2025-01-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-61796405
              customer_id: CUS-55198302
              hotel_id: HTL-26758692
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-08T11:00:00Z'
              booking_value: '450.00'
              room_type: suite
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:30:00Z'
              updated_at: '2025-09-15T10:30:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-26758692
              hotel_name: Riverside Inn
              location: Portland, OR
              partner_tier: budget
              contact_name: Sarah Mitchell
              contact_email: operations@riversideinn.com
              contact_phone: +1-503-482-7139
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-55198302
              email: marcus.webb@gmail.com
              full_name: Marcus Webb
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '450.00'
              total_bookings_count: 1
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:30:00Z'
              created_at: '2025-09-15T10:30:00Z'
              updated_at: '2025-09-15T10:30:00Z'
          corporate_api_corporate_accounts: []
          payment_api_transactions:
            - id: TXN-00000008
              transaction_id: TXN-00000008
              booking_reference: BKG-61796405
              customer_id: CUS-55198302
              amount: '450.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7823
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-15T10:30:00Z'
              updated_at: '2025-09-15T10:30:00Z'
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-61796405'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-61796405
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-26758692
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'operations@riversideinn.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Booking Data Discrepancy Inquiry - BKG-61796405
                  description: 'Hotel partner Riverside Inn (HTL-26758692, budget tier) reported data discrepancies for booking BKG-61796405. Hotel reports: check-in 2025-10-05, 4 guests, standard_room. StayBridge system shows: check-in 2025-10-06, 2 adults, 0 children, suite. Modification history is empty - no recorded changes since booking creation. Per policy Section 4.8.2, without confirmed system error evidence, StayBridge booking data is authoritative. Provided correct booking information to hotel partner for their records update.'
                  status: open
                  priority: low
                  type: question
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - hotel-partner
                  booking_reference: BKG-61796405
                  hotel_id: HTL-26758692
                  booking_value: 450.0
                  request_type_detail: other
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_hpv_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is the front desk from Oceanview Resort, hotel ID HTL-37735158. I need to verify the guest details for a booking we have coming up. The booking reference is BKG-50643171. Can you confirm the guest name, check-in and check-out dates, room type, and guest count for us?
    user_context: |
        You are a hotel partner representative working at the front desk of Oceanview Resort. You are contacting StayBridge support to verify guest details for an upcoming booking (BKG-50643171) at your hotel.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Once the agent provides the booking verification details (guest name, dates, room type, guest count), thank them and end the conversation.
    init:
      external_booking_v1:
        data_patch:
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-37735158
              hotel_name: Oceanview Resort
              location: Coastal Bay
              partner_tier: premium
              contact_name: Rebecca Martinez
              contact_email: frontdesk@oceanviewresort.com
              contact_phone: +1-858-742-3618
              escalation_contact: manager@oceanviewresort.com
              amenities:
                - pool
                - beach
                - spa
                - restaurant
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2024-08-15T10:00:00Z'
              updated_at: '2024-08-15T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Oceanview Resort Front Desk
              email: frontdesk@oceanviewresort.com
              role: end-user
              organization_id: null
              phone: +1-858-742-3618
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-50643171
              customer_id: CUS-00045678
              hotel_id: HTL-37735158
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-08T11:00:00Z'
              booking_value: '675.00'
              room_type: suite
              board_type: with_breakfast
              adults_count: 2
              children_count: 1
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_hotel_inventory: []
          booking_api_group_bookings: []
          crm_api_customer_profiles:
            - id: CUS-00045678
              customer_id: CUS-00045678
              email: sarah.johnson@outlook.com
              full_name: Sarah Johnson
              vip_tier: standard
              loyalty_program_status: active
              lifetime_value: '1250.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-06-20T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-37735158
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'frontdesk@oceanviewresort.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-50643171'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-50643171
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00045678
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Booking verification request - BKG-50643171
                  description: Hotel partner from Oceanview Resort requesting verification of guest details for booking BKG-50643171.
                  status: open
                  priority: low
                  type: question
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - hotel-partner
                  booking_reference: BKG-50643171
                  hotel_id: HTL-37735158
                  request_type_detail: other
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  resolution_action: information-provided
                  refund_amount: 0
                  booking_value: 675.0
                  tags:
                    - hotel-partner
    """

    validate_database(x)


def test_hpv_002(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Rebecca from Mountain Lodge Inn front desk. I need to verify the check-in date for booking BKG-31839335. Our hotel records show the guest is arriving on October 10th, 2025, but the guest called us and mentioned they thought their check-in was October 9th. Can you please confirm what date is in your system? Our hotel ID is HTL-39005329.
    user_context: |
        You are Rebecca Winters, a front desk representative from Mountain Lodge Inn (a StayBridge hotel partner). You are contacting StayBridge support to verify booking dates because there's a discrepancy between your hotel records (showing check-in 2025-10-10) and what the guest claims (2025-10-09). You want to know the correct date so you can prepare accordingly.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Accept and acknowledge whatever confirmation the agent provides about the booking dates.
    init:
      external_booking_v1:
        data_patch:
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-39005329
              hotel_name: Mountain Lodge Inn
              location: Bozeman, Montana
              partner_tier: standard
              contact_name: Rebecca Winters
              contact_email: frontdesk@mountainlodgeinn.com
              contact_phone: +1-406-582-7341
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - fireplace
                - ski_storage
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2024-03-15T10:00:00Z'
              updated_at: '2024-03-15T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Mountain Lodge Inn Front Desk
              email: frontdesk@mountainlodgeinn.com
              role: end-user
              organization_id: null
              phone: +1-406-582-7341
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-31839335
              customer_id: CUS-84729103
              hotel_id: HTL-39005329
              check_in_date: '2025-10-10T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '320.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-84729103
              email: marcus.wellington@protonmail.com
              full_name: Marcus Wellington
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '640.00'
              total_bookings_count: 2
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-01T10:00:00Z'
              created_at: '2025-06-15T10:00:00Z'
              updated_at: '2025-06-15T10:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_articles: []
          booking_api_hotel_inventory: []
          booking_api_group_bookings: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: hotel_partner_api_get_hotel_contact
              parameters:
                hotel_id: HTL-39005329
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'frontdesk@mountainlodgeinn.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-31839335'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-31839335
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-84729103
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Booking Verification - BKG-31839335
                  description: Hotel partner from Mountain Lodge Inn (HTL-39005329) requesting verification of check-in date for booking BKG-31839335. Hotel records show 2025-10-10, guest mentioned 2025-10-09. Need to confirm correct check-in date.
                  status: open
                  priority: low
                  type: question
                  requester_id: USR-10000007
                  assignee_id: AG-83945
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  tags:
                    - hotel-partner
                  booking_reference: BKG-31839335
                  hotel_id: HTL-39005329
                  booking_value: 320.0
                  request_type_detail: other
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_hpv_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I'm calling from Budget Stay Express hotel. We have a situation with booking BKG-50240268 - the guest is claiming they booked a suite, but in our system it shows they're assigned to a standard room. Could you check your records and verify what room type was actually booked? We need to clarify this discrepancy with the guest.
    user_context: |
        You are a hotel partner representative from Budget Stay Express contacting StayBridge support about a room type discrepancy. The guest claims they booked a suite but your hotel records show a standard room.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-50240268
              customer_id: CUS-50240268
              hotel_id: HTL-21020539
              check_in_date: '2025-10-06T15:00:00Z'
              check_out_date: '2025-10-08T11:00:00Z'
              booking_value: '320.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-21020539
              hotel_name: Budget Stay Express
              location: Denver, CO
              partner_tier: budget
              contact_name: Jessica Martinez
              contact_email: operations@budgetstayexpress.com
              contact_phone: +1-720-438-0139
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Budget Stay Express Operations
              email: operations@budgetstayexpress.com
              role: end-user
              organization_id: null
              phone: +1-720-438-0139
              verified: true
              active: true
              created_at: '2025-02-01T00:00:00Z'
              updated_at: '2025-02-01T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-50240268'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-50240268
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-21020539
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'operations@budgetstayexpress.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Room type discrepancy verification - BKG-50240268
                  description: Hotel partner from Budget Stay Express reports guest claims suite was booked but hotel shows standard_room for booking BKG-50240268. Verifying StayBridge booking data.
                  status: open
                  priority: low
                  type: question
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - hotel-partner
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  tags:
                    - hotel-partner
                  booking_reference: BKG-50240268
                  hotel_id: HTL-21020539
                  booking_value: 320.0
                  request_type_detail: other
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_hpv_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, this is Rebecca Martinez calling from City Center Hotel, hotel ID HTL-11592124. I need to verify a booking reference with you. We have a guest at our front desk who is showing us a confirmation email with booking reference BKG-99856984, but we can't find this reservation in our records. Can you check if this is a valid StayBridge booking?
    user_context: |
        You are Rebecca Martinez, a front desk representative from City Center Hotel (hotel_id: HTL-11592124), a standard tier partner hotel. You are contacting StayBridge support to verify a booking reference that a guest presented to you. The guest showed a confirmation email with booking reference BKG-99856984, but you cannot locate this booking in your hotel's reservation system.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent informs you the booking doesn't exist, acknowledge the information and thank them for checking.
    init:
      external_booking_v1:
        data_patch:
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-11592124
              hotel_name: City Center Hotel
              location: Chicago
              partner_tier: standard
              contact_name: Rebecca Martinez
              contact_email: frontdesk@citycenterhotel.com
              contact_phone: +1-312-847-6521
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - business_center
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Rebecca Martinez
              email: frontdesk@citycenterhotel.com
              role: end-user
              organization_id: null
              phone: +1-312-847-6521
              verified: true
              active: true
              created_at: '2025-02-20T09:00:00Z'
              updated_at: '2025-02-20T09:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-11592124
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-99856984'
            - tool: payment_api_get_transaction_history
              parameters:
                booking_reference: BKG-99856984
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'frontdesk@citycenterhotel.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Booking verification request - BKG-99856984
                  description: 'Hotel partner City Center Hotel (HTL-11592124) requested verification of booking reference BKG-99856984. Guest presented a confirmation email with this reference to the hotel. Agent investigation: Booking does not exist in StayBridge system. No payment transactions found for this reference.'
                  status: open
                  priority: low
                  type: question
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - hotel-partner
                  booking_reference: BKG-99856984
                  hotel_id: HTL-11592124
                  request_type_detail: other
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_hpv_006(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, this is Maria from the front desk at Riverside Inn, hotel ID HTL-96965328. I need to verify a booking - reference number BKG-71012269. We have a guest who just arrived at our property expecting to check in today, but we can't find this reservation in our system. Can you please confirm the booking details for me?
    user_context: |
        You are Maria Delgado, a front desk representative at Riverside Inn (hotel ID: HTL-96965328), a hotel partner of StayBridge. You are contacting support to verify booking BKG-71012269 because a guest named Thomas Reynolds has arrived expecting to check in today, but you cannot locate the reservation in your hotel's system.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Acknowledge information provided by the agent about the booking status.
        - If asked for your email, it is frontdesk@riversideinn.com.
    init:
      external_booking_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-16697848
              subject: Rate inquiry for booking BKG-71012269
              description: Hotel partner inquiring about room rates for upcoming guest reservation
              status: solved
              priority: normal
              type: question
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: null
              tags:
                - rate-inquiry
                - hotel-partner
              created_at: '2025-09-27T10:00:00Z'
              updated_at: '2025-09-27T14:30:00Z'
              due_at: null
              booking_reference: BKG-71012269
              hotel_id: HTL-96965328
              check_in_date: '2025-10-01T15:00:00Z'
              booking_value: 275.0
              request_type_detail: billing-inquiry
              corporate_account_id: null
              group_booking_id: null
              resolution_action: information-provided
              refund_amount: 0
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Maria Delgado
              email: frontdesk@riversideinn.com
              role: end-user
              organization_id: null
              phone: +1-951-478-3629
              verified: true
              active: true
              created_at: '2024-09-15T00:00:00Z'
              updated_at: '2024-09-15T00:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-96965328
              hotel_name: Riverside Inn
              location: Riverside, CA
              partner_tier: budget
              contact_name: Maria Delgado
              contact_email: frontdesk@riversideinn.com
              contact_phone: +1-951-478-3629
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-71012269
              booking_status: cancelled
              hotel_id: HTL-96965328
              customer_id: CUS-44291038
              check_in_date: '2025-10-01T15:00:00Z'
              check_out_date: '2025-10-03T11:00:00Z'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              special_requests:
                - ground floor room
              booking_value: '275.00'
              corporate_account_id: null
              group_booking_id: null
              modification_history:
                - '2025-09-28T14:00:00Z: booking_status: confirmed -> cancelled'
              created_at: '2025-09-15T09:30:00Z'
              updated_at: '2025-09-28T14:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-44291038
              email: thomas.reynolds@gmail.com
              full_name: Thomas Reynolds
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '275.00'
              total_bookings_count: 1
              preferences:
                - ground floor room
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T09:30:00Z'
              created_at: '2025-09-15T09:00:00Z'
              updated_at: '2025-09-28T14:00:00Z'
          payment_api_transactions:
            - id: TXN-00000008
              transaction_id: TXN-00000008
              booking_reference: BKG-71012269
              customer_id: CUS-44291038
              amount: '275.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 3847
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-15T09:30:00Z'
              updated_at: '2025-09-15T09:30:00Z'
            - id: TXN-00000009
              transaction_id: TXN-00000009
              booking_reference: BKG-71012269
              customer_id: CUS-44291038
              amount: '275.00'
              currency: USD
              transaction_type: refund
              payment_status: successful
              payment_method: null
              reason: Booking cancellation
              processing_time_estimate: 3-5 business days
              created_at: '2025-09-28T14:00:00Z'
              updated_at: '2025-09-28T14:00:00Z'
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-71012269'
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-96965328
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'frontdesk@riversideinn.com'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-71012269
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Booking verification request - BKG-71012269
                  description: 'Hotel partner from Riverside Inn requesting verification of booking BKG-71012269. Guest arrived at hotel today expecting to check in. Booking retrieved from system - status is CANCELLED (cancellation recorded 2025-09-28). Original booking details: check-in 2025-10-01, check-out 2025-10-03, standard room with breakfast, 2 adults, 0 children.'
                  status: open
                  priority: urgent
                  type: question
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - hotel-partner
                  booking_reference: BKG-71012269
                  hotel_id: HTL-96965328
                  booking_value: 275.0
                  request_type_detail: other
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_hpv_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, this is Maria Gonzalez from Beach Resort & Spa, hotel ID HTL-15654527. I'm following up on our group booking GRP-11116152 - we have 6 rooms arriving soon and I need to verify the guest names for each individual booking reference. Can you provide me with the complete guest list for this group? My email is maria.gonzalez@beachresortspa.com.
    user_context: |
        You are Maria Gonzalez, a hotel partner representative from Beach Resort & Spa (a premium tier hotel partner). You are contacting support to verify guest names for all 6 rooms in group booking GRP-11116152. You previously contacted about this same issue yesterday and have an open ticket.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent provides you with the guest list information, thank them and confirm you have what you need.
    init:
      external_booking_v1:
        data_patch:
          booking_api_group_bookings:
            - id: GRP-00000006
              group_booking_id: GRP-11116152
              coordinator_name: Jennifer Martinez
              coordinator_email: jennifer.martinez@eventplanning.org
              coordinator_phone: +1-407-892-3456
              total_rooms: 6
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-08T11:00:00Z'
              hotel_id: HTL-15654527
              booking_references:
                - BKG-00001001
                - BKG-00001002
                - BKG-00001003
                - BKG-00001004
                - BKG-00001005
                - BKG-00001006
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-00001001
              customer_id: CUS-00012001
              hotel_id: HTL-15654527
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-08T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-11116152
              modification_history: []
              special_requests:
                - ground floor preferred
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000007
              booking_reference: BKG-00001002
              customer_id: CUS-00012002
              hotel_id: HTL-15654527
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-08T11:00:00Z'
              booking_value: '450.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 1
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-11116152
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000008
              booking_reference: BKG-00001003
              customer_id: CUS-00012003
              hotel_id: HTL-15654527
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-08T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 1
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-11116152
              modification_history: []
              special_requests:
                - late check-in
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000009
              booking_reference: BKG-00001004
              customer_id: CUS-00012004
              hotel_id: HTL-15654527
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-08T11:00:00Z'
              booking_value: '600.00'
              room_type: suite
              board_type: with_breakfast
              adults_count: 2
              children_count: 2
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-11116152
              modification_history: []
              special_requests:
                - crib needed
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000010
              booking_reference: BKG-00001005
              customer_id: CUS-00012005
              hotel_id: HTL-15654527
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-08T11:00:00Z'
              booking_value: '300.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-11116152
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: BKG-00000011
              booking_reference: BKG-00001006
              customer_id: CUS-00012006
              hotel_id: HTL-15654527
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-08T11:00:00Z'
              booking_value: '450.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 1
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: GRP-11116152
              modification_history: []
              special_requests:
                - high floor
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00012001
              customer_id: CUS-00012001
              email: r.williams@outlook.com
              full_name: Robert Williams
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '850.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: CUS-00012002
              customer_id: CUS-00012002
              email: sarah.mitchell@protonmail.com
              full_name: Sarah Mitchell
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '1250.00'
              total_bookings_count: 4
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-02-20T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: CUS-00012003
              customer_id: CUS-00012003
              email: jpatterson87@gmail.com
              full_name: James Patterson
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '620.00'
              total_bookings_count: 2
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-03-10T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: CUS-00012004
              customer_id: CUS-00012004
              email: amanda.foster@icloud.com
              full_name: Amanda Foster
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '1780.00'
              total_bookings_count: 5
              preferences:
                - family-friendly rooms
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-06-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: CUS-00012005
              customer_id: CUS-00012005
              email: m.thompson@yahoo.com
              full_name: Michael Thompson
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '450.00'
              total_bookings_count: 2
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2025-04-22T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
            - id: CUS-00012006
              customer_id: CUS-00012006
              email: e.chen.travel@gmail.com
              full_name: Elizabeth Chen
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '920.00'
              total_bookings_count: 3
              preferences:
                - high floor
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-11-08T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          zendesk_tickets:
            - id: '80988516'
              subject: Group Booking Verification Request - GRP-11116152
              description: Hotel partner requesting verification of guest names for group booking with 6 rooms
              status: open
              priority: low
              type: question
              requester_id: USR-20000001
              assignee_id: null
              organization_id: null
              tags:
                - hotel-partner
              created_at: '2025-09-30T13:00:00Z'
              updated_at: '2025-09-30T13:00:00Z'
              due_at: null
              booking_reference: BKG-00001001
              hotel_id: HTL-15654527
              check_in_date: '2025-10-05T15:00:00Z'
              booking_value: null
              request_type_detail: null
              corporate_account_id: null
              group_booking_id: GRP-11116152
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-20000001
              name: Maria Gonzalez
              email: maria.gonzalez@beachresortspa.com
              role: end-user
              organization_id: null
              phone: +1-305-847-2931
              verified: true
              active: true
              created_at: '2024-08-15T10:00:00Z'
              updated_at: '2024-08-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-15654527
              hotel_name: Beach Resort & Spa
              location: Miami
              partner_tier: premium
              contact_name: Maria Gonzalez
              contact_email: maria.gonzalez@beachresortspa.com
              contact_phone: +1-305-847-2931
              escalation_contact: director@beachresortspa.com
              amenities:
                - pool
                - spa
                - beach
                - restaurant
                - gym
                - wifi
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2024-03-01T10:00:00Z'
              updated_at: '2024-03-01T10:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_group_booking
              parameters:
                group_booking_id: GRP-11116152
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-00001001'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00001001
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00012001
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00001002
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00012002
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00001003
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00012003
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00001004
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00012004
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00001005
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00012005
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-00001006
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00012006
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '80988516'
                item:
                  status: solved
                  type: question
                  priority: low
                  assignee_id: AG-83945
                  tags:
                    - hotel-partner
                  booking_reference: BKG-00001001
                  hotel_id: HTL-15654527
                  group_booking_id: GRP-11116152
                  booking_value: 2400.0
                  request_type_detail: other
                  resolution_action: information-provided
                  refund_amount: 0
    """

    validate_database(x)


def test_psc_001(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I just checked out from my stay yesterday and I need to file a complaint. I'm Michelle Turner, email michelle.turner@outlook.com, booking reference BKG-01845146. The service was absolutely terrible. The front desk staff was incredibly rude when I asked questions, room service took 2 hours to deliver our food, and housekeeping never came despite multiple requests throughout our stay. This was unacceptable and I'd like something done about it.
    user_context: |
        You are Michelle Turner, a customer who just completed a 2-night stay and is extremely dissatisfied with the service you received. You are filing a complaint about three specific issues: rude front desk staff, a 2-hour delay for room service, and housekeeping that never showed up despite multiple requests.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - Accept any compensation offer the agent provides and thank them for resolving the issue.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-01845146
              customer_id: CUS-00000006
              hotel_id: HTL-00012346
              check_in_date: '2025-09-28T15:00:00Z'
              check_out_date: '2025-09-30T11:00:00Z'
              booking_value: '420.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              special_requests: []
              modification_history: []
              created_at: '2025-09-14T10:00:00Z'
              updated_at: '2025-09-14T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: michelle.turner@outlook.com
              full_name: Michelle Turner
              vip_tier: standard
              loyalty_program_status: null
              lifetime_value: '1250.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-30T11:00:00Z'
              created_at: '2025-06-01T10:00:00Z'
              updated_at: '2025-09-30T12:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Michelle Turner
              email: michelle.turner@outlook.com
              role: end-user
              organization_id: null
              phone: +1-617-482-3947
              verified: true
              active: true
              created_at: '2025-06-01T10:00:00Z'
              updated_at: '2025-06-01T10:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          hotel_partner_api_hotels: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-01845146'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-01845146
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'michelle.turner@outlook.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Post-stay service complaint - BKG-01845146
                  description: 'Customer reports poor service during stay: rude front desk staff, room service took 2 hours to deliver food, and housekeeping never came despite multiple requests. Check-out: 2025-09-30. Reported within 48 hours.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-01845146
                refund_amount: '210.00'
                reason: post_stay_compensation
            - tool: crm_api_update_customer_info
              parameters:
                customer_id: CUS-00000006
                complaint_count: 1
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  tags:
                    - b2c-customer
                  booking_reference: BKG-01845146
                  hotel_id: HTL-00012346
                  booking_value: 420.0
                  request_type_detail: post-stay-issue
                  resolution_action: refund-partial
                  refund_amount: 210.0
    """

    validate_database(x)


def test_psc_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I just checked out of my stay at Riverside Suites yesterday and I need to file a complaint. My booking reference is BKG-85149368 and my name is Marcus Wellington (email: marcus.wellington@protonmail.com). There was incredibly loud construction happening right next to our room that started at 7 AM every single day of our 4-night stay. Nobody warned us about this when we booked or when we checked in, and the hotel never offered to move us to a different room. It completely ruined our trip and we couldn't sleep in at all. I'm very disappointed with this experience.
    user_context: |
        You are Marcus Wellington, a platinum-tier loyalty customer who just completed a 4-night stay at Riverside Suites. You are contacting support to complain about construction noise that disrupted your entire stay.

        Your complaint details:
        - Construction started at 7 AM every morning
        - It affected all 4 nights of your stay
        - You were never informed about it beforehand
        - The hotel never offered to relocate you to another room
        - You are seeking compensation for the poor experience

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm the compensation or refund offer, accept it.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-85149368
              customer_id: CUS-00000006
              hotel_id: HTL-00012350
              check_in_date: '2025-09-26T15:00:00Z'
              check_out_date: '2025-09-30T12:00:00Z'
              booking_value: '890.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-30T12:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: marcus.wellington@protonmail.com
              full_name: Marcus Wellington
              vip_tier: platinum
              loyalty_program_status: platinum-elite
              lifetime_value: '25890.50'
              total_bookings_count: 42
              preferences:
                - quiet room
                - high floor
              special_notes:
                - values responsive service
              complaint_count: 0
              last_booking_date: '2025-09-30T12:00:00Z'
              created_at: '2023-02-15T00:00:00Z'
              updated_at: '2025-09-30T12:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00012350
              hotel_name: Riverside Suites
              location: Chicago
              partner_tier: standard
              contact_name: Jennifer Walsh
              contact_email: info@riversidesuites.com
              contact_phone: +1-312-847-6293
              escalation_contact: null
              amenities:
                - wifi
                - restaurant
                - parking
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Wellington
              email: marcus.wellington@protonmail.com
              role: end-user
              organization_id: null
              phone: +1-847-293-6184
              verified: true
              active: true
              created_at: '2023-02-15T00:00:00Z'
              updated_at: '2023-02-15T00:00:00Z'
          payment_api_transactions:
            - id: TXN-00000100
              transaction_id: TXN-00000100
              booking_reference: BKG-85149368
              customer_id: CUS-00000006
              amount: '890.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7821
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          lookup_bookings: []
          lookup_hotels: []
          lookup_group_bookings: []
          lookup_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-85149368
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00012350
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-85149368'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.wellington@protonmail.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Post-stay service complaint - BKG-85149368
                  description: Customer reports noisy construction starting at 7 AM daily throughout their 4-night stay. No notification or room change offered. Requesting compensation.
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - vip-customer
                  booking_reference: BKG-85149368
                  hotel_id: HTL-00012350
                  booking_value: 890.0
                  request_type_detail: post-stay-issue
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-85149368
                refund_amount: '890.00'
                reason: post_stay_compensation
            - tool: crm_api_update_customer_info
              parameters:
                customer_id: CUS-00000006
                complaint_count: 1
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  resolution_action: refund-full
                  refund_amount: 890.0
    """

    validate_database(x)


def test_psc_004(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm reaching out about a really frustrating experience during my recent stay. My name is Marcus Webb, email marcus.webb@fastmail.net, and my booking reference is BKG-99809402. The WiFi didn't work for my entire stay - I reported it to the front desk multiple times but nothing was ever fixed. I had to use my mobile data for work calls the whole time, which was incredibly inconvenient. I'd like to know what can be done about this.
    user_context: |
        You are Marcus Webb, a customer contacting StayBridge support about a post-stay complaint regarding WiFi issues during your recent hotel stay (booking BKG-99809402). The WiFi did not work for your entire 2-night stay despite reporting the problem to the front desk multiple times. You had to use your mobile data for work calls as a result.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          crm_api_customer_profiles:
            - id: CUS-44782901
              customer_id: CUS-44782901
              email: marcus.webb@fastmail.net
              full_name: Marcus Webb
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '1875.40'
              total_bookings_count: 8
              preferences:
                - ground floor
                - extra pillows
              special_notes:
                - prefers email communication
              complaint_count: 2
              last_booking_date: '2025-09-25T11:00:00Z'
              created_at: '2024-03-15T09:00:00Z'
              updated_at: '2025-09-25T12:00:00Z'
          booking_api_bookings:
            - id: BKG-99809402
              booking_reference: BKG-99809402
              customer_id: CUS-44782901
              hotel_id: HTL-88341276
              check_in_date: '2025-09-23T15:00:00Z'
              check_out_date: '2025-09-25T11:00:00Z'
              booking_value: '310.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-10T14:30:00Z'
              updated_at: '2025-09-25T11:00:00Z'
            - id: BKG-99712458
              booking_reference: BKG-99712458
              customer_id: CUS-44782901
              hotel_id: HTL-88341276
              check_in_date: '2025-09-15T15:00:00Z'
              check_out_date: '2025-09-17T11:00:00Z'
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
              created_at: '2025-09-05T10:00:00Z'
              updated_at: '2025-09-17T11:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-88341276
              hotel_id: HTL-88341276
              hotel_name: Cityview Budget Inn
              location: Philadelphia
              partner_tier: budget
              contact_name: Teresa Ramirez
              contact_email: frontdesk@cityviewbudget.com
              contact_phone: +1-215-483-7291
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: false
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2024-06-01T10:00:00Z'
          zendesk_users:
            - id: USR-44782901
              name: Marcus Webb
              email: marcus.webb@fastmail.net
              role: end-user
              organization_id: ORG-10000002
              phone: +1-267-934-1852
              verified: true
              active: true
              created_at: '2024-03-15T09:00:00Z'
              updated_at: '2024-03-15T09:00:00Z'
          zendesk_tickets:
            - id: TCK-44550229
              subject: Post-stay complaint - room maintenance issues
              description: Customer reported issues with air conditioning during previous stay at Cityview Budget Inn. AC unit was noisy and failed to cool room properly. Issue was reported to front desk but not resolved during stay.
              status: solved
              priority: normal
              type: problem
              requester_id: USR-44782901
              assignee_id: AG-83945
              organization_id: null
              tags:
                - post-stay
                - complaint
                - b2c-customer
              created_at: '2025-09-27T14:00:00Z'
              updated_at: '2025-09-27T16:30:00Z'
              due_at: null
              booking_reference: BKG-99712458
              hotel_id: HTL-88341276
              check_in_date: null
              booking_value: 275.0
              request_type_detail: post-stay-issue
              corporate_account_id: null
              group_booking_id: null
              resolution_action: refund-partial
              refund_amount: 68.75
              escalation_reason: null
          payment_api_transactions:
            - id: TXN-99809402
              transaction_id: TXN-99809402
              booking_reference: BKG-99809402
              customer_id: CUS-44782901
              amount: '310.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7821
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-10T14:35:00Z'
              updated_at: '2025-09-10T14:35:00Z'
            - id: TXN-99712458
              transaction_id: TXN-99712458
              booking_reference: BKG-99712458
              customer_id: CUS-44782901
              amount: '275.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7821
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-05T10:05:00Z'
              updated_at: '2025-09-05T10:05:00Z'
            - id: TXN-99712459
              transaction_id: TXN-99712459
              booking_reference: BKG-99712458
              customer_id: CUS-44782901
              amount: '68.75'
              currency: USD
              transaction_type: refund
              payment_status: successful
              payment_method: null
              reason: post_stay_compensation
              processing_time_estimate: 3-5 business days
              created_at: '2025-09-27T16:30:00Z'
              updated_at: '2025-09-27T16:30:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: crm_api_get_customer_profile
              parameters:
                email: marcus.webb@fastmail.net
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-99809402
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-88341276
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-99809402'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.webb@fastmail.net'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Post-stay service complaint - BKG-99809402
                  description: 'Customer reports WiFi did not work for entire stay (2 nights, Sep 23-25, 2025) at budget partner hotel. Issue was reported to front desk multiple times during stay. Customer had to use mobile data for work calls. Complaint category: service (amenities unavailable). Timing: 6 days post-checkout (within 7-day window). Customer: standard tier, complaint_count=2.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-44782901
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                  booking_reference: BKG-99809402
                  hotel_id: HTL-88341276
                  booking_value: 310.0
                  request_type_detail: post-stay-issue
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-99809402
                refund_amount: '77.50'
                reason: post_stay_compensation
            - tool: crm_api_update_customer_info
              parameters:
                customer_id: CUS-44782901
                complaint_count: 3
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '14'
                item:
                  status: solved
                  description: 'Customer reports WiFi did not work for entire stay (2 nights, Sep 23-25, 2025) at budget partner hotel. Issue was reported to front desk multiple times during stay. Customer had to use mobile data for work calls. Complaint category: service (amenities unavailable). Timing: 6 days post-checkout (within 7-day window for standard customers). Customer: standard tier, complaint_count=2. RESOLUTION: Applied 25% compensation per service complaint policy (>48h ≤7 days, standard tier). Compensation calculated: $310 booking value × 25% = $77.50. Refund processed successfully. Transaction ID: TXN-00000011. Customer complaint_count updated to 3.'
                  resolution_action: refund-partial
                  refund_amount: 77.5
    """

    validate_database(x)


def test_psc_005(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I'm Marcus Wellington and I need to file a complaint about my recent stay. My email is marcus.wellington@horizon.net and my booking reference is BKG-61201836. I checked out on September 22nd and I had some really disappointing experiences with the staff. The valet was incredibly rude when I arrived and throughout my stay, and when I asked the concierge for help making restaurant reservations, they flat out refused to assist me. This is not the level of service I expect. I have email correspondence with the hotel staff documenting these issues that I can provide as evidence.
    user_context: |
        You are Marcus Wellington, a platinum tier customer contacting StayBridge support to file a complaint about poor service during your recent hotel stay. You experienced rude valet service and a concierge who refused to help with restaurant reservations. You have email correspondence with hotel staff as evidence of these issues.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If asked to confirm you have evidence or provide details about the evidence, confirm you have email correspondence showing your interactions with hotel staff regarding these service issues.
    init:
      external_booking_v1:
        data_patch:
          zendesk_users:
            - id: USR-10000007
              name: Marcus Wellington
              email: marcus.wellington@horizon.net
              role: end-user
              organization_id: ORG-10000002
              phone: +1-312-847-6294
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-61201836
              booking_reference: BKG-61201836
              customer_id: CUS-10000006
              hotel_id: HTL-61201836
              check_in_date: '2025-09-17T15:00:00Z'
              check_out_date: '2025-09-22T10:00:00Z'
              booking_value: '1250.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-08-10T14:30:00Z'
              updated_at: '2025-09-22T10:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-10000006
              customer_id: CUS-10000006
              email: marcus.wellington@horizon.net
              full_name: Marcus Wellington
              vip_tier: platinum
              loyalty_program_status: platinum-elite
              lifetime_value: '15000.00'
              total_bookings_count: 12
              preferences:
                - quiet room
                - early check-in
              special_notes:
                - business traveler, prefers express checkout
              complaint_count: 1
              last_booking_date: '2025-09-17T15:00:00Z'
              created_at: '2023-03-15T00:00:00Z'
              updated_at: '2025-09-22T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-61201836
              hotel_id: HTL-61201836
              hotel_name: Riverside Grand Hotel
              location: Chicago
              partner_tier: premium
              contact_name: Rebecca Morrison
              contact_email: contact@riversidegrand.com
              contact_phone: +1-312-594-8273
              escalation_contact: manager@riversidegrand.com
              amenities:
                - pool
                - spa
                - gym
                - restaurant
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
          payment_api_transactions:
            - id: TXN-61201836
              transaction_id: TXN-61201836
              booking_reference: BKG-61201836
              customer_id: CUS-10000006
              amount: '1250.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7821
              reason: null
              processing_time_estimate: null
              created_at: '2025-08-10T14:30:00Z'
              updated_at: '2025-08-10T14:30:00Z'
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.wellington@horizon.net'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-61201836'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-61201836
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-61201836
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-10000006
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Post-stay service complaint - BKG-61201836
                  description: 'Customer reports rude valet service and concierge who refused to help with restaurant reservations during stay 2025-09-17 to 2025-09-22. Customer has provided email correspondence as evidence. Platinum tier customer. Days since checkout: 9 days. Processing compensation per Section 4.4.3.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - vip-customer
                  booking_reference: BKG-61201836
                  hotel_id: HTL-61201836
                  booking_value: 1250.0
                  request_type_detail: post-stay-issue
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-61201836
                refund_amount: '625.00'
                reason: post_stay_compensation
            - tool: crm_api_update_customer_info
              parameters:
                customer_id: CUS-10000006
                complaint_count: 2
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  resolution_action: refund-partial
                  refund_amount: 625.0
    """

    validate_database(x)


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
              created_at: '2025-09-28T10:00:00Z'
              updated_at: '2025-09-28T10:00:00Z'
              due_at: null
              booking_reference: BKG-91022901
              hotel_id: HTL-48291056
              check_in_date: '2025-09-27T15:00:00Z'
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
              created_at: '2024-03-15T10:00:00Z'
              updated_at: '2024-03-15T10:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-91022901
              booking_reference: BKG-91022901
              customer_id: CUS-77234891
              hotel_id: HTL-48291056
              check_in_date: '2025-09-27T15:00:00Z'
              check_out_date: '2025-09-29T11:00:00Z'
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
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-29T11:00:00Z'
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
              last_booking_date: '2025-09-27T15:00:00Z'
              created_at: '2024-03-15T10:00:00Z'
              updated_at: '2025-09-27T15:00:00Z'
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
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2024-06-01T10:00:00Z'
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
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-91022901'
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
                filter: email eq 'marcus.webb@proton.me'
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
                  description: 'Post-stay room condition complaint for booking BKG-91022901. Customer reported minor cosmetic issues: peeling wallpaper in corner, slow drain in shower, missing TV remote. Customer provided photographic evidence confirming issues. Customer tier: VIP. Check-out: 2025-09-29T11:00:00Z. Complaint submitted approximately 50 hours post-checkout (>48h ≤7 days timing window). Severity classification: Minor (cosmetic issues, minor inconveniences per policy). No escalation required - all direct compensation criteria met. Compensation calculated per Section 4.4.3: 25% of booking_value ($245.00) = $61.25. Refund processed successfully. Transaction ID: TXN-00000008. Processing time: 3-5 business days, then 5-10 business days to appear on customer''s card. Complaint count incremented to 1.'
                  booking_reference: BKG-91022901
                  hotel_id: HTL-48291056
                  check_in_date: '2025-09-27T15:00:00Z'
                  booking_value: 245.0
                  request_type_detail: post-stay-issue
                  resolution_action: refund-partial
                  refund_amount: 61.25
    """

    validate_database(x)


def test_psc_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I just checked out from my recent stay and I'm rather disappointed. My name is Victoria Sterling, email victoria.sterling@proton.me, and my booking reference is BKG-80957015. The room had several issues - the minibar wasn't restocked at all, the coffee maker was dirty when I tried to use it, and there was a small tear in the bed sheets. I know these are mostly cosmetic things, but for what I paid, I expected better. I'd like to file a complaint and understand what can be done about this.
    user_context: |
        You are Victoria Sterling, a platinum tier customer who just checked out from Harbor View Suites. You're disappointed about minor room condition issues during your stay but remain polite and reasonable. You acknowledge the issues were cosmetic in nature.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-80957015
              customer_id: CUS-00000006
              hotel_id: HTL-00027891
              check_in_date: '2025-09-27T15:00:00Z'
              check_out_date: '2025-09-30T14:00:00Z'
              booking_value: '720.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-20T10:00:00Z'
              updated_at: '2025-09-30T14:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: victoria.sterling@proton.me
              full_name: Victoria Sterling
              vip_tier: platinum
              loyalty_program_status: platinum-elite
              lifetime_value: '8500.00'
              total_bookings_count: 12
              preferences:
                - king bed
                - quiet floor
              special_notes:
                - prefers morning contact hours
              complaint_count: 0
              last_booking_date: '2025-09-27T15:00:00Z'
              created_at: '2023-03-15T00:00:00Z'
              updated_at: '2025-09-30T14:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00027891
              hotel_name: Harbor View Suites
              location: Seattle, WA
              partner_tier: standard
              contact_name: Michelle Roberts
              contact_email: contact@harborviewsuites.com
              contact_phone: +1-206-847-3291
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-15T10:00:00Z'
              updated_at: '2025-01-15T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Victoria Sterling
              email: victoria.sterling@proton.me
              role: end-user
              organization_id: ORG-10000002
              phone: +1-206-739-4182
              verified: true
              active: true
              created_at: '2023-03-15T00:00:00Z'
              updated_at: '2023-03-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          zendesk_articles: []
          zendesk_organizations: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-80957015
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00027891
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'victoria.sterling@proton.me'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-80957015'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Post-stay room condition complaint - BKG-80957015
                  description: 'Customer reports minor room condition issues: minibar not restocked, coffee maker dirty, sheets with small tear. Customer is platinum tier VIP. Issues acknowledged as cosmetic by customer. Check-out: 2025-09-30. Reported within 48 hours. Processing 50% compensation per policy for platinum tier minor room condition issues.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - vip-customer
                  booking_reference: BKG-80957015
                  hotel_id: HTL-00027891
                  booking_value: 720.0
                  request_type_detail: post-stay-issue
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-80957015
                refund_amount: '360.00'
                reason: post_stay_compensation
            - tool: crm_api_update_customer_info
              parameters:
                customer_id: CUS-00000006
                complaint_count: 1
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  resolution_action: refund-partial
                  refund_amount: 360.0
    """

    validate_database(x)


def test_psc_009(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to report an issue with a recent stay. My name is Margaret Wilson, email margaret.wilson@outlook.com, and my booking reference is BKG-43039117. The bathroom in my room had mold in the corner - I only noticed it on day 2 of my stay. I reported it to the front desk but they told me no other rooms were available so I had to stay in that room. I took photos of the mold. What can be done about this?
    user_context: |
        You are Margaret Wilson, a customer who recently completed a stay at a hotel booked through StayBridge. You discovered mold in your bathroom on day 2 of your stay, reported it to the hotel staff, but were told no alternative rooms were available. You have photos of the mold as evidence.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If asked to confirm you have photos or evidence, confirm that you do have photos of the bathroom mold.
    init:
      external_booking_v1:
        data_patch:
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: margaret.wilson@outlook.com
              full_name: Margaret Wilson
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '1850.75'
              total_bookings_count: 4
              preferences:
                - quiet room
              special_notes: []
              complaint_count: 1
              last_booking_date: '2025-09-26T10:00:00Z'
              created_at: '2024-08-15T10:00:00Z'
              updated_at: '2025-09-26T12:00:00Z'
          booking_api_bookings:
            - id: BKG-43039117
              booking_reference: BKG-43039117
              customer_id: CUS-00000006
              hotel_id: HTL-00056789
              check_in_date: '2025-09-23T15:00:00Z'
              check_out_date: '2025-09-26T10:00:00Z'
              booking_value: '560.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-10T14:00:00Z'
              updated_at: '2025-09-26T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00056789
              hotel_name: Riverside Grand Hotel
              location: Chicago
              partner_tier: premium
              contact_name: Jennifer Martinez
              contact_email: manager@riversidegrand.com
              contact_phone: +1-312-847-6521
              escalation_contact: director@riversidegrand.com
              amenities:
                - pool
                - gym
                - restaurant
                - wifi
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-02-01T10:00:00Z'
              updated_at: '2025-02-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Margaret Wilson
              email: margaret.wilson@outlook.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-312-645-8923
              verified: true
              active: true
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2024-08-15T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          payment_api_transactions:
            - id: TXN-90000001
              transaction_id: TXN-90000001
              booking_reference: BKG-43039117
              customer_id: CUS-00000006
              amount: '560.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7832
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-10T14:30:00Z'
              updated_at: '2025-09-10T14:30:00Z'
        golden_test_case:
          tool_interactions:
            - tool: crm_api_get_customer_profile
              parameters:
                email: margaret.wilson@outlook.com
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-43039117
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00056789
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'margaret.wilson@outlook.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-43039117'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Post-stay room condition complaint - BKG-43039117
                  description: Customer reports bathroom mold issue from stay at Riverside Grand Hotel. Mold noticed on day 2 of stay, reported to hotel but no alternative rooms available. Customer has photographic evidence. Check-out was 2025-09-26. Complaint reported 5 days after checkout. Per policy Section 4.4.3, eligible for 25% compensation ($140) as standard customer with evidence within 7-day window.
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                  booking_reference: BKG-43039117
                  hotel_id: HTL-00056789
                  booking_value: 560.0
                  request_type_detail: post-stay-issue
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-43039117
                refund_amount: '140.00'
                reason: post_stay_compensation
            - tool: crm_api_update_customer_info
              parameters:
                customer_id: CUS-00000006
                complaint_count: 2
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  resolution_action: refund-partial
                  refund_amount: 140.0
                  description: 'Customer reports bathroom mold issue from stay at Riverside Grand Hotel. Mold noticed on day 2 of stay, reported to hotel but no alternative rooms available. Customer has photographic evidence. Check-out was 2025-09-26. Complaint reported 5 days after checkout. Per policy Section 4.4.3, eligible for 25% compensation as standard customer with evidence within 7-day window. Processed $140.00 refund. Transaction ID: TXN-00000008.'
    """

    validate_database(x)


def test_psc_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I just checked out of my hotel yesterday and I need to file a complaint. My name is Marcus Gray, email marcus.gray@hotmail.com, booking reference BKG-89638346. The air conditioning in my room was completely broken during my entire stay. It was 95 degrees outside and my room was like a sauna - I literally couldn't sleep at all. I had to go out and buy a portable fan just to get through the nights. I complained to the front desk but they didn't do anything about it or offer any kind of resolution. This was at Riverside Budget Inn in Phoenix. I'd like some kind of compensation for this terrible experience.
    user_context: |
        You are Marcus Gray, a customer who just checked out of Riverside Budget Inn in Phoenix after a terrible stay due to completely broken air conditioning. You are contacting StayBridge support to file a complaint and seek compensation.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If the agent offers compensation or a refund, accept it and thank them for their help.
    init:
      external_booking_v1:
        data_patch:
          zendesk_users:
            - id: USR-10000007
              name: Marcus Gray
              email: marcus.gray@hotmail.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-847-293-7614
              verified: true
              active: true
              created_at: '2025-04-18T00:00:00Z'
              updated_at: '2025-04-18T00:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-89638346
              customer_id: CUS-00000006
              hotel_id: HTL-00073241
              check_in_date: '2025-09-28T15:00:00Z'
              check_out_date: '2025-09-30T11:00:00Z'
              booking_value: '195.00'
              room_type: standard_room
              board_type: without_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-30T11:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: marcus.gray@hotmail.com
              full_name: Marcus Gray
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '876.50'
              total_bookings_count: 4
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-28T15:00:00Z'
              created_at: '2025-03-10T00:00:00Z'
              updated_at: '2025-09-30T11:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00073241
              hotel_name: Riverside Budget Inn
              location: Phoenix, Arizona
              partner_tier: budget
              contact_name: Rachel Morrison
              contact_email: info@riversidebudgetinn.com
              contact_phone: +1-602-847-2938
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: false
              created_at: '2025-02-15T10:00:00Z'
              updated_at: '2025-02-15T10:00:00Z'
          payment_api_transactions: []
          lookup_bookings: []
          lookup_hotels: []
          lookup_group_bookings: []
          lookup_corporate_accounts: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.gray@hotmail.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-89638346'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-89638346
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00073241
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Post-stay room condition complaint - BKG-89638346
                  description: 'Customer reports major room condition issue for completed stay. Air conditioning was completely broken during their stay when outside temperature was 95°F. Customer couldn''t sleep and had to purchase a portable fan. Hotel did not offer any resolution. Check-out: 2025-09-30. Complaint received within 48 hours of checkout. Processing compensation per Section 4.4.3.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                  booking_reference: BKG-89638346
                  hotel_id: HTL-00073241
                  booking_value: 195.0
                  request_type_detail: post-stay-issue
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-89638346
                refund_amount: '146.25'
                reason: post_stay_compensation
            - tool: crm_api_update_customer_info
              parameters:
                customer_id: CUS-00000006
                complaint_count: 1
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  tags:
                    - b2c-customer
                  booking_reference: BKG-89638346
                  hotel_id: HTL-00073241
                  booking_value: 195.0
                  request_type_detail: post-stay-issue
                  resolution_action: refund-partial
                  refund_amount: 146.25
    """

    validate_database(x)


def test_psc_011(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm extremely frustrated and need help with my recent stay. My name is Marcus Riley, email marcus.riley@hotmail.com, and my booking reference is BKG-57871331. I found BED BUGS in the mattress on the second night of my stay! I had to call the front desk at 2 AM and they moved me to another room. This was absolutely traumatic. I have photos of the bugs and the bites. I already contacted you about this 2 days ago and haven't heard back. I'm demanding a full refund for this nightmare experience.
    user_context: |
        You are Marcus Riley, a frustrated VIP customer who had a terrible hotel experience with bed bugs. You already reported this issue 2 days ago and are following up because you haven't received resolution.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If asked about photos, confirm you have clear photos of the bed bugs and can provide them.
        - If the agent offers a partial refund instead of full refund, you may express disappointment about it being less than you expected, but ultimately accept the resolution if they explain the policy.
    init:
      external_booking_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-50983930
              subject: Bed bugs complaint - room condition issue
              description: Customer found bed bugs in mattress on second night of stay
              status: pending
              priority: high
              type: problem
              requester_id: USR-48291735
              assignee_id: AG-83945
              organization_id: ORG-10000002
              tags:
                - post-stay
                - room-condition
              created_at: '2025-09-29T14:00:00Z'
              updated_at: '2025-09-30T10:00:00Z'
              due_at: null
              booking_reference: BKG-57871331
              hotel_id: HTL-73829104
              check_in_date: '2025-09-27T15:00:00Z'
              booking_value: 480.0
              request_type_detail: post-stay-issue
              corporate_account_id: null
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-48291735
              name: Marcus Riley
              email: marcus.riley@hotmail.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-312-594-8273
              verified: true
              active: true
              created_at: '2024-05-15T10:00:00Z'
              updated_at: '2024-05-15T10:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-57871331
              customer_id: CUS-48291735
              hotel_id: HTL-73829104
              check_in_date: '2025-09-27T15:00:00Z'
              check_out_date: '2025-09-29T10:00:00Z'
              booking_value: '480.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-20T10:00:00Z'
              updated_at: '2025-09-29T10:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-48291735
              customer_id: CUS-48291735
              email: marcus.riley@hotmail.com
              full_name: Marcus Riley
              vip_tier: vip
              loyalty_program_status: gold
              lifetime_value: '8450.50'
              total_bookings_count: 15
              preferences:
                - late checkout
                - quiet room
              special_notes:
                - prefers email communication
              complaint_count: 2
              last_booking_date: '2025-09-29T10:00:00Z'
              created_at: '2024-05-15T10:00:00Z'
              updated_at: '2025-09-01T12:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-73829104
              hotel_name: Riverside Suites
              location: Chicago
              partner_tier: standard
              contact_name: Jennifer Walsh
              contact_email: manager@riversidesuites.com
              contact_phone: +1-312-847-6291
              escalation_contact: null
              amenities:
                - wifi
                - gym
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-57871331'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-50983930
                item:
                  status: open
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-57871331
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-48291735
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-73829104
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-57871331
                refund_amount: '120.00'
                reason: post_stay_compensation
            - tool: crm_api_update_customer_info
              parameters:
                customer_id: CUS-48291735
                complaint_count: 3
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-50983930
                item:
                  status: solved
                  type: task
                  priority: normal
                  tags:
                    - b2c-customer
                    - vip-customer
                  request_type_detail: post-stay-issue
                  resolution_action: refund-partial
                  booking_reference: BKG-57871331
                  hotel_id: HTL-73829104
                  check_in_date: '2025-09-27T15:00:00Z'
                  booking_value: 480.0
                  refund_amount: 120.0
    """

    validate_database(x)


def test_psc_012(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to report a serious safety issue from my recent stay. I'm Marcus Brennan, email marcus.brennan@outlook.com, and my booking reference is BKG-10310518. The hot water in my room was dangerously scalding - I nearly got burned when I tried to shower. There was no way to adjust the temperature properly, the shower controls didn't work. I literally had to go down to the hotel gym to shower the entire stay. This is completely unacceptable for a premium hotel.
    user_context: |
        You are Marcus Brennan, a platinum tier loyalty customer who just completed a stay at Premium Plaza Hotel. You experienced a serious safety issue where the hot water was scalding hot and nearly burned you. The shower had no functioning temperature controls, forcing you to use the gym facilities to shower during your entire stay. You are frustrated but expect appropriate resolution given your loyalty status.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-10310518
              booking_reference: BKG-10310518
              customer_id: CUS-00045678
              hotel_id: HTL-00098765
              check_in_date: '2025-09-28T15:00:00Z'
              check_out_date: '2025-09-30T12:00:00Z'
              booking_value: '1450.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-30T12:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00045678
              customer_id: CUS-00045678
              email: marcus.brennan@outlook.com
              full_name: Marcus Brennan
              vip_tier: platinum
              loyalty_program_status: platinum-elite
              lifetime_value: '28750.00'
              total_bookings_count: 42
              preferences:
                - quiet room
                - high floor
              special_notes:
                - prefers early check-in when available
              complaint_count: 0
              last_booking_date: '2025-09-28T15:00:00Z'
              created_at: '2022-03-15T00:00:00Z'
              updated_at: '2025-09-30T12:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00098765
              hotel_id: HTL-00098765
              hotel_name: Premium Plaza Hotel
              location: New York
              partner_tier: premium
              contact_name: Victoria Reynolds
              contact_email: manager@premiumplazahotel.com
              contact_phone: +1-212-847-3295
              escalation_contact: director@premiumplazahotel.com
              amenities:
                - pool
                - gym
                - spa
                - restaurant
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2024-06-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Brennan
              email: marcus.brennan@outlook.com
              role: end-user
              organization_id: null
              phone: +1-646-273-8194
              verified: true
              active: true
              created_at: '2022-03-15T00:00:00Z'
              updated_at: '2022-03-15T00:00:00Z'
          payment_api_transactions:
            - id: TXN-10310518
              transaction_id: TXN-10310518
              booking_reference: BKG-10310518
              customer_id: CUS-00045678
              amount: '1450.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7821
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
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
                booking_reference: BKG-10310518
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00045678
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00098765
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.brennan@outlook.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-10310518'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Post-stay complaint - BKG-10310518
                  description: 'Customer reports major safety concern with hot water system at Premium Plaza Hotel. Water was scalding hot and nearly caused burns. Shower had no way to adjust temperature properly. Customer had to use gym facilities to shower. Complaint reported within 25 hours of checkout (≤48h). Customer VIP tier: platinum, complaint_count: 0. Applying room condition compensation policy - Major severity.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  booking_reference: BKG-10310518
                  hotel_id: HTL-00098765
                  booking_value: 1450.0
                  request_type_detail: post-stay-issue
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-10310518
                refund_amount: '1450.00'
                reason: post_stay_compensation
            - tool: crm_api_update_customer_info
              parameters:
                customer_id: CUS-00045678
                complaint_count: 1
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  tags:
                    - b2c-customer
                    - vip-customer
                  resolution_action: refund-full
                  refund_amount: 1450.0
    """

    validate_database(x)


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
              check_in_date: '2025-09-28T15:00:00Z'
              check_out_date: '2025-09-30T10:00:00Z'
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
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-30T10:00:00Z'
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
              last_booking_date: '2025-09-28T15:00:00Z'
              created_at: '2025-02-15T10:00:00Z'
              updated_at: '2025-09-30T12:00:00Z'
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
              created_at: '2025-09-28T14:30:00Z'
              updated_at: '2025-09-28T14:30:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Jenkins
              email: marcus.jenkins@hotmail.com
              role: end-user
              organization_id: null
              phone: +1-404-892-6743
              verified: true
              active: true
              created_at: '2025-02-15T10:00:00Z'
              updated_at: '2025-02-15T10:00:00Z'
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
              created_at: '2025-01-10T10:00:00Z'
              updated_at: '2025-01-10T10:00:00Z'
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
                filter: booking_reference eq 'BKG-56670106'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.jenkins@hotmail.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Billing overcharge correction - BKG-56670106
                  description: 'Customer reported billing discrepancy for completed stay. Original request: Customer was charged $325 but booking confirmation shows $275. Key data: Booking BKG-56670106, booking_value $275, transaction shows $325 charge. No modification history found. Customer provided booking confirmation as evidence. Standard tier customer, budget partner hotel. Policy applied: Section 4.3.5 Billing Overcharge Corrections. Overcharge of $50 identified as system error. Reported 27 hours after checkout (≤48h), 10% courtesy credit applied. Actions: Processing refund of $55.00 ($50 overcharge + $5 courtesy credit). Resolution: Billing error corrected with partial refund.'
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
    """

    validate_database(x)


def test_psc_016(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm Marcus Reynolds and I stayed at The Harrington Grand in Chicago recently. My booking reference is BKG-10801326 and my email is marcus.reynolds@cloudtech.io. I have a billing issue - I was charged twice for room service. There's an $85 charge that appears twice on my credit card statement. I have my statement right here showing both charges. Can you help me get this corrected?
    user_context: |
        You are Marcus Reynolds, a customer who stayed at The Harrington Grand hotel and discovered a duplicate room service charge on your credit card statement after checkout. You were charged $85 twice for the same room service.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If asked to confirm you want to proceed with escalation to the hotel, confirm yes.
        If asked about the evidence, confirm you have your credit card statement showing both $85 charges for room service.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-10801326
              booking_reference: BKG-10801326
              customer_id: CUS-10801326
              hotel_id: HTL-10801326
              check_in_date: '2025-09-19T15:00:00Z'
              check_out_date: '2025-09-21T10:00:00Z'
              booking_value: '980.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-21T10:30:00Z'
          crm_api_customer_profiles:
            - id: CUS-10801326
              customer_id: CUS-10801326
              email: marcus.reynolds@cloudtech.io
              full_name: Marcus Reynolds
              vip_tier: platinum
              loyalty_program_status: active
              lifetime_value: '15000.00'
              total_bookings_count: 12
              preferences:
                - sea view
                - quiet room
              special_notes:
                - prefers early check-in when available
              complaint_count: 2
              last_booking_date: '2025-09-21T10:00:00Z'
              created_at: '2023-03-15T09:00:00Z'
              updated_at: '2025-09-21T10:30:00Z'
          hotel_partner_api_hotels:
            - id: HTL-10801326
              hotel_id: HTL-10801326
              hotel_name: The Harrington Grand
              location: Chicago
              partner_tier: premium
              contact_name: Victoria Chambers
              contact_email: frontdesk@harringtongrand.com
              contact_phone: +1-312-847-9245
              escalation_contact: manager@harringtongrand.com
              amenities:
                - spa
                - gym
                - restaurant
                - wifi
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2024-06-01T09:00:00Z'
              updated_at: '2024-06-01T09:00:00Z'
          payment_api_transactions:
            - id: TXN-10801326
              transaction_id: TXN-10801326
              booking_reference: BKG-10801326
              customer_id: CUS-10801326
              amount: '980.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7829
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-17T14:30:00Z'
              updated_at: '2025-09-17T14:30:00Z'
          zendesk_users:
            - id: USR-10801326
              name: Marcus Reynolds
              email: marcus.reynolds@cloudtech.io
              role: end-user
              organization_id: null
              phone: +1-312-495-7831
              verified: true
              active: true
              created_at: '2023-03-15T09:00:00Z'
              updated_at: '2023-03-15T09:00:00Z'
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
                booking_reference: BKG-10801326
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-10801326
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-10801326
            - tool: payment_api_get_transaction_history
              parameters:
                booking_reference: BKG-10801326
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-10801326'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.reynolds@cloudtech.io'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Post-stay billing dispute - BKG-10801326
                  description: 'Customer reports duplicate room service charge of $85 (charged twice) at premium partner hotel. Checkout date: 2025-09-21. Days since checkout: 10 days. Customer has credit card statement as evidence showing both charges. Customer is platinum VIP tier (entitled to 14-day complaint window). Escalation to hotel partner required for verification. Note: Customer vip_tier=platinum, hotel-partner-escalation required (documented here as tags filtered by system).'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10801326
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                  booking_reference: BKG-10801326
                  hotel_id: HTL-10801326
                  booking_value: 980.0
                  request_type_detail: post-stay-issue
            - tool: hotel_partner_api_escalate_to_hotel
              parameters:
                hotel_id: HTL-10801326
                booking_reference: BKG-10801326
                issue_type: guest-complaint
                description: 'Guest disputes billing - claims double-charged for room service at $85 each (total duplicate charge: $85). Customer checkout: 2025-09-21. Customer has provided credit card statement showing both charges as evidence. Requesting verification of room service charges and correction if duplicate charge confirmed. Platinum VIP customer - 14-day complaint window applies. Complaint reported within eligible window (10 days post-checkout).'
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: hold
                  tags:
                    - b2c-customer
                    - vip-customer
                    - hotel-partner-escalation
                  escalation_reason: guest-complaint
                  refund_amount: 0
    """

    validate_database(x)


def test_psc_018(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to report a serious issue from my stay. I checked out yesterday from the Riverside Budget Inn and the shower door glass completely shattered while I was using it! Thankfully I wasn't injured but I was extremely shaken - there was broken glass everywhere in the bathroom. I took photos of the damage. My booking reference is BKG-34309805 and my email is victoria.meadows@proton.me. This was a major safety hazard and I'd like to know what you can do about this.
    user_context: |
        You are Victoria Meadows, a customer contacting support about a serious safety incident during your recent hotel stay. The shower door glass shattered while you were using it. You were not injured but were very shaken by the experience. You have photos of the broken glass on your phone.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        If asked about the incident details: The glass shattered suddenly while you were in the shower. You were able to carefully step out and avoid injury, but there was glass all over the bathroom floor. You were alone at the time and it was very frightening.

        If asked about photos: Confirm you have several photos showing the broken glass scattered on the bathroom floor and the empty shower door frame.
    init:
      external_booking_v1:
        data_patch:
          zendesk_users:
            - id: USR-10000007
              name: Victoria Meadows
              email: victoria.meadows@proton.me
              role: end-user
              organization_id: null
              phone: +1-773-418-5629
              verified: true
              active: true
              created_at: '2025-03-15T10:00:00Z'
              updated_at: '2025-03-15T10:00:00Z'
          zendesk_tickets: []
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-34309805
              customer_id: CUS-00000006
              hotel_id: HTL-00055678
              check_in_date: '2025-09-27T15:00:00Z'
              check_out_date: '2025-09-30T12:00:00Z'
              booking_value: '620.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: checked_out
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-30T12:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: victoria.meadows@proton.me
              full_name: Victoria Meadows
              vip_tier: vip
              loyalty_program_status: silver
              lifetime_value: '7850.25'
              total_bookings_count: 12
              preferences:
                - quiet room
                - high floor
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-09-30T12:00:00Z'
              created_at: '2024-08-15T00:00:00Z'
              updated_at: '2025-09-30T12:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00055678
              hotel_name: Riverside Budget Inn
              location: Chicago
              partner_tier: budget
              contact_name: Raymond Blake
              contact_email: manager@riversidebudgetinn.com
              contact_phone: +1-312-847-2093
              escalation_contact: null
              amenities:
                - wifi
                - parking
              supports_pets: false
              accessible_rooms_available: false
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions:
            - id: TXN-00000010
              transaction_id: TXN-00000010
              booking_reference: BKG-34309805
              customer_id: CUS-00000006
              amount: '620.00'
              currency: USD
              transaction_type: charge
              payment_status: successful
              payment_method: Visa ending in 7291
              reason: null
              processing_time_estimate: null
              created_at: '2025-09-01T10:00:00Z'
              updated_at: '2025-09-01T10:00:00Z'
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'victoria.meadows@proton.me'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-34309805'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-34309805
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00055678
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Post-stay room condition complaint - BKG-34309805
                  description: 'Customer reports major room condition issue: shower door glass shattered while in use during stay. Customer was not injured but was shaken. Customer has provided photo evidence of broken glass. VIP tier customer (vip). Checkout: 2025-09-30, complaint filed within 48 hours.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - vip-customer
                  booking_reference: BKG-34309805
            - tool: payment_api_process_refund
              parameters:
                booking_reference: BKG-34309805
                refund_amount: '465.00'
                reason: post_stay_compensation
            - tool: crm_api_update_customer_info
              parameters:
                customer_id: CUS-00000006
                complaint_count: 1
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  description: 'Customer reports major room condition issue: shower door glass shattered while in use during stay. Customer was not injured but was shaken. Customer has provided photo evidence of broken glass. VIP tier customer (vip). Checkout: 2025-09-30, complaint filed within 48 hours.


                    Resolution: Verified booking BKG-34309805 at budget partner hotel, checkout 2025-09-30. Complaint received within 48 hours of checkout. Issue classified as Major room condition (safety concern - shattered glass). Customer vip_tier = vip, complaint_count = 0. Per policy Section 4.4.3, compensation = 75% of booking_value ($620) = $465. Processed partial refund of $465.00. Customer complaint_count incremented to 1.'
                  tags:
                    - b2c-customer
                    - vip-customer
                  booking_reference: BKG-34309805
                  hotel_id: HTL-00055678
                  booking_value: 620.0
                  request_type_detail: post-stay-issue
                  resolution_action: refund-partial
                  refund_amount: 465.0
    """

    validate_database(x)


def test_pss_003(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there! I have a booking coming up on October 5th and I was hoping to arrange an early check-in. My booking reference is BKG-19399091 and my email is thomas.rivera@gmail.com. Would it be possible to check in at 11:00 AM instead of the regular 3:00 PM check-in time?
    user_context: |
        You are Thomas Rivera, a customer who wants to arrange early check-in for your upcoming hotel booking. You want to check in at 11:00 AM instead of the standard 3:00 PM.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.

        ADDITIONAL CONTEXT:
        - If the agent mentions a $25 fee for early check-in, accept it and confirm you want to proceed.
    init:
      external_booking_v1:
        data_patch:
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: thomas.rivera@gmail.com
              full_name: Thomas Rivera
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '850.00'
              total_bookings_count: 3
              preferences:
                - early check-in
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-15T12:00:00Z'
              created_at: '2025-03-10T09:00:00Z'
              updated_at: '2025-08-15T12:00:00Z'
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-19399091
              customer_id: CUS-00000006
              hotel_id: HTL-29384756
              check_in_date: '2025-10-05T15:00:00Z'
              check_out_date: '2025-10-08T11:00:00Z'
              booking_value: '450.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-20T10:00:00Z'
              updated_at: '2025-09-20T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-29384756
              hotel_name: Riverside Luxury Hotel
              location: Chicago
              partner_tier: premium
              contact_name: Jennifer Walsh
              contact_email: reservations@riversideluxury.com
              contact_phone: +1-312-847-5293
              escalation_contact: manager@riversideluxury.com
              amenities:
                - pool
                - spa
                - gym
                - restaurant
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Thomas Rivera
              email: thomas.rivera@gmail.com
              role: end-user
              organization_id: ORG-10000002
              phone: +1-312-491-7832
              verified: true
              active: true
              created_at: '2025-03-10T09:00:00Z'
              updated_at: '2025-03-10T09:00:00Z'
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
            - tool: crm_api_get_customer_profile
              parameters:
                email: thomas.rivera@gmail.com
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-19399091
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-29384756
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-19399091'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'thomas.rivera@gmail.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Early check-in request - BKG-19399091
                  description: 'Customer requests early check-in at 11:00 AM instead of standard 3:00 PM for booking BKG-19399091. Check-in date: 2025-10-05. Request made 4 days in advance. Customer VIP tier: standard. Hotel partner tier: premium. Early check-in fee: $25 applies.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-19399091
                  hotel_id: HTL-29384756
            - tool: payment_api_process_charge
              parameters:
                booking_reference: BKG-19399091
                charge_amount: '25.00'
                reason: early_check_in_fee
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-19399091
                special_requests:
                  - Early check-in at 11:00 AM (subject to availability)
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  check_in_date: '2025-10-05T15:00:00Z'
                  booking_value: 450.0
                  request_type_detail: add-special-request
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_pss_007(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there! I have an upcoming booking at the Skyline Grand Hotel in San Francisco and I'd like to request a room preference if possible. I'm hoping to get a high floor room, preferably above floor 10, with a city view. My booking reference is BKG-41241182 and I'm checking in on October 12th. My name is Marcus Reynolds and my email is marcus.reynolds@outlook.com. Is this something you can help me with?
    user_context: |
        You are Marcus Reynolds, a customer contacting support to request a room preference for your upcoming hotel booking. You want a high floor room (above floor 10) with a city view at the Skyline Grand Hotel.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent confirms your request has been added, thank them and end the conversation.
        - You understand this is a preference request and may be subject to availability.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-41241182
              customer_id: CUS-00098765
              hotel_id: HTL-00045678
              check_in_date: '2025-10-12T15:00:00Z'
              check_out_date: '2025-10-15T11:00:00Z'
              booking_value: '520.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          crm_api_customer_profiles:
            - id: CUS-00098765
              customer_id: CUS-00098765
              email: marcus.reynolds@outlook.com
              full_name: Marcus Reynolds
              vip_tier: standard
              loyalty_program_status: member
              lifetime_value: '1250.00'
              total_bookings_count: 3
              preferences: []
              special_notes: []
              complaint_count: 0
              last_booking_date: '2025-08-20T14:00:00Z'
              created_at: '2025-03-15T10:00:00Z'
              updated_at: '2025-09-15T12:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00045678
              hotel_name: Skyline Grand Hotel
              location: San Francisco
              partner_tier: premium
              contact_name: Jennifer Walsh
              contact_email: reservations@skylinegrand.com
              contact_phone: +1-415-892-3174
              escalation_contact: manager@skylinegrand.com
              amenities:
                - pool
                - gym
                - spa
                - restaurant
                - concierge
              supports_pets: true
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          zendesk_users:
            - id: USR-10000007
              name: Marcus Reynolds
              email: marcus.reynolds@outlook.com
              role: end-user
              organization_id: null
              phone: +1-628-547-3891
              verified: true
              active: true
              created_at: '2025-03-15T10:00:00Z'
              updated_at: '2025-03-15T10:00:00Z'
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
                booking_reference: BKG-41241182
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00098765
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00045678
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-41241182'
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'marcus.reynolds@outlook.com'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Room preference request - BKG-41241182
                  description: 'Customer requests high floor room (preferably above floor 10) with city view for booking BKG-41241182. Check-in: 2025-10-12. This is a room preference request which is best effort, not guaranteed. No fee applies. Customer tier: standard. Hotel tier: premium.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                  booking_reference: BKG-41241182
                  hotel_id: HTL-00045678
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-41241182
                special_requests:
                  - High floor room requested (preferably above floor 10) with city view - subject to availability
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  check_in_date: '2025-10-12T15:00:00Z'
                  booking_value: 520.0
                  request_type_detail: add-special-request
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_pss_008(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I have a booking coming up and I'd like to request a quiet room. Can you help with that?
    user_context: |
        You are Marcus Reid, a VIP customer contacting StayBridge support to request a quiet room preference for your upcoming booking. You are a light sleeper and want a room away from elevators and ice machines.

        Only if you are asked for your booking reference or booking number — tell the agent it is BKG-44935348.
        Only if you are asked about which property or hotel — tell the agent it is Riverside Inn.
        Only if you are asked when your booking is or when you're staying — tell the agent it is next week.
        Only if you are asked for your name or to identify yourself — tell the agent your name is Marcus Reid.
        Only if you are asked for your email address — tell the agent it is marcus.reid@outlook.com.
        Only if you are asked about specific room preferences or what kind of quiet room you want — tell the agent you'd like a room away from the elevators and ice machines.
        Only if you are asked why you need a quiet room — tell the agent you are a light sleeper.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - When the agent confirms your room preference has been added to your booking, acknowledge and thank them.
    init:
      external_booking_v1:
        data_patch:
          zendesk_tickets:
            - id: TCK-74016400
              subject: Room preference request - quiet room
              description: Customer requesting quiet room away from elevators and ice machines due to being a light sleeper
              status: open
              priority: normal
              type: task
              requester_id: USR-10000007
              assignee_id: AG-83945
              organization_id: ORG-10000001
              tags:
                - special-request
                - room-preference
              due_at: null
              created_at: '2025-09-30T13:00:00Z'
              updated_at: '2025-09-30T13:00:00Z'
              booking_reference: BKG-44935348
              hotel_id: HTL-00012350
              check_in_date: '2025-10-07T15:00:00Z'
              booking_value: 410.0
              request_type_detail: add-special-request
              corporate_account_id: null
              group_booking_id: null
              resolution_action: null
              refund_amount: null
              escalation_reason: null
          zendesk_users:
            - id: USR-10000007
              name: Marcus Reid
              email: marcus.reid@outlook.com
              role: end-user
              organization_id: ORG-10000001
              phone: +1-312-847-3921
              verified: true
              active: true
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-44935348
              customer_id: CUS-00000006
              hotel_id: HTL-00012350
              check_in_date: '2025-10-07T15:00:00Z'
              check_out_date: '2025-10-09T11:00:00Z'
              booking_value: '410.00'
              room_type: standard_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_hotel_inventory: []
          booking_api_group_bookings: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00000006
              email: marcus.reid@outlook.com
              full_name: Marcus Reid
              vip_tier: vip
              loyalty_program_status: silver
              lifetime_value: '3250.75'
              total_bookings_count: 12
              preferences:
                - quiet room
                - high floor
              special_notes:
                - light sleeper, prefers rooms away from elevators
              complaint_count: 0
              last_booking_date: '2025-09-15T10:00:00Z'
              created_at: '2024-06-01T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00012350
              hotel_name: Riverside Inn
              location: Chicago
              partner_tier: standard
              contact_name: Jennifer Walsh
              contact_email: reservations@riversideinn.com
              contact_phone: +1-312-528-7412
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - gym
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions: []
        golden_test_case:
          tool_interactions:
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-44935348'
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-44935348
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00000006
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00012350
            - tool: booking_api_modify_booking
              parameters:
                booking_reference: BKG-44935348
                special_requests:
                  - Quiet room away from elevators and ice machines (subject to availability)
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: TCK-74016400
                item:
                  status: solved
                  priority: normal
                  type: task
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                  booking_reference: BKG-44935348
                  hotel_id: HTL-00012350
                  check_in_date: '2025-10-07T15:00:00Z'
                  booking_value: 410.0
                  request_type_detail: add-special-request
                  resolution_action: modification-completed
                  refund_amount: 0
    """

    validate_database(x)


def test_pss_010(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there! I have a booking coming up at the Riverside Garden Hotel - booking reference BKG-01128059. My name is Natasha Reynolds and my email is natasha.reynolds@protonmail.com. I wanted to ask about bringing my dog with me - she's a small dog, under 20 lbs. Is pet accommodation available for my stay?
    user_context: |
        You are Natasha Reynolds, a platinum tier customer contacting support to inquire about bringing your small dog (under 20 lbs) to your upcoming hotel stay. You have a confirmed booking at Riverside Garden Hotel.

        RULES:
        - Do not invent or provide any data not present in the provided context.
        - Do not change your goal or switch topics.
        - If asked for the same info, provide it again.
        - Remain focused, clear, and patient.
        - Answer agent's questions briefly and directly.
        - After sending a message you must always wait for a response message before sending a new one.
        - If the agent informs you that the hotel does not accommodate pets, accept this explanation politely. You may express mild disappointment but do not argue or demand alternatives unless you genuinely want to explore other options.
    init:
      external_booking_v1:
        data_patch:
          booking_api_bookings:
            - id: BKG-00000006
              booking_reference: BKG-01128059
              customer_id: CUS-00473829
              hotel_id: HTL-00056721
              check_in_date: '2025-10-09T15:00:00Z'
              check_out_date: '2025-10-12T11:00:00Z'
              booking_value: '490.00'
              room_type: deluxe_room
              board_type: with_breakfast
              adults_count: 2
              children_count: 0
              booking_status: confirmed
              corporate_account_id: null
              group_booking_id: null
              modification_history: []
              special_requests: []
              created_at: '2025-09-15T10:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          booking_api_group_bookings: []
          booking_api_hotel_inventory: []
          corporate_api_corporate_accounts: []
          crm_api_customer_profiles:
            - id: CUS-00000006
              customer_id: CUS-00473829
              email: natasha.reynolds@protonmail.com
              full_name: Natasha Reynolds
              vip_tier: platinum
              loyalty_program_status: platinum-elite
              lifetime_value: '32500.00'
              total_bookings_count: 45
              preferences:
                - quiet room
                - high floor
              special_notes:
                - prefers early check-in when available
              complaint_count: 1
              last_booking_date: '2025-09-10T14:00:00Z'
              created_at: '2023-06-01T00:00:00Z'
              updated_at: '2025-09-15T10:00:00Z'
          hotel_partner_api_hotels:
            - id: HTL-00000006
              hotel_id: HTL-00056721
              hotel_name: Riverside Garden Hotel
              location: Chicago
              partner_tier: standard
              contact_name: Jennifer Morrison
              contact_email: contact@riversidegarden.com
              contact_phone: +1-312-847-2396
              escalation_contact: null
              amenities:
                - wifi
                - parking
                - restaurant
              supports_pets: false
              accessible_rooms_available: true
              created_at: '2025-01-01T10:00:00Z'
              updated_at: '2025-01-01T10:00:00Z'
          payment_api_transactions: []
          zendesk_tickets: []
          zendesk_users:
            - id: USR-10000007
              name: Natasha Reynolds
              email: natasha.reynolds@protonmail.com
              role: end-user
              organization_id: null
              phone: +1-312-582-7493
              verified: true
              active: true
              created_at: '2024-03-15T00:00:00Z'
              updated_at: '2024-03-15T00:00:00Z'
          zendesk_organizations: []
          zendesk_comments: []
          zendesk_ticket_comments: []
          zendesk_articles: []
        golden_test_case:
          tool_interactions:
            - tool: booking_api_get_booking
              parameters:
                booking_reference: BKG-01128059
            - tool: crm_api_get_customer_profile
              parameters:
                customer_id: CUS-00473829
            - tool: hotel_partner_api_get_hotel_info
              parameters:
                hotel_id: HTL-00056721
            - tool: zendesk_get_items
              parameters:
                table: users
                filter: email eq 'natasha.reynolds@protonmail.com'
            - tool: zendesk_get_items
              parameters:
                table: tickets
                filter: booking_reference eq 'BKG-01128059'
            - tool: zendesk_create_item
              parameters:
                table: tickets
                item:
                  subject: Pet accommodation request - BKG-01128059
                  description: 'Platinum customer requesting pet accommodation for small dog (under 20 lbs). Hotel does not support pets (supports_pets = false). Customer VIP tier: platinum. Request cannot be fulfilled per hotel policy.'
                  status: open
                  priority: normal
                  type: task
                  requester_id: USR-10000007
                  assignee_id: AG-83945
                  tags:
                    - b2c-customer
                    - check-in-upcoming
                    - vip-customer
                  booking_reference: BKG-01128059
                  hotel_id: HTL-00056721
                  booking_value: 490.0
                  request_type_detail: add-special-request
            - tool: zendesk_update_item
              parameters:
                table: tickets
                id: '13'
                item:
                  status: solved
                  resolution_action: policy-applied-no-action
                  refund_amount: 0
    """

    validate_database(x)
