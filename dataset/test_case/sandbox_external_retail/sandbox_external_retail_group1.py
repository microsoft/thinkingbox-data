# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json

from thinkingbox.common import Judge, TestContext

"""!
scenario: sandbox_external_retail
"""


def validate_database(x: TestContext):
    result_db_hash = x.effects["sandbox_external_retail"]["result_db_hash"]
    golden_db_hash = x.effects["sandbox_external_retail"]["golden_db_hash"]

    if result_db_hash != golden_db_hash:
        diff = x.effects["sandbox_external_retail"].get("diff", [])
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


def test_case_ST002_001(x: TestContext, judge: Judge):
    """!
    query: Hi, my order ORD-70020 for the Bluetooth soundbar was supposed to arrive 7 days ago, but it's still delayed according to UPS tracking (TRK-700200001). I placed the order 18 days ago and I'm really frustrated with the long wait. Can you tell me what's going on and if I'm eligible for any compensation?
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      If asked for additional information, you may provide:

      - Identity: Name Alex Kim, email [alex.kim@example.com](mailto:alex.kim@example.com)
      - Order details: order ID ORD-70020, placed about 18 days ago, estimated delivery was about 11 days ago, status shows delayed in tracking
      - Frustration: waiting more than a week past ETA and want an updated delivery timeline
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10003'
            name: Alex Kim
            email: alex.kim@example.com
            role: end-user
            organization_id: null
            phone: +1-555-0203
            verified: true
            active: true
            created_at: '2025-09-13T10:00:00Z'
            updated_at: '2025-09-13T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-70020
            customer_id: CUS-30020
            order_date: '2025-09-13T10:30:00Z'
            status: shipped
            subtotal_amount: 435
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 435
            shipping_address_line1: 789 Pine St
            shipping_address_city: Springfield
            shipping_address_state: IL
            shipping_address_zip: '62703'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SH-70020-001
            order_id: ORD-70020
            carrier: UPS
            tracking_number: TRK-700200001
            ship_date: '2025-09-14T09:15:00Z'
            estimated_delivery_date: '2025-09-20T17:00:00Z'
            actual_delivery_date: null
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-700200001
            shipment_id: SH-70020-001
            carrier: UPS
            status: delayed
            current_location: Springfield, IL hub
            estimated_delivery: '2025-10-03T17:00:00Z'
            last_update: '2025-09-30T16:00:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LI-70020-001
            order_id: ORD-70020
            sku: SND-8720
            product_name: Bluetooth soundbar
            quantity: 1
            base_price: 435
            discount_amount: 0
            final_price: 435
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-70020-001
            order_id: ORD-70020
            customer_id: CUS-30020
            amount: 435
            status: authorized
            payment_method: Visa ending in 5678
            transaction_date: '2025-09-13T10:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: SND-8720
            available_quantity: 15
            reserved_quantity: 1
            warehouse_location: MAIN-D10
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: SND-8720
            name: Bluetooth soundbar
            category: audio_video
            brand: TechHome
            base_price: 435
            weight_lbs: 8.5
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-30020
            email: alex.kim@example.com
            name: Alex Kim
            phone: +1-555-0203
            registration_date: '2025-01-15T14:30:00Z'
            customer_tier: standard
            lifetime_value: 435
            total_orders: 3
            customer_score: 85
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.25
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Delayed shipment
                priority: normal
                assignee_id: '2'
                description: Customer reports order ORD-70020 is delayed; tracking shows carrier-reported delay about a week past ETA.
                requester_id: '10003'
                organization_id: null
              table: tickets
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST002_003(x: TestContext, judge: Judge):
    """!
    query: I'm following up on my order for the KitchenAid mixer. It was shipped over two weeks ago, and the estimated delivery date of September 23rd has passed by over a week. The tracking still just says 'delayed'. I already contacted support about this and was told to wait, but nothing has happened. This is very frustrating. What can you do for me about this significant delay? Am I eligible for any compensation?
    user_context: |-
      - You are Sarah
      - If the agent asks for the email, it's [sarah.martinez@email.com](mailto:sarah.martinez@email.com).
      - If the agent asks for the order ID, it's ORD-10000020



      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: null
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-03-12T09:30:00Z'
            updated_at: '2024-03-12T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '20'
            subject: Order Status Inquiry - Delayed Delivery
            description: Customer inquiring about order ORD-10000020 status. Order shipped on 2025-09-17 with estimated delivery 2025-09-23 but showing delayed status. Customer advised to wait for carrier updates.
            status: solved
            priority: normal
            type: incident
            requester_id: '10'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-27T10:15:00Z'
            updated_at: '2025-09-27T16:30:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000020
            customer_id: CUS-10000010
            order_date: '2025-09-15T14:30:00Z'
            status: shipped
            subtotal_amount: 1245
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1245
            shipping_address_line1: 789 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000020
            order_id: ORD-10000020
            carrier: UPS
            tracking_number: TRK-100000000020
            ship_date: '2025-09-17T09:15:00Z'
            estimated_delivery_date: '2025-09-23T17:00:00Z'
            actual_delivery_date: null
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000020
            shipment_id: SHP-10000020
            carrier: UPS
            status: delayed
            current_location: Louisville, KY
            estimated_delivery: '2025-10-03T17:00:00Z'
            last_update: '2025-09-30T14:20:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000020
            order_id: ORD-10000020
            sku: SKU-10000020
            product_name: KitchenAid Professional Stand Mixer
            quantity: 1
            base_price: 1245
            discount_amount: 0
            final_price: 1245
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000020
            order_id: ORD-10000020
            customer_id: CUS-10000010
            amount: 1245
            status: authorized
            payment_method: Visa ending in 7834
            transaction_date: '2025-09-15T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: SKU-10000020
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: SKU-10000020
            name: KitchenAid Professional Stand Mixer
            category: appliances
            brand: KitchenAid
            base_price: 1245
            weight_lbs: 28.5
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2024-03-12T09:30:00Z'
            customer_tier: standard
            lifetime_value: 2850.75
            total_orders: 6
            customer_score: 92
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.35
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000010
          - tool: get_order
            parameters:
              order_id: ORD-10000020
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'sarah.martinez@email.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '10' and created_at ge '2025-09-23T00:00:00Z'
              $select: null
              $orderby: null
          - tool: zendesk_update_item
            parameters:
              id: '20'
              item:
                tags: null
                type: null
                due_at: null
                status: open
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
          - tool: get_shipment_tracking
            parameters:
              order_id: ORD-10000020
          - tool: create_refund
            parameters:
              amount: 124.5
              order_id: ORD-10000020
              customer_id: CUS-10000010
              refund_reason: late_delivery_compensation
          - tool: zendesk_update_item
            parameters:
              id: '20'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: normal
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST002_004(x: TestContext, judge: Judge):
    """!
    query: I've been waiting for my KitchenAid Stand Mixer Professional 600 (order ORD-10000020) for over a week past the delivery estimate. Tracking says it's delayed and it's been 9 days since it was supposed to arrive. Can I get any compensation for this inconvenience?
    user_context: |-
      Rules :

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      You are Sarah Martinez. You are looking for compensation for a delayed delivery. If asked, your email is [sarah.martinez@email.com](mailto:sarah.martinez@email.com) and your phone number is +1-555-0198.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-03-15T10:00:00Z'
            updated_at: '2024-03-15T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000020
            customer_id: CUS-10000010
            order_date: '2025-09-10T14:30:00Z'
            status: shipped
            subtotal_amount: 895.5
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 895.5
            shipping_address_line1: 456 Maple Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000020
            order_id: ORD-10000020
            carrier: FedEx
            tracking_number: TRK-100000000020
            ship_date: '2025-09-12T09:00:00Z'
            estimated_delivery_date: '2025-09-22T17:00:00Z'
            actual_delivery_date: null
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000020
            shipment_id: SHP-10000020
            carrier: FedEx
            status: delayed
            current_location: Memphis, TN Distribution Center
            estimated_delivery: '2025-10-05T17:00:00Z'
            last_update: '2025-09-30T08:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000020
            order_id: ORD-10000020
            sku: SKU-10000020
            product_name: KitchenAid Stand Mixer Professional 600
            quantity: 1
            base_price: 895.5
            discount_amount: 0
            final_price: 895.5
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000020
            order_id: ORD-10000020
            customer_id: CUS-10000010
            amount: 895.5
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2025-09-10T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: SKU-10000020
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: SKU-10000020
            name: KitchenAid Stand Mixer Professional 600
            category: appliances
            brand: KitchenAid
            base_price: 895.5
            weight_lbs: 28.5
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000010
            customer_id: CUS-10000010
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 1250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2024-03-15T10:00:00Z'
            customer_tier: plus_member
            lifetime_value: 2150.75
            total_orders: 6
            customer_score: 48
            behavioral_segment: opportunist
            acquisition_source: email_marketing
            discount_usage_rate: 0.78
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Delayed shipment compensation request for order ORD-10000020
                priority: high
                assignee_id: '2'
                description: Customer reports KitchenAid Stand Mixer Professional 600 (order ORD-10000020) is 9 days past estimated delivery. Tracking status is 'delayed'. Customer requests compensation for inconvenience.
                requester_id: '10'
                organization_id: null
              table: tickets
          - tool: create_refund
            parameters:
              amount: 44.78
              order_id: ORD-10000020
              customer_id: CUS-10000010
              refund_reason: late_delivery_compensation
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST002_006(x: TestContext, judge: Judge):
    """!
    query: Hi, I ordered a Samsung TV and it was supposed to arrive 6 days ago. Can you please investigate what the issue is?
    user_context: "Rules:\n\n- Only use data provided in the scenario (name, email address, Order ID, etc.). You do not invent any data, names, IDs, policies, or details not present in the provided context.\n- Remain polite, clear, and patient throughout the conversation. \n- If the Agent requests the same information again, repeat your request and information above as needed.\n- Do not change the goal or switch topics."
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '20001'
            name: Sarah Martinez
            email: sarah.martinez@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0201
            verified: true
            active: true
            created_at: '2022-08-15T10:30:00Z'
            updated_at: '2025-09-30T12:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-50000008
            customer_id: CUS-20000001
            order_date: '2025-09-17T14:30:00Z'
            status: shipped
            subtotal_amount: 2499.99
            discount_amount: 159.99
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 2340
            shipping_address_line1: 456 Luxury Lane
            shipping_address_city: Beverly Hills
            shipping_address_state: CA
            shipping_address_zip: '90210'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-90000127
            order_id: ORD-50000008
            carrier: FedEx
            tracking_number: TRK-700000000033
            ship_date: '2025-09-18T09:15:00Z'
            estimated_delivery_date: '2025-09-25T17:00:00Z'
            actual_delivery_date: null
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-700000000033
            shipment_id: SHP-90000127
            carrier: FedEx
            status: delayed
            current_location: Phoenix, AZ Distribution Center
            estimated_delivery: '2025-10-03T17:00:00Z'
            last_update: '2025-09-30T08:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-387000032
            order_id: ORD-50000008
            sku: SKU-60000061
            product_name: Samsung 85-inch Neo QLED 8K Smart TV
            quantity: 1
            base_price: 2499.99
            discount_amount: 159.99
            final_price: 2340
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-24000566
            order_id: ORD-50000008
            customer_id: CUS-20000001
            amount: 2340
            status: authorized
            payment_method: Amex ending in 1009
            transaction_date: '2025-09-17T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-40000025
            order_id: ORD-50000008
            sku: SKU-60000061
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-09-17T00:00:00Z'
            end_date: '2026-09-17T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for electronics
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: SKU-60000061
            available_quantity: 3
            reserved_quantity: 1
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: SKU-60000061
            name: Samsung 85-inch Neo QLED 8K Smart TV
            category: audio_video
            brand: Samsung
            base_price: 2499.99
            weight_lbs: 95.2
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: sarah.martinez@example.com
            name: Sarah Martinez
            phone: +1-555-0201
            registration_date: '2022-08-15T10:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 18
            customer_score: 88
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: sarah.martinez@example.com
              customer_id: null
          - tool: get_order
            parameters:
              order_id: ORD-50000008
          - tool: get_shipment_tracking
            parameters:
              order_id: ORD-50000008
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'sarah.martinez@example.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Delayed shipment - VIP customer inquiry
                priority: urgent
                assignee_id: '2'
                description: Customer reports order ORD-20000001 was due 6 days ago, tracking shows carrier delay. Customer requests expedited delivery or compensation.
                requester_id: '20001'
                organization_id: null
              $skip: null
              table: tickets
              $filter: status eq 'open' and requesterid eq '20001'
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Delayed shipment - VIP customer
                priority: urgent
                assignee_id: '2'
                description: VIP customer enquired about shipment for ORD-50000008, overdue by 6 days due to carrier delay.
                requester_id: '20001'
                organization_id: null
              table: tickets
          - tool: create_refund
            parameters:
              amount: 234
              order_id: ORD-50000008
              customer_id: CUS-20000001
              refund_reason: late_delivery_compensation
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: Processed partial refund of 10% = $234 for VIP customer, as compensation for delayed shipment of order ORD-50000008.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST003_003(x: TestContext, judge: Judge):
    """!
    query: Hi, I'm Sarah Martine. I'm following up on my order ORD-20000001. It was supposed to be delivered on September 21st, but UPS tracking still shows it's in exception status due to access problems. It's been 19 days since I ordered and 10 days past the delivery estimate. I already opened a ticket about this 8 days ago, but nothing has changed. What is being done to resolve this?
    user_context: |2+


      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: null
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2023-05-15T14:30:00Z'
            updated_at: '2025-09-23T10:15:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '6'
            subject: Order delivery exception - access problems
            description: Customer reporting that UPS tracking shows exception status due to access problems at delivery location. Order ORD-20000001 was supposed to be delivered on 2025-09-21 but has been stuck in exception status since then.
            status: open
            priority: high
            type: incident
            requester_id: '6'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-23T10:15:00Z'
            updated_at: '2025-09-23T10:15:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-09-12T15:45:00Z'
            status: shipped
            subtotal_amount: 329.98
            discount_amount: 0
            points_used: 1350
            points_value: 67.5
            shipping_cost: 0
            total_amount: 262.48
            shipping_address_line1: 4567 Maple Drive
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78704'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: UPS
            tracking_number: TRK-200000000001
            ship_date: '2025-09-14T09:30:00Z'
            estimated_delivery_date: '2025-09-21T17:00:00Z'
            actual_delivery_date: null
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: UPS
            status: exception
            current_location: Austin, TX Distribution Center
            estimated_delivery: '2025-09-21T17:00:00Z'
            last_update: '2025-09-22T14:20:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: SKU-20000001
            product_name: Ninja Foodi 8-Quart Pressure Cooker
            quantity: 1
            base_price: 199.99
            discount_amount: 0
            final_price: 199.99
          - id: LIN-20000002
            order_id: ORD-20000001
            sku: SKU-20000002
            product_name: Instant Vortex Plus 6-Quart Air Fryer
            quantity: 1
            base_price: 129.99
            discount_amount: 0
            final_price: 129.99
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 262.48
            status: authorized
            payment_method: Visa ending in 7834
            transaction_date: '2025-09-12T15:45:15Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: SKU-20000001
            available_quantity: 8
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          - sku: SKU-20000002
            available_quantity: 12
            reserved_quantity: 1
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: SKU-20000001
            name: Ninja Foodi 8-Quart Pressure Cooker
            category: appliances
            brand: Ninja
            base_price: 199.99
            weight_lbs: 22.5
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          - sku: SKU-20000002
            name: Instant Vortex Plus 6-Quart Air Fryer
            category: appliances
            brand: Instant
            base_price: 129.99
            weight_lbs: 12.8
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-20000001
            customer_id: CUS-20000001
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 1850
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2023-05-15T14:30:00Z'
            customer_tier: plus_member
            lifetime_value: 2150.75
            total_orders: 12
            customer_score: 81
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.35
        golden_test_case:
          tool_interactions:
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: high
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST003_004(x: TestContext, judge: Judge):
    """!
    query: |+
      Hi, my order ORD-2025-0011 for the KitchenAid Stand Mixer Professional 600 was placed 22 days ago and shipped via FedEx, but the tracking (TRK-20250011) has shown 'exception' for a long time due to failed delivery attempts. The estimated delivery date was 13 days ago and I still haven't received it. Can you tell me what's going on and if I can get any compensation for this delay?

    user_context: |-
      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '20250011'
            name: Alex Miller
            email: alex.miller@example.com
            role: end-user
            organization_id: null
            phone: +1-615-555-0187
            verified: true
            active: true
            created_at: '2024-08-15T14:30:00Z'
            updated_at: '2024-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-2025-0011
            customer_id: CUS-20250011
            order_date: '2025-09-09T16:45:00Z'
            status: shipped
            subtotal_amount: 1150
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1150
            shipping_address_line1: 2847 Music Valley Dr
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20250011
            order_id: ORD-2025-0011
            carrier: FedEx
            tracking_number: TRK-20250011
            ship_date: '2025-09-10T09:30:00Z'
            estimated_delivery_date: '2025-09-18T17:00:00Z'
            actual_delivery_date: null
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-20250011
            shipment_id: SHP-20250011
            carrier: FedEx
            status: exception
            current_location: Nashville TN Distribution Center
            estimated_delivery: '2025-09-18T17:00:00Z'
            last_update: '2025-09-24T14:20:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20250011
            order_id: ORD-2025-0011
            sku: SKU-20250011
            product_name: KitchenAid Stand Mixer Professional 600
            quantity: 1
            base_price: 1150
            discount_amount: 0
            final_price: 1150
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20250011
            order_id: ORD-2025-0011
            customer_id: CUS-20250011
            amount: 1150
            status: authorized
            payment_method: Visa ending in 7892
            transaction_date: '2025-09-09T16:45:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20250011
            order_id: ORD-2025-0011
            sku: SKU-20250011
            customer_id: CUS-20250011
            warranty_type: manufacturer
            start_date: '2025-09-09T00:00:00Z'
            end_date: '2028-09-09T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for small appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: SKU-20250011
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Nashville-B08
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: SKU-20250011
            name: KitchenAid Stand Mixer Professional 600
            category: appliances
            brand: KitchenAid
            base_price: 1150
            weight_lbs: 28.5
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20250011
            email: alex.miller@example.com
            name: Alex Miller
            phone: +1-615-555-0187
            registration_date: '2024-08-15T14:30:00Z'
            customer_tier: standard
            lifetime_value: 2850.75
            total_orders: 3
            customer_score: 95
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.25
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: alex.miller@example.com
              customer_id: null
          - tool: get_order
            parameters:
              order_id: ORD-2025-0011
          - tool: get_shipment_tracking
            parameters:
              order_id: ORD-2025-0011
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'alex.miller@example.com'
              $select: null
              $orderby: null
              is_defective: false
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: null
                due_at: null
                status: open
                subject: Delivery delay / tracking exception for ORD-2025-0011
                priority: normal
                assignee_id: '2'
                description: Customer reports the shipment has been in exception status for 13 days past estimated delivery.
                requester_id: '20250011'
                organization_id: null
              table: tickets
          - tool: create_refund
            parameters:
              amount: 115
              order_id: ORD-2025-0011
              customer_id: CUS-20250011
              refund_reason: late_delivery_compensation
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: incident
                due_at: null
                status: solved
                subject: Delivery delay compensation issued
                priority: normal
                assignee_id: '2'
                description: Issued $115 late delivery compensation refund. Customer notified.
                requester_id: '20250011'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST003_006(x: TestContext, judge: Judge):
    """!
    query: My order was supposed to arrive over two weeks ago, but tracking still shows an exception status and I haven't received it. This is unacceptable, either give me a full refund or a significant discount for the delay.
    user_context: |-
      You are Sarah Martinez, a Plus member of TechHome Direct with email address [sarah.martinez@email.com](mailto:sarah.martinez@email.com)

      Your intent is to follow up on a delayed order (ORD-10000020) that remains undelivered despite being told earlier that the carrier corrected the address issue. The estimated delivery date was 15 days ago (making it 15 days late). You contacted their customer service 6 days ago, where you were told to wait for the carrier’s resolution. You are now following up to demand a refund or discount for the extended delay.

      —------

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      —------
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2023-08-15T14:30:00Z'
            updated_at: '2025-09-25T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '20'
            subject: Order delivery delay - tracking shows exception
            description: Customer contacted about delayed order ORD-10000020. Package showing exception status due to incorrect address label. Advised customer to wait for carrier resolution as address has been corrected.
            status: solved
            priority: high
            type: incident
            requester_id: '10'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-25T10:00:00Z'
            updated_at: '2025-09-25T16:30:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 23118465221930
            ticket_id: 20
            author_id: 10
            body: My order ORD-10000020 is showing exception status and was supposed to be delivered over 2 weeks ago. What's happening with my package?
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">My order ORD-10000020 is showing exception status and was supposed to be delivered over 2 weeks ago. What's happening with my package?</p></div>
            public: true
            created_at: '2025-09-25T10:00:00Z'
            ItemInternalId: 630d7175-2bb9-41d9-9131-d5f2e57af9f0
            key: '23118465221930'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000020
            customer_id: CUS-10000010
            order_date: '2025-09-06T15:30:00Z'
            status: shipped
            subtotal_amount: 745
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 745
            shipping_address_line1: 456 Elm Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000020
            order_id: ORD-10000020
            carrier: UPS
            tracking_number: TRK-100000000020
            ship_date: '2025-09-08T09:15:00Z'
            estimated_delivery_date: '2025-09-16T17:00:00Z'
            actual_delivery_date: null
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000020
            shipment_id: SHP-10000020
            carrier: UPS
            status: exception
            current_location: Nashville Distribution Center
            estimated_delivery: '2025-10-02T17:00:00Z'
            last_update: '2025-09-30T14:20:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000020
            order_id: ORD-10000020
            sku: SKU-10000020
            product_name: KitchenAid Stand Mixer Professional 600
            quantity: 1
            base_price: 745
            discount_amount: 0
            final_price: 745
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000020
            order_id: ORD-10000020
            customer_id: CUS-10000010
            amount: 745
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-09-06T15:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: SKU-10000020
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: SKU-10000020
            name: KitchenAid Stand Mixer Professional 600
            category: appliances
            brand: KitchenAid
            base_price: 745
            weight_lbs: 28.5
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000010
            customer_id: CUS-10000010
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 1250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2023-08-15T14:30:00Z'
            customer_tier: plus_member
            lifetime_value: 2150.75
            total_orders: 12
            customer_score: 28
            behavioral_segment: bonus_hunter
            acquisition_source: promotional_email
            discount_usage_rate: 0.92
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: sarah.martinez@email.com
              customer_id: null
          - tool: get_order
            parameters:
              order_id: ORD-10000020
          - tool: get_shipment_tracking
            parameters:
              order_id: ORD-10000020
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'sarah.martinez@email.com'
              $select: null
              $orderby: created_at desc
          - tool: zendesk_get_items
            parameters:
              id: '10'
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '10'
              $select: null
              $orderby: null
          - tool: zendesk_update_item
            parameters:
              id: '20'
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Order delivery delay - tracking shows exception
                priority: high
                assignee_id: '2'
                description: Customer contacted again about delayed order ORD-10000020. Package still showing exception status due to incorrect address label. Carrier has corrected the address but delivery is delayed 15 days past estimate. Customer demanding refund or discount. Advised that carrier is still working to resolve delivery and we will continue to monitor.
                requester_id: '10'
                organization_id: null
              table: tickets
          - tool: zendesk_update_item
            parameters:
              id: '20'
              item:
                tags: null
                type: incident
                due_at: null
                status: hold
                subject: Order delivery delay - Awaiting carrier shipment
                priority: high
                assignee_id: '2'
                description: Customer contacted again about the delayed order, Initiated Carrier investigation
                requester_id: '10'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST004_001(x: TestContext, judge: Judge):
    """!
    query: Hi, I need help regarding my recent camera order. The tracking says it was delivered, but I never received the package. I’ve already checked with my neighbors and around my property, but the package is nowhere to be found. Could you please look into this?
    user_context: "Rules: \nDo not invent or provide any data not present in the provided context.\nDo not change your goal or switch topics.\nIf asked for the same info, provide it again.\nRemain focused, clear, and patient.\n\nYou are Jonathan Pierce, a VIP customer of TechHome Direct. You are contacting support because the tracking for your recent camera order says it was delivered, but you did not receive the package.\n\n1. If the agent asks for your email, give exactly: [jonathan.pierce@email.com](mailto:jonathan.pierce@email.com)\n2. If the agent asks for your shipping address, provide: “1428 Willow Creek Drive, Austin, TX 73301”\n3. If the agent asks about what items you ordered, say: “ORD-90005551”\n\n"
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '90001'
            name: Jonathan Pierce
            email: jonathan.pierce@email.com
            role: end-user
            organization_id: '1'
            phone: +1-512-555-0187
            verified: true
            active: true
            created_at: '2024-03-15T14:30:00Z'
            updated_at: '2024-03-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-90005551
            customer_id: CUS-90000001
            order_date: '2025-09-23T10:00:00Z'
            status: delivered
            subtotal_amount: 899
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 899
            shipping_address_line1: 1428 Willow Creek Drive
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '73301'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-90005551
            order_id: ORD-90005551
            carrier: UPS
            tracking_number: TRK-55009
            ship_date: '2025-09-24T09:15:00Z'
            estimated_delivery_date: '2025-09-29T14:00:00Z'
            actual_delivery_date: '2025-09-29T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-55009
            shipment_id: SHP-90005551
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-29T14:00:00Z'
            last_update: '2025-09-29T15:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-90010001
            order_id: ORD-90005551
            sku: CAM-9845
            product_name: High-End Mirrorless Camera
            quantity: 1
            base_price: 899
            discount_amount: 0
            final_price: 899
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-90005551
            order_id: ORD-90005551
            customer_id: CUS-90000001
            amount: 899
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2025-09-23T10:05:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: CAM-9845
            available_quantity: 12
            reserved_quantity: 1
            warehouse_location: Austin-B14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: CAM-9845
            name: High-End Mirrorless Camera
            category: electronics
            brand: Canon
            base_price: 899
            weight_lbs: 4
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-90000001
            email: jonathan.pierce@email.com
            name: Jonathan Pierce
            phone: +1-512-555-0187
            registration_date: '2024-03-15T14:20:00Z'
            customer_tier: vip
            lifetime_value: 4250.75
            total_orders: 5
            customer_score: 87
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.25
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Customer reports missing delivered package
                priority: urgent
                assignee_id: '2'
                description: Customer states the carrier marked the order as delivered but they did not receive the package.
                requester_id: '90001'
                organization_id: null
              table: tickets
          - tool: create_replacement_order
            parameters:
              sku: CAM-9845
              quantity: 1
              customer_id: CUS-90000001
              shipping_speed: expedited
              original_order_id: ORD-90005551
              shipping_address_zip: '73301'
              shipping_address_city: Austin
              shipping_address_line1: 1428 Willow Creek Drive
              shipping_address_state: TX
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: Replacement order has been created for missing delivered package.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST004_003(x: TestContext, judge: Judge):
    """!
    query: Hi, I ordered an Axiom Smart Watch Pro (SKU WATCH-7723) 10 days ago under order ORD-10000010. The tracking shows it was delivered 3 days ago, but I never received it. I already checked with neighbors and around my building—nothing was found. I need an immediate replacement or a refund because this is unacceptable.
    user_context: "Rules:\n\nDo not invent or provide any data not present in the provided context.\n\nDo not change your goal or switch topics. \n\nIf asked for the same info, provide it again.\n\nRemain focused, clear, and patient."
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10'
            name: Victoria Chen
            email: victoria.chen@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0150
            verified: true
            active: true
            created_at: '2022-03-15T09:30:00Z'
            updated_at: '2022-03-15T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '10'
            subject: Product specifications inquiry
            description: Customer asking about smartwatch compatibility with different phone models
            status: solved
            priority: low
            type: question
            requester_id: '10'
            assignee_id: '2'
            organization_id: '1'
            tags:
            - product
            - inquiry
            created_at: '2025-09-24T10:00:00Z'
            updated_at: '2025-09-25T14:30:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000010
            customer_id: CUS-10000010
            order_date: '2025-09-21T15:30:00Z'
            status: delivered
            subtotal_amount: 349
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 349
            shipping_address_line1: 789 Executive Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000010
            order_id: ORD-10000010
            carrier: UPS
            tracking_number: TRK-100000000010
            ship_date: '2025-09-22T09:15:00Z'
            estimated_delivery_date: '2025-09-28T17:00:00Z'
            actual_delivery_date: '2025-09-28T14:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000010
            shipment_id: SHP-10000010
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-28T17:00:00Z'
            last_update: '2025-09-28T14:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000010
            order_id: ORD-10000010
            sku: WATCH-7723
            product_name: Samsung Galaxy Watch 6 Classic 47mm
            quantity: 1
            base_price: 349
            discount_amount: 0
            final_price: 349
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000010
            order_id: ORD-10000010
            customer_id: CUS-10000010
            amount: 349
            status: authorized
            payment_method: Amex ending in 9876
            transaction_date: '2025-09-21T15:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: WATCH-7723
            available_quantity: 25
            reserved_quantity: 5
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: WATCH-7723
            name: Samsung Galaxy Watch 6 Classic 47mm
            category: wearables
            brand: Samsung
            base_price: 349
            weight_lbs: 0.8
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: victoria.chen@example.com
            name: Victoria Chen
            phone: +1-555-0150
            registration_date: '2022-03-15T09:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 28
            customer_score: 31
            behavioral_segment: bonus_hunter
            acquisition_source: referral
            discount_usage_rate: 0.95
        golden_test_case:
          tool_interactions:
          - tool: get_order
            parameters:
              order_id: ORD-10000010
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000010
          - tool: get_shipment_tracking
            parameters:
              order_id: ORD-10000010
          - tool: check_inventory
            parameters:
              sku: WATCH-7723
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Package marked delivered but not received - replacement requested
                priority: urgent
                assignee_id: '2'
                description: Customer reports order ORD-10000010 (SKU WATCH-7723) marked delivered 3 days ago but not received. Customer has checked with neighbors and all possible locations. Courtesy replacement to be issued per VIP policy.
                requester_id: '10'
                organization_id: null
              table: tickets
          - tool: create_replacement_order
            parameters:
              sku: WATCH-7723
              quantity: 1
              customer_id: CUS-10000010
              shipping_speed: expedited
              original_order_id: ORD-10000010
              shipping_address_zip: '37203'
              shipping_address_city: Nashville
              shipping_address_line1: 789 Executive Drive
              shipping_address_state: TN
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST004_004(x: TestContext, judge: Judge):
    """!
    query: Hi, I never received my Samsung Galaxy Tab S9 (order ORD-10000007) even though tracking says it was delivered to 456 Elm Street, Nashville 2 days ago. I've checked with neighbors and everywhere at home. What can you do to help me?
    user_context: |-
      Rules:
      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Customer Name
            email: customer@example.com
            role: end-user
            organization_id: null
            phone: +1-555-0199
            verified: true
            active: true
            created_at: '2025-10-01T13:00:00Z'
            updated_at: '2025-10-01T13:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000007
            customer_id: CUS-10000006
            order_date: '2025-09-25T14:30:00Z'
            status: delivered
            subtotal_amount: 549
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 549
            shipping_address_line1: 456 Elm Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000007
            order_id: ORD-10000007
            carrier: UPS
            tracking_number: TRK-100000000007
            ship_date: '2025-09-26T09:15:00Z'
            estimated_delivery_date: '2025-09-29T17:00:00Z'
            actual_delivery_date: '2025-09-29T15:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000007
            shipment_id: SHP-10000007
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-29T17:00:00Z'
            last_update: '2025-09-29T15:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000007
            order_id: ORD-10000007
            sku: TAB-5512
            product_name: Samsung Galaxy Tab S9 11-inch 128GB
            quantity: 1
            base_price: 549
            discount_amount: 0
            final_price: 549
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000007
            order_id: ORD-10000007
            customer_id: CUS-10000006
            amount: 549
            status: authorized
            payment_method: Visa ending in 2468
            transaction_date: '2025-09-25T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: TAB-5512
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: TAB-5512
            name: Samsung Galaxy Tab S9 11-inch 128GB
            category: computing
            brand: Samsung
            base_price: 549
            weight_lbs: 1.1
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000006
            email: customer@example.com
            name: Customer Name
            phone: +1-555-0199
            registration_date: '2024-08-15T10:30:00Z'
            customer_tier: standard
            lifetime_value: 1850.75
            total_orders: 4
            customer_score: 91
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.35
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Package marked delivered but not received - Samsung Galaxy Tab
                priority: urgent
                assignee_id: '2'
                description: Customer reports package was marked as delivered 2 days ago but never received. Has checked with neighbors, household members, and all alternate locations. Order ORD-10000007 for Samsung Galaxy Tab S9 valued at $549.00. Courtesy replacement order created.
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: check_inventory
            parameters:
              sku: TAB-5512
          - tool: create_replacement_order
            parameters:
              sku: TAB-5512
              quantity: 1
              customer_id: CUS-10000006
              shipping_speed: standard
              original_order_id: ORD-10000007
              shipping_address_zip: '37203'
              shipping_address_city: Nashville
              shipping_address_line1: 456 Elm Street
              shipping_address_state: TN
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST004_005(x: TestContext, judge: Judge):
    """!
    query: Hi, I’m following up on my missing package for order ORD-10000015. UPS shows it was delivered on September 27th, but I still have not received anything. I already checked with my neighbors and everyone at home. I really need this taken care of now because I have nothing to work with. What can we do to get this resolved today?
    user_context: |-
      **Your Goal:** Your goal is to resolve the missing package issue and get a replacement sent to you immediately.

      **Rules for Behavior:**

      - **Do not invent or provide any data not present in the provided context.**
      - **Do not change your goal or switch topics.**
      - **If asked for the same info, provide it again.**
      - **Remain focused, clear, and patient.**
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Michael Chen
            email: michael.chen@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0156
            verified: true
            active: true
            created_at: '2024-02-10T14:30:00Z'
            updated_at: '2024-02-10T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '15'
            subject: Package marked delivered but not received - Gaming Headset
            description: Customer reports that order ORD-10000015 (SteelSeries Arctis 7P Wireless Gaming Headset) was marked as delivered by UPS on 2025-09-27 but they have not received the package. Customer has checked with neighbors and household members. Tracking shows delivery confirmation to customer address.
            status: open
            priority: urgent
            type: incident
            requester_id: '15'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-28T14:20:00Z'
            updated_at: '2025-09-28T14:20:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-09-22T10:15:00Z'
            status: delivered
            subtotal_amount: 159.99
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 159.99
            shipping_address_line1: 789 Pine Street
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: UPS
            tracking_number: TRK-100000000015
            ship_date: '2025-09-24T09:30:00Z'
            estimated_delivery_date: '2025-09-27T17:00:00Z'
            actual_delivery_date: '2025-09-27T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000015
            shipment_id: SHP-10000015
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-27T17:00:00Z'
            last_update: '2025-09-27T15:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: GAM-8834
            product_name: SteelSeries Arctis 7P Wireless Gaming Headset
            quantity: 1
            base_price: 159.99
            discount_amount: 0
            final_price: 159.99
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            amount: 159.99
            status: authorized
            payment_method: Visa ending in 2468
            transaction_date: '2025-09-22T10:15:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: GAM-8834
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Dallas-G15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: GAM-8834
            name: SteelSeries Arctis 7P Wireless Gaming Headset
            category: gaming
            brand: SteelSeries
            base_price: 159.99
            weight_lbs: 1.2
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: michael.chen@example.com
            name: Michael Chen
            phone: +1-555-0156
            registration_date: '2024-02-10T14:30:00Z'
            customer_tier: standard
            lifetime_value: 320.75
            total_orders: 2
            customer_score: 76
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000015
          - tool: get_order
            parameters:
              order_id: ORD-10000015
          - tool: get_shipment_tracking
            parameters:
              order_id: ORD-10000015
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '15'
              $select: null
              $orderby: null
          - tool: check_inventory
            parameters:
              sku: GAM-8834
          - tool: create_replacement_order
            parameters:
              sku: GAM-8834
              quantity: 1
              customer_id: CUS-10000015
              shipping_speed: standard
              original_order_id: ORD-10000015
              shipping_address_zip: '78701'
              shipping_address_city: Austin
              shipping_address_line1: 789 Pine Street
              shipping_address_state: TX
          - tool: zendesk_update_item
            parameters:
              id: '15'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: urgent
                assignee_id: null
                description: Replacement order for missing package (SteelSeries Arctis 7P Wireless Gaming Headset) has been issued and will ship to your original address. Issue fully resolved.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST004_007(x: TestContext, judge: Judge):
    """!
    query: Hi, my order ORD-10000015 shows as delivered by UPS three days ago, but I never received it. I've already checked with my neighbors and everyone in my household. What can you do about this?
    user_context: "You are Sarah Martinez with email [sarah.martinez@email.com](mailto:sarah.martinez@email.com)\n\nYour address line 1 is 742 Oak Street\n\naddress city is Nashville \n\nAddress state is: TN\n\nAddress Zip is : 37203\n\nRules:\n\nDo not invent or provide any data not present in the provided context.\n\nDo not change your goal or switch topics.\n\nIf asked for the same info, provide it again.\n\nRemain focused, clear, and patient."
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-08-15T14:20:00Z'
            updated_at: '2024-08-15T14:20:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000010
            order_date: '2025-09-24T16:45:00Z'
            status: delivered
            subtotal_amount: 39.99
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 8.99
            total_amount: 48.98
            shipping_address_line1: 742 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: UPS
            tracking_number: TRK-100000000015
            ship_date: '2025-09-27T09:30:00Z'
            estimated_delivery_date: '2025-09-28T17:00:00Z'
            actual_delivery_date: '2025-09-28T14:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000015
            shipment_id: SHP-10000015
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-28T17:00:00Z'
            last_update: '2025-09-28T14:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: ACC-4432
            product_name: Premium Silicone Phone Case
            quantity: 1
            base_price: 39.99
            discount_amount: 0
            final_price: 39.99
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000010
            amount: 48.98
            status: authorized
            payment_method: Visa ending in 7834
            transaction_date: '2025-09-24T16:45:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: ACC-4432
            available_quantity: 25
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: ACC-4432
            name: Premium Silicone Phone Case
            category: electronics
            brand: TechGuard
            base_price: 39.99
            weight_lbs: 0.2
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2024-08-15T14:20:00Z'
            customer_tier: standard
            lifetime_value: 89.99
            total_orders: 2
            customer_score: 54
            behavioral_segment: opportunist
            acquisition_source: social_media
            discount_usage_rate: 0.75
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Delivered but not received - ORD-10000015
                priority: urgent
                assignee_id: '2'
                description: Customer reports package marked delivered by UPS on 28 Sep 2025, but not received. Carrier investigation to be opened.
                requester_id: '10'
                organization_id: null
              table: tickets
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: Carrier investigation with UPS initiated on 1 Oct 2025. ETA 3–5 business days. Customer advised to monitor for package and provide any extra delivery details.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST004_008(x: TestContext, judge: Judge):
    """!
    query: Hi, I need an update on a ticket I opened. Can you check the status for me?
    user_context: |-
      Rules:

      If the agent asks for the order ID, it's ORD-20000001.

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '20001'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-03-15T09:30:00Z'
            updated_at: '2024-03-15T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '20001'
            subject: Package not received - Order ORD-20000001
            description: Customer reports fitness tracker was marked as delivered on 9/25 but package was not received. Customer has checked with neighbors and household members.
            status: open
            priority: urgent
            type: incident
            requester_id: '20001'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-27T16:45:00Z'
            updated_at: '2025-09-27T16:45:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-09-19T14:30:00Z'
            status: delivered
            subtotal_amount: 129
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 129
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Portland
            shipping_address_state: OR
            shipping_address_zip: '97201'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: UPS
            tracking_number: TRK-200000000001
            ship_date: '2025-09-20T10:00:00Z'
            estimated_delivery_date: '2025-09-25T17:00:00Z'
            actual_delivery_date: '2025-09-25T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-25T17:00:00Z'
            last_update: '2025-09-25T15:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: WEAR-3387
            product_name: FitTrack Pro Fitness Tracker
            quantity: 1
            base_price: 129
            discount_amount: 0
            final_price: 129
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 129
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2025-09-19T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: WEAR-3387
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Portland-W15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: WEAR-3387
            name: FitTrack Pro Fitness Tracker
            category: wearables
            brand: FitTrack
            base_price: 129
            weight_lbs: 0.3
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-20000001
            customer_id: CUS-20000001
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 2500
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2024-03-15T09:30:00Z'
            customer_tier: plus_member
            lifetime_value: 890.5
            total_orders: 6
            customer_score: 47
            behavioral_segment: opportunist
            acquisition_source: social_media
            discount_usage_rate: 0.75
        golden_test_case:
          tool_interactions:
          - tool: zendesk_update_item
            parameters:
              id: '20001'
              item:
                tags: null
                type: incident
                due_at: null
                status: hold
                subject: null
                priority: urgent
                assignee_id: '2'
                description: 'Customer follow-up on missing FitTrack Pro Fitness Tracker from order ORD-20000001. Package marked delivered 2025-09-25 but customer reports non-receipt after checking with neighbors. Carrier investigation initiated with UPS. Expected resolution: 3-5 business days.'
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST004_009(x: TestContext, judge: Judge):
    """!
    query: I never received my wireless charger (order ORD-77110001), even though tracking says it was delivered 8 days ago to 456 Oak Street, Nashville. I already checked with my neighbors and still can't find it. I want a replacement or a full refund right now.
    user_context: |-
      —------

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '87654'
            name: Alex Turner
            email: alex.turner@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0876
            verified: true
            active: true
            created_at: '2024-08-15T14:30:00Z'
            updated_at: '2024-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '445566'
            requester_id: '87654'
            type: incident
            subject: Shipping status question for previous order ORD-66009900
            description: Customer asked about shipping status and delivery details for order ORD-66009900.
            status: solved
            priority: normal
            created_at: '2025-09-24T10:00:00Z'
            updated_at: '2025-09-29T12:00:00Z'
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-77110001
            customer_id: CUS-00001876
            order_date: '2025-09-17T10:00:00Z'
            status: delivered
            subtotal_amount: 49.99
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 49.99
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          - id: ORD-66009900
            customer_id: CUS-00001876
            order_date: '2025-08-20T14:15:00Z'
            status: delivered
            subtotal_amount: 79.99
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 79.99
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-77110001
            order_id: ORD-77110001
            carrier: UPS
            tracking_number: 1Z77110001TEST
            ship_date: '2025-09-18T09:30:00Z'
            estimated_delivery_date: '2025-09-23T17:00:00Z'
            actual_delivery_date: '2025-09-23T15:00:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: 1Z77110001TEST
            shipment_id: SHP-77110001
            carrier: UPS
            status: delivered
            current_location: 456 Oak Street, Nashville, TN 37203
            estimated_delivery: '2025-09-23T17:00:00Z'
            last_update: '2025-09-23T15:00:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: OI-77110001-1
            order_id: ORD-77110001
            sku: ACC-7756
            product_name: Wireless Charger
            quantity: 1
            base_price: 49.99
            discount_amount: 0
            final_price: 49.99
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-77110001
            order_id: ORD-77110001
            customer_id: CUS-00001876
            amount: 49.99
            status: authorized
            payment_method: Visa ending in 2468
            transaction_date: '2025-09-17T10:05:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: ACC-7756
            available_quantity: 25
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: ACC-7756
            name: Wireless Charger
            category: electronics
            brand: TechHome
            base_price: 49.99
            weight_lbs: 0.8
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-00001876
            email: alex.turner@example.com
            name: Alex Turner
            phone: +1-555-0876
            registration_date: '2024-08-15T14:30:00Z'
            customer_tier: standard
            lifetime_value: 149.97
            total_orders: 3
            customer_score: 18
            behavioral_segment: bonus_hunter
            acquisition_source: paid_search
            discount_usage_rate: 0.95
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Package marked delivered but not received - Wireless Charger
                priority: urgent
                assignee_id: '2'
                description: Order ORD-77110001 for Wireless Charger (ACC-7756) placed 14 days ago, marked delivered 8 days ago to correct address. Customer reports non-receipt, has checked with neighbors, and is requesting a replacement or refund.
                requester_id: '87654'
                organization_id: null
              table: tickets
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: subject eq 'Package marked delivered but not received - Wireless Charger' and requester_id eq '87654'
              $select: null
              $orderby: null
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: Carrier investigation for missing package on order ORD-77110001 is in progress. Awaiting carrier response before proceeding with replacement or refund.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST005_001(x: TestContext, judge: Judge):
    """!
    query: Hi, I never received my package for order ORD-55442001. The tracking says it was "returned to sender," but I don't understand why. What happened to my delivery?
    user_context: |-
      Rules:
      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.


      You are Jordan Ellis, a Standard Customer.

      If the agent specifically asks for the zip code, then provide: "62704"

      If the agent asks for your email, reply: "jordan.ellis@example.com"

      If the agent suggests the address might be incomplete, insist your address is correct
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '30004577'
            name: Jordan Ellis
            email: jordan.ellis@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0199
            verified: true
            active: true
            created_at: '2024-08-15T10:30:00Z'
            updated_at: '2024-08-15T10:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-55442001
            customer_id: CUS-30004577
            order_date: '2025-09-16T13:00:00Z'
            status: shipped
            subtotal_amount: 245.5
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 245.5
            shipping_address_line1: 4582 Maple Street, Apt 3B
            shipping_address_city: Springfield
            shipping_address_state: IL
            shipping_address_zip: '62704'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-55442001
            order_id: ORD-55442001
            carrier: UPS
            tracking_number: TRK-55442001
            ship_date: '2025-09-17T09:30:00Z'
            estimated_delivery_date: '2025-09-20T17:00:00Z'
            actual_delivery_date: null
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-55442001
            shipment_id: SHP-55442001
            carrier: UPS
            status: returned_to_sender
            current_location: UPS Facility - Springfield, IL
            estimated_delivery: '2025-09-20T17:00:00Z'
            last_update: '2025-10-01T11:00:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LI-99000100
            order_id: ORD-55442001
            sku: ELEC-9982
            product_name: Wireless Bluetooth Speaker
            quantity: 1
            base_price: 245.5
            discount_amount: 0
            final_price: 245.5
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-55442001
            order_id: ORD-55442001
            customer_id: CUS-30004577
            amount: 245.5
            status: authorized
            payment_method: Visa ending in 4242
            transaction_date: '2025-09-17T13:00:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: ELEC-9982
            available_quantity: 25
            reserved_quantity: 5
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: ELEC-9982
            name: Wireless Bluetooth Speaker
            category: audio_video
            brand: SoundTech
            base_price: 245.5
            weight_lbs: 4.2
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-30004577
            email: jordan.ellis@example.com
            name: Jordan Ellis
            phone: +1-555-0199
            registration_date: '2024-08-15T10:30:00Z'
            customer_tier: standard
            lifetime_value: 735.5
            total_orders: 3
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-30004577
          - tool: get_order
            parameters:
              order_id: ORD-55442001
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'jordan.ellis@example.com'
              $select: id,email,name
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Package returned to sender for order ORD-55442001
                priority: normal
                assignee_id: '2'
                description: Customer reports package not received. Tracking shows returned to sender due to undeliverable address. Address confirmed as correct.
                requester_id: '30004577'
                organization_id: null
              table: tickets
          - tool: reship_order
            parameters:
              order_id: ORD-55442001
              customer_fault: false
              corrected_address_zip: '62704'
              corrected_address_city: Springfield
              corrected_address_line1: 4582 Maple Street, Apt 3B
              corrected_address_state: IL
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: normal
                assignee_id: null
                description: Reshipment issued at no charge due to carrier undeliverable return. Address confirmed as correct. New shipment is on the way.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST005_005(x: TestContext, judge: Judge):
    """!
    query: |-
      Hi, my customer ID is CUS-10000015. I'm following up on my open ticket about order ORD-10000015. I just saw that my package with tracking number (TRK-100000000015
      ) is being returned to sender because of an incorrect address. I meant to have it shipped to 2401 East Boulevard, Los Angeles, CA 90001, but I accidentally selected 2401 West Boulevard during checkout. Can you please fix this immediately and make sure it gets delivered to the correct address?
    user_context: |+
      You are Victoria.

      Rules:

      Do NOT invent or provide data not present in the context or database.

      Do NOT change your goal or switch topics.

      Remain focused, clear, and patient.

      If asked for the same info, provide it again.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Victoria Martinez
            email: victoria.martinez@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0189
            verified: true
            active: true
            created_at: '2022-03-15T10:30:00Z'
            updated_at: '2022-03-15T10:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '15'
            subject: Order delayed - tracking shows no updates
            description: Customer inquiring about delayed shipment for order ORD-10000015. Package was supposed to arrive by September 20th but tracking hasn't updated in several days.
            status: open
            priority: urgent
            type: incident
            requester_id: '15'
            assignee_id: '2'
            organization_id: '1'
            created_at: '2025-09-24T16:30:00Z'
            updated_at: '2025-09-24T16:30:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 23118465221925
            ticket_id: 15
            author_id: 15
            body: Customer inquiring about delayed shipment for order ORD-10000015. Package was supposed to arrive by September 20th but tracking hasn't updated in several days.
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">Customer inquiring about delayed shipment for order ORD-10000015. Package was supposed to arrive by September 20th but tracking hasn't updated in several days.</p></div>
            public: true
            created_at: '2025-09-24T16:30:00Z'
            ItemInternalId: 925d7175-2bb9-41d9-9131-d5f2e57af9f9
            key: '23118465221925'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-09-11T14:30:00Z'
            status: shipped
            subtotal_amount: 3250
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 3250
            shipping_address_line1: 2401 West Boulevard
            shipping_address_city: Los Angeles
            shipping_address_state: CA
            shipping_address_zip: '90001'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: FedEx
            tracking_number: TRK-100000000015
            ship_date: '2025-09-13T09:15:00Z'
            estimated_delivery_date: '2025-09-20T17:00:00Z'
            actual_delivery_date: null
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000015
            shipment_id: SHP-10000015
            carrier: FedEx
            status: returned_to_sender
            current_location: Los Angeles Distribution Center
            estimated_delivery: '2025-09-20T17:00:00Z'
            last_update: '2025-09-30T11:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: SKU-10000015
            product_name: Sub-Zero 48-inch Built-in Side-by-Side Refrigerator
            quantity: 1
            base_price: 3250
            discount_amount: 0
            final_price: 3250
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            amount: 3250
            status: authorized
            payment_method: Amex ending in 1009
            transaction_date: '2025-09-11T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: SKU-10000015
            available_quantity: 3
            reserved_quantity: 1
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: SKU-10000015
            name: Sub-Zero 48-inch Built-in Side-by-Side Refrigerator
            category: appliances
            brand: Sub-Zero
            base_price: 3250
            weight_lbs: 425
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: false
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000015
            customer_id: CUS-10000015
            membership_type: vip
            start_date: '2023-08-15T00:00:00Z'
            end_date: '2026-08-15T23:59:59Z'
            status: active
            points_balance: 88
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: victoria.martinez@example.com
            name: Victoria Martinez
            phone: +1-555-0189
            registration_date: '2022-03-15T10:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 28
            customer_score: 95
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: reship_order
            parameters:
              order_id: ORD-10000015
              customer_fault: true
              corrected_address_zip: '90001'
              corrected_address_city: Los Angeles
              corrected_address_line1: 2401 East Boulevard
              corrected_address_state: CA
          - tool: charge_customer
            parameters:
              amount: 15
              order_id: ORD-10000015
              customer_id: CUS-10000015
              charge_reason: reship_fee
          - tool: zendesk_update_item
            parameters:
              id: '15'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: urgent
                assignee_id: null
                description: Reshipment initiated to correct address (2401 East Boulevard, Los Angeles, CA 90001) for order ORD-10000015. Customer charged reship fee due to address error.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_001(x: TestContext, judge: Judge):
    """!
    query: I bought a DSLR camera about a month ago and it was delivered. I've changed my mind and want to return it for a refund.
    user_context: "Rules:\n\nDo not invent or provide any data not present in the provided context.\n\nDo not change your goal or switch topics.\n\nIf asked for the same info, provide it again.\n\nRemain focused, clear, and patient.\n\n\n\nIf asked for additional information, you may provide:\n\n- Approximate purchase/delivery: ordered about 38 days ago; delivered about 35 days ago\n\n- Item details: DSLR camera, opened condition \n\n- Reason: changed mind, item not defective\n\n- Return preference: refund\n\n- Willing to use standard return label with shipping deducted\n\n- Identity/order: Name Jane Roe, email [customer2@example.com](mailto:customer2@example.com), order ORD-60010"
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10002'
            name: Jane Roe
            email: customer2@example.com
            role: end-user
            organization_id: null
            phone: +1-555-0987
            verified: true
            active: true
            created_at: '2025-08-24T10:00:00Z'
            updated_at: '2025-08-24T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-60010
            customer_id: CUS-20010
            order_date: '2025-08-24T10:30:00Z'
            status: delivered
            subtotal_amount: 799
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 799
            shipping_address_line1: 456 Oak St
            shipping_address_city: Springfield
            shipping_address_state: IL
            shipping_address_zip: '62704'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SH-60010-001
            order_id: ORD-60010
            carrier: UPS
            tracking_number: TRK-600100001
            ship_date: '2025-08-25T09:15:00Z'
            estimated_delivery_date: '2025-08-27T17:00:00Z'
            actual_delivery_date: '2025-08-27T16:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-600100001
            shipment_id: SH-60010-001
            carrier: UPS
            status: delivered
            current_location: Springfield, IL
            estimated_delivery: '2025-08-27T17:00:00Z'
            last_update: '2025-08-27T16:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LI-60010-001
            order_id: ORD-60010
            sku: CAM-4521
            product_name: DSLR camera
            quantity: 1
            base_price: 799
            discount_amount: 0
            final_price: 799
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-60010-001
            order_id: ORD-60010
            customer_id: CUS-20010
            amount: 799
            status: authorized
            payment_method: Visa ending in 1234
            transaction_date: '2025-08-24T10:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: CAM-4521
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: MAIN-C15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: CAM-4521
            name: DSLR camera
            category: audio_video
            brand: Canon
            base_price: 799
            weight_lbs: 3.2
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20010
            email: customer2@example.com
            name: Jane Roe
            phone: +1-555-0987
            registration_date: '2024-06-15T14:20:00Z'
            customer_tier: standard
            lifetime_value: 3995
            total_orders: 5
            customer_score: 84
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.4
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request for Camera
                priority: normal
                assignee_id: '2'
                description: Customer requests return of opened but non-defective camera
                requester_id: '10002'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-60010
              customer_id: CUS-20010
              removal_fee: 0
              is_defective: false
              line_item_id: LI-60010-001
              refund_amount: 790.01
              return_reason: changed_mind
              restocking_fee: 0
              return_shipping_cost: 8.99
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_002(x: TestContext, judge: Judge):
    """!
    query: I'm following up on my open ticket about returning my Samsung Galaxy Tab A9+ (order ORD-10000010). I received it more than a month ago, and it's opened but not defective. It's just not what I expected. Can I return it?
    user_context: |-
      Rules:
      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      You are Michael Rodriguez,  email: "michael.rodriguez@email.com",  "customer_id": "CUS-10000010", You purchased a tablet some time ago (say 20 days) with Order "ORD-10000010", which you want to return as it is not what you expected. You only provide IDs if asked.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-08-15T14:30:00Z'
            updated_at: '2024-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '16'
            subject: Questions about return policies
            description: Customer wants to know more details about the return policy for his last order
            status: open
            priority: low
            type: incident
            requester_id: '10'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-29T13:00:00Z'
            updated_at: '2025-09-29T13:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000010
            customer_id: CUS-10000010
            order_date: '2025-08-20T15:45:00Z'
            status: delivered
            subtotal_amount: 449
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 449
            shipping_address_line1: 2847 Oak Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000010
            order_id: ORD-10000010
            carrier: UPS
            tracking_number: TRK-100000000010
            ship_date: '2025-08-21T09:30:00Z'
            estimated_delivery_date: '2025-08-23T17:00:00Z'
            actual_delivery_date: '2025-08-22T14:15:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000010
            shipment_id: SHP-10000010
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-08-23T17:00:00Z'
            last_update: '2025-08-22T14:15:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000010
            order_id: ORD-10000010
            sku: TAB-7832
            product_name: Samsung Galaxy Tab A9+ 11-inch Android Tablet
            quantity: 1
            base_price: 449
            discount_amount: 0
            final_price: 449
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000010
            order_id: ORD-10000010
            customer_id: CUS-10000010
            amount: 449
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-08-20T15:45:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000010
            order_id: ORD-10000010
            sku: TAB-7832
            customer_id: CUS-10000010
            warranty_type: manufacturer
            start_date: '2025-08-22T00:00:00Z'
            end_date: '2026-08-22T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: TAB-7832
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: TAB-7832
            name: Samsung Galaxy Tab A9+ 11-inch Android Tablet
            category: computing
            brand: Samsung
            base_price: 449
            weight_lbs: 1.8
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2024-08-15T14:30:00Z'
            customer_tier: standard
            lifetime_value: 1247.5
            total_orders: 3
            customer_score: 56
            behavioral_segment: opportunist
            acquisition_source: paid_search
            discount_usage_rate: 0.72
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000010
          - tool: get_order
            parameters:
              order_id: ORD-10000010
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'michael.rodriguez@email.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '10' and created_at ge '2025-09-23T00:00:00Z'
              $select: null
              $orderby: null
          - tool: zendesk_update_item
            parameters:
              id: '16'
              item:
                tags: null
                type: null
                due_at: null
                status: null
                subject: null
                priority: normal
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
          - tool: zendesk_update_item
            parameters:
              id: '16'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_003(x: TestContext, judge: Judge):
    """!
    query: I received the wrong model of headphones in my order ORD-10000015, which was delivered a few weeks ago. I opened the box, but it's unused. I'd like to return it for a refund. What do I need to do?
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.


      Only provide these details when specifically asked:

      email : [michael.rodriguez@email.com](mailto:michael.rodriguez@email.com)

      order ID: ORD-10000015

      customer ID: CUS-10000015

      order delivery date: 8 September 2025

      order placed date:  6 September 2025

      Box Opened: yes
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-03-12T09:30:00Z'
            updated_at: '2024-03-12T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '15'
            subject: Order delivery issue
            description: Customer reported issue with previous order delivery
            status: solved
            priority: normal
            type: incident
            requester_id: '15'
            assignee_id: '2'
            organization_id: '1'
            tags:
            - delivery
            - order
            created_at: '2025-09-20T10:15:00Z'
            updated_at: '2025-09-25T16:30:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 23118465221950
            ticket_id: 15
            author_id: 15
            body: Customer reported issue with previous order delivery
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">Customer reported issue with previous order delivery</p></div>
            public: true
            created_at: '2025-09-20T10:15:00Z'
            ItemInternalId: 950d7175-2bb9-41d9-9131-d5f2e57af9f0
            key: '23118465221950'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-09-06T11:45:00Z'
            status: delivered
            subtotal_amount: 179.99
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 8.99
            total_amount: 188.98
            shipping_address_line1: 742 Maple Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: UPS
            tracking_number: TRK-100000000015
            ship_date: '2025-09-07T09:30:00Z'
            estimated_delivery_date: '2025-09-08T17:00:00Z'
            actual_delivery_date: '2025-09-08T14:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000015
            shipment_id: SHP-10000015
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-08T17:00:00Z'
            last_update: '2025-09-08T14:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: AUD-6623
            product_name: Sony WH-CH720N Wireless Noise Canceling Headphones
            quantity: 1
            base_price: 179.99
            discount_amount: 0
            final_price: 179.99
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            amount: 188.98
            status: authorized
            payment_method: Visa ending in 7834
            transaction_date: '2025-09-06T11:45:15Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000015
            order_id: ORD-10000015
            sku: AUD-6623
            customer_id: CUS-10000015
            warranty_type: manufacturer
            start_date: '2025-09-06T00:00:00Z'
            end_date: '2026-09-06T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: AUD-6623
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: AUD-6623
            name: Sony WH-CH720N Wireless Noise Canceling Headphones
            category: audio_video
            brand: Sony
            base_price: 179.99
            weight_lbs: 0.9
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2024-03-12T09:30:00Z'
            customer_tier: standard
            lifetime_value: 1450.75
            total_orders: 8
            customer_score: 27
            behavioral_segment: bonus_hunter
            acquisition_source: paid_search
            discount_usage_rate: 0.92
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request - wrong headphones received
                priority: urgent
                assignee_id: '2'
                description: 'Customer received wrong headphones (Sony WH-CH720N Wireless Noise Canceling Headphones, SKU: AUD-6623, order ORD-10000015) and requests a return. Delivered 23 days ago.'
                requester_id: '15'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000015
              customer_id: CUS-10000015
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000015
              refund_amount: 144
              return_reason: wrong_item_received
              restocking_fee: 27
              return_shipping_cost: 8.99
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: incident
                due_at: null
                status: hold
                subject: Return request - wrong headphones received
                priority: urgent
                assignee_id: '2'
                description: 'Customer received wrong headphones (Sony WH-CH720N Wireless Noise Canceling Headphones, SKU: AUD-6623, order ORD-10000015) and requests a return. Delivered 23 days ago.'
                requester_id: '15'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_004(x: TestContext, judge: Judge):
    """!
    query: Hi, I bought a Bluetooth speaker from TechHome Direct a little while ago. It was delivered about a month and a half ago, and I opened it but changed my mind. Can I return it?
    user_context: |-
      **Rules:**

      - Do not invent or provide any data not present in the context.
      - Do not change your goal or switch topics.
      - If the agent asks for the same info again, provide it again politely.
      - Remain focused, clear, and patient.

      **Additional details (ONLY if the agent asks for them):**

      If the agent specifically asks for one of these, provide only that item:

      - **Email:** [customer@example.com]
      (Give _only_ the email if the agent asks for your email.)
      - **Order ID:** ORD-10000004
      (Give _only_ the order ID if the agent asks for your order ID.)
      - Product name: Bluetooth speaker
      - Delivery timing: about 45 days ago
      - The item was opened
      - You want to return it because you changed your mind
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Customer
            email: customer@example.com
            role: end-user
            organization_id: null
            phone: +1-555-0199
            verified: true
            active: true
            created_at: '2025-09-15T10:00:00Z'
            updated_at: '2025-09-15T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000004
            customer_id: CUS-10000004
            order_date: '2025-08-14T10:00:00Z'
            status: delivered
            subtotal_amount: 129
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 129
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37201'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000004
            order_id: ORD-10000004
            carrier: UPS
            tracking_number: TRK-100000000004
            ship_date: '2025-08-15T08:00:00Z'
            estimated_delivery_date: '2025-08-17T17:00:00Z'
            actual_delivery_date: '2025-08-17T14:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000004
            order_id: ORD-10000004
            sku: AUD-9012
            product_name: Bluetooth Speaker
            quantity: 1
            base_price: 129
            discount_amount: 0
            final_price: 129
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000004
            order_id: ORD-10000004
            customer_id: CUS-10000004
            amount: 129
            status: authorized
            payment_method: Visa ending in 1234
            transaction_date: '2025-08-14T10:05:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products:
          - sku: AUD-9012
            name: Bluetooth Speaker
            category: audio_video
            brand: TechSound
            base_price: 129
            weight_lbs: 2.5
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000004
            email: customer@example.com
            name: Customer
            phone: +1-555-0199
            registration_date: '2025-08-14T10:00:00Z'
            customer_tier: standard
            lifetime_value: 129
            total_orders: 1
            customer_score: 51
            behavioral_segment: opportunist
            acquisition_source: organic_search
            discount_usage_rate: 0
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000004
          - tool: get_order
            parameters:
              order_id: ORD-10000004
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'customer@example.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '6' and (status eq 'open' or status eq 'pending' or status eq 'hold')
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request for Bluetooth Speaker (ORD-10000004)
                priority: normal
                assignee_id: '2'
                description: 'Customer requests to return opened Bluetooth speaker (SKU: AUD-9012, order ORD-10000004) delivered 45 days ago.'
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000004
              customer_id: CUS-10000004
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000004
              refund_amount: 120.01
              return_reason: changed_mind
              restocking_fee: 0
              return_shipping_cost: 8.99
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_005(x: TestContext, judge: Judge):
    """!
    query: Hi, I'd like to return my Dell 27-inch 4K Monitor (order ORD-20000001). It's unopened and not what I expected based on the specs. Can you help me start the return?
    user_context: |-
      You are Michael Thompson, a TechHome Direct customer. You are looking to return the monitor you ordered and the reason for return is that the monitor is not what you were expecting based on the specs, your email is [michael.thompson@email.com](mailto:michael.thompson@email.com), you contacted the support yesterday to request information about returning unopened items



      —------

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      —------
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Michael Thompson
            email: michael.thompson@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0234
            verified: true
            active: true
            created_at: '2024-03-15T09:30:00Z'
            updated_at: '2024-03-15T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '6'
            subject: Return policy question for unopened items
            description: Customer inquiring about return policy for unopened items
            status: open
            priority: low
            type: incident
            requester_id: '6'
            assignee_id: '2'
            created_at: '2025-09-30T10:15:00Z'
            updated_at: '2025-09-30T10:15:00Z'
          zendesk_ticket_comments:
          - id: 23118465221921
            ticket_id: 6
            author_id: 6
            body: Customer inquiring about return policy for unopened items
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">Customer inquiring about return policy for unopened items</p></div>
            public: true
            created_at: '2025-09-30T10:15:00Z'
            ItemInternalId: 623d7175-2bb9-41d9-9131-d5f2e57af9fc
            key: '23118465221921'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-08-10T14:30:00Z'
            status: delivered
            subtotal_amount: 329
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 329
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: UPS
            tracking_number: TRK-200000000001
            ship_date: '2025-08-11T09:15:00Z'
            estimated_delivery_date: '2025-08-12T17:00:00Z'
            actual_delivery_date: '2025-08-12T15:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-08-12T17:00:00Z'
            last_update: '2025-08-12T15:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: MON-3345
            product_name: Dell 27-inch 4K Monitor
            quantity: 1
            base_price: 329
            discount_amount: 0
            final_price: 329
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 329
            status: authorized
            payment_method: Visa ending in 7892
            transaction_date: '2025-08-10T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: MON-3345
            available_quantity: 25
            reserved_quantity: 4
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: MON-3345
            name: Dell 27-inch 4K Monitor
            category: audio_video
            brand: Dell
            base_price: 329
            weight_lbs: 12.4
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: michael.thompson@email.com
            name: Michael Thompson
            phone: +1-555-0234
            registration_date: '2024-03-15T09:30:00Z'
            customer_tier: standard
            lifetime_value: 1847.5
            total_orders: 6
            customer_score: 33
            behavioral_segment: bonus_hunter
            acquisition_source: paid_search
            discount_usage_rate: 0.92
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: michael.thompson@email.com
              customer_id: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'michael.thompson@email.com'
              $select: null
              $orderby: null
          - tool: get_order
            parameters:
              order_id: ORD-20000001
          - tool: get_shipment_tracking
            parameters:
              order_id: ORD-20000001
          - tool: get_product_details
            parameters:
              sku: MON-3345
          - tool: zendesk_search_articles
            parameters:
              query: return shipping cost
              locale: null
              section: null
              brand_id: null
              category: null
              multibrand: null
              label_names: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '6'
              $select: null
              $orderby: null
          - tool: create_rma
            parameters:
              order_id: ORD-20000001
              customer_id: CUS-20000001
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-20000001
              refund_amount: 320.01
              return_reason: not_as_expected
              restocking_fee: 0
              return_shipping_cost: 8.99
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: normal
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_006(x: TestContext, judge: Judge):
    """!
    query: Hi, I recently bought a Panasonic Countertop Microwave (order number ORD-20000001) and it was delivered about a month and a half ago. I changed my mind and would like to return it. The microwave has been opened but is not defective. Can you help me with the return process?
    user_context: |+
      **Rules:**

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      **Context:** You are Sarah Johnson, a Standard tier customer of TechHome Direct. You placed order **ORD-20000001** 47 days ago for a Panasonic Countertop Microwave. It was delivered 44 days ago. You have opened the box, but the item is not defective; it works fine, but you simply changed your mind and want to return it for a refund.

      **Specific Information to Provide (Only if asked):**

      - **Order ID:** ORD-20000001
      - **Item Condition:** Opened, non-defective.
      - **Reason for Return:** Changed mind.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '20001'
            name: Sarah Johnson
            email: sarah.johnson@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0234
            verified: true
            active: true
            created_at: '2024-03-15T10:00:00Z'
            updated_at: '2024-03-15T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '16'
            subject: Question about fridge
            description: Customer wants more information about frigerator
            status: solved
            priority: normal
            type: incident
            requester_id: '20001'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-28T13:00:00Z'
            updated_at: '2025-09-28T13:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-08-15T14:30:00Z'
            status: delivered
            subtotal_amount: 189
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 189
            shipping_address_line1: 456 Maple Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: UPS
            tracking_number: TRK-200000000001
            ship_date: '2025-08-16T09:00:00Z'
            estimated_delivery_date: '2025-08-18T17:00:00Z'
            actual_delivery_date: '2025-08-18T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-08-18T17:00:00Z'
            last_update: '2025-08-18T15:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: APPL-5678
            product_name: Panasonic Countertop Microwave 1.2 cu ft
            quantity: 1
            base_price: 189
            discount_amount: 0
            final_price: 189
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 189
            status: authorized
            payment_method: Visa ending in 3456
            transaction_date: '2025-08-15T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: APPL-5678
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-08-18T00:00:00Z'
            end_date: '2026-08-18T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for small appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-5678
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-5678
            name: Panasonic Countertop Microwave 1.2 cu ft
            category: appliances
            brand: Panasonic
            base_price: 189
            weight_lbs: 42
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: sarah.johnson@email.com
            name: Sarah Johnson
            phone: +1-555-0234
            registration_date: '2024-03-15T10:00:00Z'
            customer_tier: standard
            lifetime_value: 756.5
            total_orders: 4
            customer_score: 62
            behavioral_segment: opportunist
            acquisition_source: paid_search
            discount_usage_rate: 0.75
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: 'Return request: Panasonic Countertop Microwave (ORD-20000001)'
                priority: normal
                assignee_id: '2'
                description: 'Customer requests to return opened, non-defective microwave (SKU: APPL-5678, order ORD-20000001, delivered 44 days ago, weight 42 lbs). Customer is Standard tier. Return window valid. Item opened, not defective.'
                requester_id: '20001'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-20000001
              customer_id: CUS-20000001
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-20000001
              refund_amount: 160.65
              return_reason: changed_mind
              restocking_fee: 28.35
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: 'RMA created for return of microwave (SKU: APPL-5678, order ORD-20000001). Refund amount: $160.65 (15% restocking fee applied, no shipping fee). Ticket set to hold while return is processed.'
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_008(x: TestContext, judge: Judge):
    """!
    query: Hi, I want to return my Bosch 500 Series Built-In Dishwasher purchased a couple of weeks back before the installation happens, as it's not as expected.  I had called yesterday to enquire about cancellation options. What do I need to do to start the return?
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      If the agent asks for the Order ID, share the Order ID ORD-20000001.

      Provide your email address [michael.rodriguez@email.com](mailto:michael.rodriguez@email.com), if the agent asks for it.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-08-15T14:30:00Z'
            updated_at: '2024-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '6'
            subject: Cancellation options for dishwasher order
            description: Customer inquiring about cancellation options for their dishwasher order ORD-20000001 before installation
            status: open
            priority: low
            type: incident
            requester_id: '6'
            assignee_id: '2'
            tags: []
            created_at: '2025-09-30T14:20:00Z'
            updated_at: '2025-09-30T14:20:00Z'
            due_at: null
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-09-13T16:45:00Z'
            status: installation_scheduled
            subtotal_amount: 649
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 649
            shipping_address_line1: 2847 Oak Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-20000001
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: FedEx
            tracking_number: TRK-200000000001
            ship_date: '2025-09-15T09:30:00Z'
            estimated_delivery_date: '2025-09-21T17:00:00Z'
            actual_delivery_date: '2025-09-21T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-21T17:00:00Z'
            last_update: '2025-09-21T15:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: APPL-2394
            product_name: Bosch 500 Series Built-In Dishwasher
            quantity: 1
            base_price: 649
            discount_amount: 0
            final_price: 649
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 778
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2025-09-13T16:45:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: APPL-2394
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-09-21T00:00:00Z'
            end_date: '2028-09-21T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            service_type: appliance_basic
            scheduled_date: '2025-10-04T10:00:00Z'
            technician_id: TECH-0067
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-2394
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-2394
            name: Bosch 500 Series Built-In Dishwasher
            category: appliances
            brand: Bosch
            base_price: 649
            weight_lbs: 68
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2024-08-15T14:30:00Z'
            customer_tier: standard
            lifetime_value: 1298.5
            total_orders: 2
            customer_score: 58
            behavioral_segment: opportunist
            acquisition_source: organic_search
            discount_usage_rate: 0.75
        golden_test_case:
          tool_interactions:
          - tool: cancel_installation
            parameters:
              job_id: JOB-20000001
              order_id: ORD-20000001
              cancellation_reason: customer_cancelled_order
          - tool: create_rma
            parameters:
              order_id: ORD-20000001
              customer_id: CUS-20000001
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-20000001
              refund_amount: 649
              return_reason: not_as_expected
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: incident
                due_at: null
                status: hold
                subject: null
                priority: normal
                assignee_id: '2'
                description: Return initiated for Bosch 500 Series Built-In Dishwasher (ORD-20000001). Installation appointment cancelled. RMA created for unopened item. Refund will be processed after item is received at warehouse. Next steps will be sent to your email.
                requester_id: '6'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_010(x: TestContext, judge: Judge):
    """!
    query: Hi, I’m Michael Rodriguez, and my Samsung front-load washer from order ORD-20000001 that you delivered and installed around a month ago isn’t performing as I expected, so I want to have it picked up and refunded.
    user_context: |-
      - Email: [michael.rodriguez@email.com](mailto:michael.rodriguez@email.com)
      - Phone: +1-555-0198
      - Product: Samsung Front-Load Washing Machine 4.5 cu ft
      - Goal: Have TechHome take the washer back and give you your money back

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2023-05-12T14:20:00Z'
            updated_at: '2023-05-12T14:20:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-08-23T16:45:00Z'
            status: delivered
            subtotal_amount: 749
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 749
            shipping_address_line1: 2847 Oak Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-20000001
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: FedEx
            tracking_number: TRK-200000000001
            ship_date: '2025-08-25T09:30:00Z'
            estimated_delivery_date: '2025-08-30T17:00:00Z'
            actual_delivery_date: '2025-08-30T14:15:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-08-30T17:00:00Z'
            last_update: '2025-08-30T14:15:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: APPL-5543
            product_name: Samsung Front-Load Washing Machine 4.5 cu ft
            quantity: 1
            base_price: 749
            discount_amount: 0
            final_price: 749
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 749
            status: authorized
            payment_method: Visa ending in 7892
            transaction_date: '2025-08-23T16:45:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: APPL-5543
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-08-30T00:00:00Z'
            end_date: '2028-08-30T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            service_type: appliance_basic
            scheduled_date: '2025-08-30T10:00:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2025-08-30T15:30:00Z'
            workmanship_warranty_end: '2025-11-28T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-5543
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-5543
            name: Samsung Front-Load Washing Machine 4.5 cu ft
            category: appliances
            brand: Samsung
            base_price: 749
            weight_lbs: 198
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2023-05-12T14:20:00Z'
            customer_tier: standard
            lifetime_value: 3250.75
            total_orders: 11
            customer_score: 89
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request for Samsung front-load washer not as expected
                priority: normal
                assignee_id: '2'
                description: Customer requests pickup and refund for Samsung front-load washer (order ORD-20000001, installed and delivered 32 days ago, not performing as expected)
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-20000001
              customer_id: CUS-20000001
              removal_fee: 50
              is_defective: false
              line_item_id: LIN-20000001
              refund_amount: 699
              return_reason: not_as_expected
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_011(x: TestContext, judge: Judge):
    """!
    query: Hi, I’m reaching out about an incorrect color Whirlpool electric dryer that was delivered to me. My customer ID is CUS-10000025, and my order ID is ORD-2-78432. The dryer was delivered 19 days ago, has already been installed and opened, but I still need to request a return since it’s not the item I ordered.
    user_context: |-
      RULES to follow:

      • You need the agent to initiate the return (create RMA).

      • Do not invent or provide any data not present in the provided context.

      • Do not change your goal or switch topics.

      • If asked for the same information, you can provide it again.

      • Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '25'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2025-09-04T10:00:00Z'
            updated_at: '2025-09-04T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '25'
            subject: Wrong Item received
            description: Customer received the wrong color dryer and wants to return the item.
            status: open
            priority: urgent
            type: incident
            requester_id: '25'
            assignee_id: '2'
            organization_id: null
            created_at: '2025-09-29T10:00:00Z'
            updated_at: '2025-09-29T10:00:00Z'
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-2-78432
            customer_id: CUS-10000025
            order_date: '2025-09-05T14:30:00Z'
            status: delivered
            subtotal_amount: 599
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 728
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000025
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000025
            order_id: ORD-2-78432
            carrier: FedEx
            tracking_number: TRK-100000000025
            ship_date: '2025-09-06T09:00:00Z'
            estimated_delivery_date: '2025-09-12T17:00:00Z'
            actual_delivery_date: '2025-09-12T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000025
            shipment_id: SHP-10000025
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-12T17:00:00Z'
            last_update: '2025-09-12T15:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000025
            order_id: ORD-2-78432
            sku: APPL-6689
            product_name: Whirlpool Electric Dryer 7.4 cu ft
            quantity: 1
            base_price: 599
            discount_amount: 0
            final_price: 599
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000025
            order_id: ORD-2-78432
            customer_id: CUS-10000025
            amount: 728
            status: authorized
            payment_method: Visa ending in 3456
            transaction_date: '2025-09-05T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000025
            order_id: ORD-2-78432
            customer_id: CUS-10000025
            service_type: appliance_basic
            scheduled_date: '2025-09-12T18:30:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2025-09-12T20:30:00Z'
            workmanship_warranty_end: '2025-12-11T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-6689
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-6689
            name: Whirlpool Electric Dryer 7.4 cu ft
            category: appliances
            brand: Whirlpool
            base_price: 599
            weight_lbs: 152
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000025
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2025-09-04T10:00:00Z'
            customer_tier: standard
            lifetime_value: 728
            total_orders: 1
            customer_score: 45
            behavioral_segment: opportunist
            acquisition_source: google_ads
            discount_usage_rate: 0.75
        golden_test_case:
          tool_interactions:
          - tool: create_rma
            parameters:
              order_id: ORD-2-78432
              customer_id: CUS-10000025
              removal_fee: 50
              is_defective: false
              line_item_id: LIN-10000025
              refund_amount: 549
              return_reason: wrong_item_received
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '25'
              item:
                tags: null
                type: incident
                due_at: null
                status: hold
                subject: Return wrong item
                priority: urgent
                assignee_id: '2'
                description: 'Return process initiated for Whirlpool Electric Dryer (SKU: APPL-6689) as item is not the model ordered. Customer instructed on return of installed appliance.'
                requester_id: '25'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_015(x: TestContext, judge: Judge):
    """!
    query: 'Hi, I recently bought a Dell Inspiron 14 Laptop (SKU: COMP-7756) from TechHome Direct, order ORD-10000010, and it was delivered about 18 days ago. I’ve opened the box but haven’t used it, and I’ve changed my mind. Can you initiate a return quickly?'
    user_context: |+
      Rules:

      Never change the original goal or switch topics.

      Do not invent or provide any data not present in the provided context.

      Do not provide information the agent is expected to obtain with their tools.

      If asked for the same info multiple times, provide it again.

      Remain clear, focused, and patient until the goal is achieved or clearly impossible.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2025-09-11T10:30:00Z'
            updated_at: '2025-09-11T10:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '101'
            subject: Shipping timeframes
            description: What are the shipping timeframes for a laptop
            status: solved
            priority: urgent
            type: incident
            requester_id: '10'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-29T13:00:00Z'
            updated_at: '2025-09-29T15:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000010
            customer_id: CUS-10000010
            order_date: '2025-09-11T14:20:00Z'
            status: delivered
            subtotal_amount: 1299
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 15
            total_amount: 1314
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000010
            order_id: ORD-10000010
            carrier: UPS
            tracking_number: TRK-100000000010
            ship_date: '2025-09-12T09:15:00Z'
            estimated_delivery_date: '2025-09-13T17:00:00Z'
            actual_delivery_date: '2025-09-13T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000010
            shipment_id: SHP-10000010
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-13T17:00:00Z'
            last_update: '2025-09-13T15:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000010
            order_id: ORD-10000010
            sku: COMP-7756
            product_name: Dell Inspiron 14 Laptop
            quantity: 1
            base_price: 1299
            discount_amount: 0
            final_price: 1299
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000010
            order_id: ORD-10000010
            customer_id: CUS-10000010
            amount: 1314
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2025-09-11T14:20:15Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000010
            order_id: ORD-10000010
            sku: COMP-7756
            customer_id: CUS-10000010
            warranty_type: manufacturer
            start_date: '2025-09-13T00:00:00Z'
            end_date: '2026-09-13T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: COMP-7756
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: COMP-7756
            name: Dell Inspiron 14 Laptop
            category: computing
            brand: Dell
            base_price: 1299
            weight_lbs: 3.8
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2025-09-11T10:30:00Z'
            customer_tier: standard
            lifetime_value: 1299
            total_orders: 1
            customer_score: 67
            behavioral_segment: opportunist
            acquisition_source: organic_search
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000010
          - tool: get_order
            parameters:
              order_id: ORD-10000010
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'sarah.martinez@email.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '10'
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: 'Return request for Dell Inspiron 14 Laptop (SKU: COMP-7756, Order: ORD-10000010)'
                priority: normal
                assignee_id: '2'
                description: Customer requests to return unopened Dell Inspiron 14 Laptop delivered 18 days ago. Eligible for standard 30-day return window.
                requester_id: '10'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000010
              customer_id: CUS-10000010
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000010
              refund_amount: 1290.01
              return_reason: changed_mind
              restocking_fee: 0
              return_shipping_cost: 8.99
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_016(x: TestContext, judge: Judge):
    """!
    query: Hi, I bought a Sony Alpha a7 IV Mirrorless Camera (order ORD-10000015) about two months ago, and it was delivered to me in Austin on July 31st. I’ve opened it and tried it out, but it’s not meeting my expectations. I’d like to return it. Can you help me with the return process?
    user_context: |-
      Rules:
      Do not invent or provide any data that is not present in the provided context.
      Do not change your goal or switch topics.
      If the agent asks again for the same information, provide it again.
      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2023-08-15T14:30:00Z'
            updated_at: '2023-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-07-28T16:45:00Z'
            status: delivered
            subtotal_amount: 1199
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1199
            shipping_address_line1: 742 Oak Ridge Drive
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78704'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: UPS
            tracking_number: TRK-100000000015
            ship_date: '2025-07-29T09:30:00Z'
            estimated_delivery_date: '2025-07-31T17:00:00Z'
            actual_delivery_date: '2025-07-31T15:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: CAM-3398
            product_name: Sony Alpha a7 IV Mirrorless Camera
            quantity: 1
            base_price: 1199
            discount_amount: 0
            final_price: 1199
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            amount: 1199
            status: authorized
            payment_method: Visa ending in 8742
            transaction_date: '2025-07-28T16:45:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: CAM-3398
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: CAM-3398
            name: Sony Alpha a7 IV Mirrorless Camera
            category: electronics
            brand: Sony
            base_price: 1199
            weight_lbs: 2.9
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000015
            customer_id: CUS-10000015
            membership_type: plus
            start_date: '2024-01-01T00:00:00Z'
            end_date: '2024-12-31T23:59:59Z'
            status: active
            points_balance: 1250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2023-08-15T14:30:00Z'
            customer_tier: plus_member
            lifetime_value: 3850.75
            total_orders: 8
            customer_score: 86
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.35
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000015
          - tool: get_order
            parameters:
              order_id: ORD-10000015
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'sarah.martinez@email.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '15' and status eq 'open'
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags:
                - return
                - camera
                - plus_member
                type: incident
                due_at: null
                status: open
                subject: Return request for Sony Alpha a7 IV Mirrorless Camera (ORD-10000015)
                priority: high
                assignee_id: '2'
                description: 'Customer requests to return Sony Alpha a7 IV Mirrorless Camera (SKU: CAM-3398, order ORD-10000015) delivered on 2025-07-31. Item opened, not meeting expectations.'
                requester_id: '15'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000015
              customer_id: CUS-10000015
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000015
              refund_amount: 1199
              return_reason: not_as_expected
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_017(x: TestContext, judge: Judge):
    """!
    query: Hi, I'd like to return my unopened 10-inch Android Tablet (order ORD-10000015) that was delivered about two months ago. I changed my mind and don't need it anymore. Can you help me with the return process?
    user_context: |-
      You are Sarah Martinez with email [sarah.martinez@email.com](mailto:sarah.martinez@email.com)

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0156
            verified: true
            active: true
            created_at: '2024-02-10T14:30:00Z'
            updated_at: '2024-02-10T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '15'
            subject: Plus member return window inquiry
            description: Customer asking about return window for Plus members
            status: open
            priority: high
            type: incident
            requester_id: '15'
            assignee_id: '2'
            tags: []
            created_at: '2025-09-30T13:00:00Z'
            updated_at: '2025-09-30T13:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-07-21T10:15:00Z'
            status: delivered
            subtotal_amount: 329
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 329
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: UPS
            tracking_number: TRK-100000000015
            ship_date: '2025-07-22T09:00:00Z'
            estimated_delivery_date: '2025-07-24T15:30:00Z'
            actual_delivery_date: '2025-07-24T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: TAB-4421
            product_name: 10-inch Android Tablet
            quantity: 1
            base_price: 329
            discount_amount: 0
            final_price: 329
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            amount: 329
            status: authorized
            payment_method: Visa ending in 7890
            transaction_date: '2025-07-21T10:15:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products:
          - sku: TAB-4421
            name: 10-inch Android Tablet
            category: computing
            brand: TechBrand
            base_price: 329
            weight_lbs: 1.2
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0156
            registration_date: '2024-02-10T14:30:00Z'
            customer_tier: plus_member
            lifetime_value: 1645.75
            total_orders: 5
            customer_score: 59
            behavioral_segment: opportunist
            acquisition_source: email_marketing
            discount_usage_rate: 0.72
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000015
          - tool: create_rma
            parameters:
              order_id: ORD-10000015
              customer_id: CUS-10000015
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000015
              refund_amount: 329
              return_reason: changed_mind
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '15'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: 'Customer requested return of unopened 10-inch Android Tablet (SKU: TAB-4421, line item LIN-10000015) from order ORD-10000015. RMA RMA-20000004 has been created (approved). We have emailed you a prepaid return shipping label; please affix it and deposit the package with the carrier. Once we receive the item, a full refund of $329.00 will be processed to your original payment method within 7-10 business days.'
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_019(x: TestContext, judge: Judge):
    """!
    query: Hi, I ordered a Samsung side-by-side refrigerator (order ORD-10000015) about 25 days ago, and it's scheduled for installation in a few days. I haven't opened it yet, but after doing more research, I realized it's not what i expected. I'd like to return it before the installation happens. Can you help me please?
    user_context: |-
      Only provide these details when specifically asked:

      email : [sarah.martinez@email.com](mailto:sarah.martinez@email.com)

      order_id: ORD-10000015

      customer_id: CUS-10000015

      order_delivery_date: 16 September 2025

      order_placed_date:  6 September 2025

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2023-08-15T14:30:00Z'
            updated_at: '2023-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-09-06T10:15:00Z'
            status: installation_scheduled
            subtotal_amount: 2199
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 2328
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37205'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000015
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: FedEx
            tracking_number: TRK-100000000015
            ship_date: '2025-09-08T09:00:00Z'
            estimated_delivery_date: '2025-09-16T17:00:00Z'
            actual_delivery_date: '2025-09-16T14:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000015
            shipment_id: SHP-10000015
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-16T17:00:00Z'
            last_update: '2025-09-16T14:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: APPL-1156
            product_name: Samsung 28 cu ft Side-by-Side Refrigerator
            quantity: 1
            base_price: 2199
            discount_amount: 0
            final_price: 2199
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            amount: 2328
            status: authorized
            payment_method: Visa ending in 7892
            transaction_date: '2025-09-06T10:15:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000015
            order_id: ORD-10000015
            sku: APPL-1156
            customer_id: CUS-10000015
            warranty_type: manufacturer
            start_date: '2025-09-16T00:00:00Z'
            end_date: '2028-09-16T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            service_type: appliance_basic
            scheduled_date: '2025-10-06T10:00:00Z'
            technician_id: TECH-0067
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-1156
            available_quantity: 8
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-1156
            name: Samsung 28 cu ft Side-by-Side Refrigerator
            category: appliances
            brand: Samsung
            base_price: 2199
            weight_lbs: 312
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000015
            customer_id: CUS-10000015
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 1250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2023-08-15T14:30:00Z'
            customer_tier: plus_member
            lifetime_value: 3850.75
            total_orders: 9
            customer_score: 74
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request for Samsung refrigerator, order ORD-10000015
                priority: high
                assignee_id: '2'
                description: Customer Sarah Martinez (Plus member) requests to return unopened Samsung 28 cu ft Side-by-Side Refrigerator (LIN-10000015) from order ORD-10000015, delivered 15 days ago, installation scheduled but not completed. Customer states product is not as expected.
                requester_id: '15'
                organization_id: null
              table: tickets
          - tool: cancel_installation
            parameters:
              job_id: JOB-10000015
              order_id: ORD-10000015
              cancellation_reason: customer_cancelled_order
          - tool: create_rma
            parameters:
              order_id: ORD-10000015
              customer_id: CUS-10000015
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000015
              refund_amount: 2199
              return_reason: not_as_expected
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: incident
                due_at: null
                status: hold
                subject: Return request for Samsung refrigerator, order ORD-10000015
                priority: high
                assignee_id: '2'
                description: Customer Sarah Martinez (Plus member) requests to return unopened Samsung 28 cu ft Side-by-Side Refrigerator (LIN-10000015) from order ORD-10000015, delivered 15 days ago, installation scheduled but not completed. Customer states product is not as expected.
                requester_id: '15'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_021(x: TestContext, judge: Judge):
    """!
    query: 'Hi, I want to return my Next-Gen Gaming Console (order ORD-08012222). I received the wrong console bundle and have already opened the box. The order was delivered about two and a half months ago. Can you help me with the return process? '
    user_context: "You are a TechHome Plus member contacting TechHome Direct customer support to return a gaming console because the wrong console bundle was delivered.\n\nDo not invent or provide any data not present in the provided context.\nDo not change your goal or switch topics.\nIf asked for the same info, provide it again.\nRemain focused, clear, and patient.\n\nProvide these details only if the agent asks for them:\n\n- Email: [rachel.adams@example.com](mailto:rachel.adams@example.com)  \n- Order number: ORD-08012222  \n- Delivery date: 78 days ago  \n- Item details: Next-Gen Gaming Console, quantity 1, opened  \n- No installation service was involved  "
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '99887766'
            name: Rachel Adams
            email: rachel.adams@example.com
            role: end-user
            organization_id: null
            phone: +1-555-0789
            verified: true
            active: true
            created_at: '2023-05-15T10:30:00Z'
            updated_at: '2025-09-28T14:20:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '771199'
            subject: Discount inquiry for last purchase
            description: Customer asking about discount eligibility for recent order
            status: solved
            priority: high
            type: question
            requester_id: '99887766'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-28T10:00:00Z'
            updated_at: '2025-09-28T15:30:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-08012222
            customer_id: CUS-20000001
            order_date: '2025-07-12T14:30:00Z'
            status: delivered
            subtotal_amount: 499.99
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 499.99
            shipping_address_line1: 456 Maple Street
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-08012222
            carrier: UPS
            tracking_number: TRK-200000000001
            ship_date: '2025-07-13T09:15:00Z'
            estimated_delivery_date: '2025-07-15T17:00:00Z'
            actual_delivery_date: '2025-07-15T14:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-07-15T17:00:00Z'
            last_update: '2025-07-15T14:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-01333333
            order_id: ORD-08012222
            sku: GAME-7745
            product_name: Next-Gen Gaming Console
            quantity: 1
            base_price: 499.99
            discount_amount: 0
            final_price: 499.99
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions: []
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: GAME-7745
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: GAME-7745
            name: Next-Gen Gaming Console
            category: gaming
            brand: TechGaming
            base_price: 499.99
            weight_lbs: 9.8
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-20000001
            customer_id: CUS-20000001
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 1850
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: rachel.adams@example.com
            name: Rachel Adams
            phone: +1-555-0789
            registration_date: '2023-05-15T10:30:00Z'
            customer_tier: plus_member
            lifetime_value: 3250.75
            total_orders: 16
            customer_score: 29
            behavioral_segment: bonus_hunter
            acquisition_source: paid_search
            discount_usage_rate: 0.92
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Wrong console bundle delivered - return request
                priority: urgent
                assignee_id: '2'
                description: 'Customer reports receiving the wrong console bundle in order ORD-08012222 (SKU: GAME-7745). Item opened, non-defective. TechHome Plus member requesting refund.'
                requester_id: '99887766'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-08012222
              customer_id: CUS-20000001
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-01333333
              refund_amount: 499.99
              return_reason: wrong_item_received
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: incident
                due_at: null
                status: hold
                subject: Wrong console bundle delivered - return request
                priority: urgent
                assignee_id: '2'
                description: 'Customer reports receiving the wrong console bundle in order ORD-08012222 (SKU: GAME-7745). Item opened, non-defective. TechHome Plus member requesting refund.'
                requester_id: '99887766'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_022(x: TestContext, judge: Judge):
    """!
    query: Hi, I just received my Dell XPS 17 Laptop (order ORD-10000101) a few weeks ago, but after doing some research, I realized it's not what I expected. The box is still unopened. I'd like to return it. Can you help me with the return process?
    user_context: |+
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '101'
            name: Sarah Johnson
            email: customer.plus@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0201
            verified: true
            active: true
            created_at: '2025-09-04T10:00:00Z'
            updated_at: '2025-09-04T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000101
            customer_id: CUS-10000101
            order_date: '2025-09-04T14:30:00Z'
            status: delivered
            subtotal_amount: 1599
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1599
            shipping_address_line1: 456 Maple Street
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000101
            order_id: ORD-10000101
            carrier: FedEx
            tracking_number: TRK-100000000101
            ship_date: '2025-09-05T09:00:00Z'
            estimated_delivery_date: '2025-09-07T17:00:00Z'
            actual_delivery_date: '2025-09-07T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000101
            shipment_id: SHP-10000101
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-07T17:00:00Z'
            last_update: '2025-09-07T15:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000101
            order_id: ORD-10000101
            sku: COMP-8891
            product_name: Dell XPS 17 Laptop
            quantity: 1
            base_price: 1599
            discount_amount: 0
            final_price: 1599
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000101
            order_id: ORD-10000101
            customer_id: CUS-10000101
            amount: 1599
            status: authorized
            payment_method: Visa ending in 2468
            transaction_date: '2025-09-04T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: COMP-8891
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: COMP-8891
            name: Dell XPS 17 Laptop
            category: computing
            brand: Dell
            base_price: 1599
            weight_lbs: 5.3
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000101
            customer_id: CUS-10000101
            membership_type: plus
            start_date: '2025-09-04T00:00:00Z'
            end_date: '2026-09-04T23:59:59Z'
            status: active
            points_balance: 1200
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000101
            email: customer.plus@example.com
            name: Sarah Johnson
            phone: +1-555-0201
            registration_date: '2025-09-04T10:00:00Z'
            customer_tier: plus_member
            lifetime_value: 1599
            total_orders: 1
            customer_score: 79
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.3
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000101
          - tool: get_order
            parameters:
              order_id: ORD-10000101
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: 'Return request: Dell XPS 17 Laptop (ORD-10000101)'
                priority: high
                assignee_id: '2'
                description: Customer requests to return unopened Dell XPS 17 Laptop, order delivered 24 days ago, not as expected.
                requester_id: '101'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000101
              customer_id: CUS-10000101
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000101
              refund_amount: 1599
              return_reason: not_as_expected
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: RMA initiated for return of unopened Dell XPS 17 Laptop. Customer will receive instructions for shipping and refund timeline.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_023(x: TestContext, judge: Judge):
    """!
    query: Hi, I'd like to return my Sony WH-1000XM6 Noise-Canceling Headphones (order ORD-10000020) that I purchased about two months ago. I opened and tried them, but decided I don't need them. Can you help me with the return?
    user_context: "Rules\n\nDo not invent or provide any data not present in the provided context.\n\nDo not change your goal or switch topics.\n\nIf asked for the same info, provide it again.\n\nRemain focused, clear, and patient.\n\n\n\nYou are  Sarah Martinez, a VIP customer of TechHome Direct. "
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10'
            name: Sarah Martinez
            email: sarah.martinez@example.com
            role: end-user
            organization_id: null
            phone: +1-555-0190
            verified: true
            active: true
            created_at: '2022-03-15T10:00:00Z'
            updated_at: '2022-03-15T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '10'
            subject: VIP return policy inquiry
            description: Customer asking about VIP return policies and timeframes
            status: open
            priority: urgent
            type: incident
            requester_id: '10'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-29T10:00:00Z'
            updated_at: '2025-09-29T10:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000020
            customer_id: CUS-10000010
            order_date: '2025-07-25T14:30:00Z'
            status: delivered
            subtotal_amount: 349
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 349
            shipping_address_line1: 789 Oak Boulevard
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000020
            order_id: ORD-10000020
            carrier: UPS
            tracking_number: TRK-100000000020
            ship_date: '2025-07-26T09:00:00Z'
            estimated_delivery_date: '2025-07-28T17:00:00Z'
            actual_delivery_date: '2025-07-28T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000020
            shipment_id: SHP-10000020
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-07-28T17:00:00Z'
            last_update: '2025-07-28T15:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000020
            order_id: ORD-10000020
            sku: AUD-1123
            product_name: Sony WH-1000XM6 Noise-Canceling Headphones
            quantity: 1
            base_price: 349
            discount_amount: 0
            final_price: 349
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000020
            order_id: ORD-10000020
            customer_id: CUS-10000010
            amount: 349
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-07-25T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: AUD-1123
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: AUD-1123
            name: Sony WH-1000XM6 Noise-Canceling Headphones
            category: audio_video
            brand: Sony
            base_price: 349
            weight_lbs: 0.8
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: sarah.martinez@example.com
            name: Sarah Martinez
            phone: +1-555-0190
            registration_date: '2022-03-15T10:00:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 22
            customer_score: 93
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000010
          - tool: get_order
            parameters:
              order_id: ORD-10000020
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '10'
              $select: null
              $orderby: null
          - tool: create_rma
            parameters:
              order_id: ORD-10000020
              customer_id: CUS-10000010
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000020
              refund_amount: 349
              return_reason: changed_mind
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '10'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: urgent
                assignee_id: null
                description: Return for Sony WH-1000XM6 Noise-Canceling Headphones processed. RMA created for full refund with no fees as per VIP policy.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_024(x: TestContext, judge: Judge):
    """!
    query: 'Hi, I bought a Samsung 32-inch Curved Gaming Monitor ORDER ID ORD-20000001 about two and a half months ago, but the specs aren''t what I expected. It''s still unopened. Can I return it? Here is my email address: [michael.rodriguez@email.com](mailto:michael.rodriguez@email.com). '
    user_context: |-
      —------

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      —------
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0789
            verified: true
            active: true
            created_at: '2022-03-15T10:00:00Z'
            updated_at: '2025-09-27T09:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '6'
            subject: Plus membership benefits question
            description: Customer inquiring about Plus membership benefits and upgrade process
            status: solved
            priority: low
            type: question
            requester_id: '6'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-23T14:30:00Z'
            updated_at: '2025-09-27T11:45:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-07-16T15:30:00Z'
            status: delivered
            subtotal_amount: 599
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 599
            shipping_address_line1: 2847 Oak Ridge Drive
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78745'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: UPS
            tracking_number: TRK-200000000001
            ship_date: '2025-07-17T09:00:00Z'
            estimated_delivery_date: '2025-07-19T17:00:00Z'
            actual_delivery_date: '2025-07-19T14:25:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: UPS
            status: delivered
            current_location: Austin, TX
            estimated_delivery: '2025-07-19T17:00:00Z'
            last_update: '2025-07-19T14:25:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: MON-5567
            product_name: Samsung 32-inch Curved Gaming Monitor
            quantity: 1
            base_price: 599
            discount_amount: 0
            final_price: 599
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 599
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-07-16T15:30:15Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: MON-5567
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-07-19T00:00:00Z'
            end_date: '2026-07-19T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: MON-5567
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: MON-5567
            name: Samsung 32-inch Curved Gaming Monitor
            category: audio_video
            brand: Samsung
            base_price: 599
            weight_lbs: 15.2
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0789
            registration_date: '2022-03-15T10:00:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 18
            customer_score: 64
            behavioral_segment: opportunist
            acquisition_source: referral
            discount_usage_rate: 0.35
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: michael.rodriguez@email.com
              customer_id: CUS-20000001
          - tool: get_order
            parameters:
              order_id: ORD-20000001
          - tool: get_product_details
            parameters:
              sku: MON-5567
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'michael.rodriguez@email.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '6' and (status eq 'open' or status eq 'pending' or status eq 'hold')
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request - Samsung 32-inch Curved Gaming Monitor (ORD-20000001)
                priority: urgent
                assignee_id: '2'
                description: Customer requests to return unopened monitor, delivered 74 days ago. Specs not as expected.
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-20000001
              customer_id: CUS-20000001
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-20000001
              refund_amount: 599
              return_reason: not_as_expected
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: Return request - Samsung 32-inch Curved Gaming Monitor (ORD-20000001)
                priority: urgent
                assignee_id: '2'
                description: The item was delivered 74 days ago and remains unopened. The customer states the specifications do not meet their expectations and would like to proceed with a return.  A new return has been created for the monitor, and the customer has been informed that no restocking or return shipping fees apply. The expected refund amount is $599.00 once the item is received at the warehouse.
                requester_id: '6'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_025(x: TestContext, judge: Judge):
    """!
    query: Hi, I need help with returning the commercial air purifier I bought because it is not the size I ordered.
    user_context: |-
      Your Order_id: ORD-10000101

      email: [victoria.patterson@gmail.com](mailto:victoria.patterson@gmail.com)

      name: Victoria Patterson

      phone: +1-510-2921090

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '101550'
            name: Victoria Patterson
            email: victoria.patterson@gmail.com
            role: end-user
            phone: +1-510-2921090
            verified: true
            active: true
            created_at: '2022-03-15T10:00:00Z'
            updated_at: '2025-10-01T13:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000101
            customer_id: CUS-10000101
            order_date: '2025-07-10T14:30:00Z'
            status: delivered
            subtotal_amount: 549
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 549
            shipping_address_line1: 789 Business Park Dr
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000101
            order_id: ORD-10000101
            carrier: FedEx
            tracking_number: TRK-100000000101
            ship_date: '2025-07-11T09:00:00Z'
            estimated_delivery_date: '2025-07-13T17:00:00Z'
            actual_delivery_date: '2025-07-13T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000101
            order_id: ORD-10000101
            sku: APPL-4456
            product_name: Commercial Air Purifier Pro
            quantity: 1
            base_price: 549
            discount_amount: 0
            final_price: 549
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000101
            order_id: ORD-10000101
            customer_id: CUS-10000101
            amount: 549
            status: authorized
            payment_method: Visa ending in 8901
            transaction_date: '2025-07-10T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-4456
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Austin-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-4456
            name: Commercial Air Purifier Pro
            category: appliances
            brand: AirTech
            base_price: 549
            weight_lbs: 48
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000101
            email: victoria.patterson@gmail.com
            name: Victoria Patterson
            phone: +1-510-2921090
            registration_date: '2022-03-15T10:00:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 25
            customer_score: 38
            behavioral_segment: bonus_hunter
            acquisition_source: referral
            discount_usage_rate: 0.92
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: 'Return request: Commercial Air Purifier Pro wrong size'
                priority: urgent
                assignee_id: '2'
                description: Customer received the wrong size Commercial Air Purifier Pro and wants to return it. Order delivered 80 days ago. Item is opened. Customer is VIP tier.
                requester_id: '101550'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000101
              customer_id: CUS-10000101
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000101
              refund_amount: 549
              return_reason: wrong_item_received
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_026(x: TestContext, judge: Judge):
    """!
    query: Hi, I'm following up on my previous message about my washing machine order. I've decided I don't want it anymore and would like to return it before the installation happens.
    user_context: |-
      Rules:
      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      Order number: ORD-0200111

      Customer ID: CUS-12345678

      Email: [alex.johnson@example.com](mailto:alex.johnson@example.com)

      Item condition: unopened

      Installation status: scheduled but not completed

      Reason for return: changed mind
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6789'
            name: Alex Johnson
            email: alex.johnson@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0199
            verified: true
            active: true
            created_at: '2023-05-15T10:00:00Z'
            updated_at: '2023-05-15T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '1234'
            subject: Order modification request
            description: Customer asking about modifying their order ORD-0200111
            status: open
            priority: urgent
            type: incident
            requester_id: '6789'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-28T00:00:00Z'
            updated_at: '2025-09-28T00:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-0200111
            customer_id: CUS-12345678
            order_date: '2025-09-09T14:30:00Z'
            status: installation_scheduled
            subtotal_amount: 899
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1028
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: INST-001
          external_retail_toolset_oms_models_shipments:
          - id: SHP-0200111
            order_id: ORD-0200111
            carrier: FedEx
            tracking_number: TRK-200111000001
            ship_date: '2025-09-17T09:00:00Z'
            estimated_delivery_date: '2025-09-19T17:00:00Z'
            actual_delivery_date: '2025-09-19T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200111000001
            shipment_id: SHP-0200111
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-19T17:00:00Z'
            last_update: '2025-09-19T15:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-0200111
            order_id: ORD-0200111
            sku: SKU-APPL-2278
            product_name: Whirlpool Top-Load Washing Machine 4.3 cu ft
            quantity: 1
            base_price: 899
            discount_amount: 0
            final_price: 899
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-0200111
            order_id: ORD-0200111
            customer_id: CUS-12345678
            amount: 1028
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-09-09T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-0200111
            order_id: ORD-0200111
            sku: SKU-APPL-2278
            customer_id: CUS-12345678
            warranty_type: manufacturer
            start_date: '2025-09-19T00:00:00Z'
            end_date: '2028-09-19T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: INST-001
            order_id: ORD-0200111
            customer_id: CUS-12345678
            service_type: appliance_basic
            scheduled_date: '2025-10-03T10:00:00Z'
            technician_id: TECH-0078
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: SKU-APPL-2278
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: SKU-APPL-2278
            name: Whirlpool Top-Load Washing Machine 4.3 cu ft
            category: appliances
            brand: Whirlpool
            base_price: 899
            weight_lbs: 175
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-12345678
            email: alex.johnson@example.com
            name: Alex Johnson
            phone: +1-555-0199
            registration_date: '2023-05-15T10:00:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 31
            customer_score: 90
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: cancel_installation
            parameters:
              job_id: INST-001
              order_id: ORD-0200111
              cancellation_reason: customer_cancelled_order
          - tool: create_rma
            parameters:
              order_id: ORD-0200111
              customer_id: CUS-12345678
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-0200111
              refund_amount: 899
              return_reason: changed_mind
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '1234'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_028(x: TestContext, judge: Judge):
    """!
    query: 'Hi, I bought the Luxury Smartwatch Pro, order ORD-10000087) about three months ago and it''s been opened but barely used. I changed my mind and would like to return it. Can you help me with the return process? This is my email: [victoria.sterling@example.com](mailto:victoria.sterling@example.com).'
    user_context: |-
      —------

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      —------
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '87'
            name: Victoria Sterling
            email: victoria.sterling@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0187
            verified: true
            active: true
            created_at: '2022-03-15T10:00:00Z'
            updated_at: '2022-03-15T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000087
            customer_id: CUS-10000087
            order_date: '2025-07-08T14:30:00Z'
            status: delivered
            subtotal_amount: 599
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 599
            shipping_address_line1: 456 Luxury Lane
            shipping_address_city: Beverly Hills
            shipping_address_state: CA
            shipping_address_zip: '90210'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000087
            order_id: ORD-10000087
            carrier: FedEx
            tracking_number: TRK-100000000087
            ship_date: '2025-07-09T10:00:00Z'
            estimated_delivery_date: '2025-07-11T17:00:00Z'
            actual_delivery_date: '2025-07-11T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000087
            shipment_id: SHP-10000087
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-07-11T17:00:00Z'
            last_update: '2025-07-11T15:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000087
            order_id: ORD-10000087
            sku: WEAR-6612
            product_name: Luxury Smartwatch Pro
            quantity: 1
            base_price: 599
            discount_amount: 0
            final_price: 599
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000087
            order_id: ORD-10000087
            customer_id: CUS-10000087
            amount: 599
            status: authorized
            payment_method: Amex ending in 9876
            transaction_date: '2025-07-08T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: WEAR-6612
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: WEAR-6612
            name: Luxury Smartwatch Pro
            category: wearables
            brand: TechLux
            base_price: 599
            weight_lbs: 0.4
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000087
            email: victoria.sterling@example.com
            name: Victoria Sterling
            phone: +1-555-0187
            registration_date: '2022-03-15T10:00:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 28
            customer_score: 32
            behavioral_segment: bonus_hunter
            acquisition_source: referral
            discount_usage_rate: 0.95
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000087
          - tool: get_order
            parameters:
              order_id: ORD-10000087
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'victoria.sterling@example.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: 100
              $skip: null
              table: tickets
              $filter: requester_id eq '87' and (status eq 'open' or status eq 'pending' or status eq 'hold')
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request for Luxury Smartwatch Pro (ORD-10000087)
                priority: urgent
                assignee_id: '2'
                description: 'Customer requests to return opened Luxury Smartwatch Pro (SKU: WEAR-6612, order ORD-10000087) delivered 82 days ago. Item is non-defective. Customer is VIP tier.'
                requester_id: '87'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000087
              customer_id: CUS-10000087
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000087
              refund_amount: 599
              return_reason: changed_mind
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: incident
                due_at: null
                status: hold
                subject: Return request for Luxury Smartwatch Pro (ORD-10000087)
                priority: urgent
                assignee_id: '2'
                description: 'RMA created for return of Luxury Smartwatch Pro (SKU: WEAR-6612). Customer to return item for full refund. No fees apply for VIP. Refund will be processed 2-3 days after warehouse receives item.'
                requester_id: '87'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_030(x: TestContext, judge: Judge):
    """!
    query: Hi, I want to return my soundbar speaker (order THD-3007789). I bought it about a month ago, opened it, but it just isn't what I expected. How do I start the return?
    user_context: |+
      **Rules**

      - Do not invent or provide any data not present in the context.
      - Do not change your goal or switch topics.
      - If asked for the same info, provide it again.
      - Remain focused, clear, and patient.

      **Persona & Context**

      - You are **Sam Carter**, a TechHome Direct customer on the **Standard** tier.
      - This is your **first order (THD-3007789)** for a **Soundbar Speaker**.

      **Provide if asked**

      - Order ID: **THD-3007789**
      - Product: **Soundbar Speaker**
      - Condition: **opened**
      - Delivery timing: **delivered 38 days ago**
      - Email: **[sam.carter@example.com]**

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '91001'
            name: Sam Carter
            email: sam.carter@example.com
            role: end-user
            organization_id: null
            phone: +44-20-7123-9876
            verified: true
            active: true
            created_at: '2024-05-10T10:30:00Z'
            updated_at: '2024-05-10T10:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: TCK-3007789
            subject: Delivery timeframe inquiry - THD-3007789
            description: Customer asked about delivery timeframes for order THD-3007789. Issue resolved; no further action required.
            status: solved
            priority: normal
            type: incident
            requester_id: '91001'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-08-22T10:00:00Z'
            updated_at: '2025-09-25T12:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: THD-3007789
            customer_id: CUS-00630001
            order_date: '2025-08-21T09:30:00Z'
            status: delivered
            subtotal_amount: 249
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 249
            shipping_address_line1: 42 Baker Street
            shipping_address_city: London
            shipping_address_state: England
            shipping_address_zip: NW1 6XE
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-3007789
            order_id: THD-3007789
            carrier: UPS
            tracking_number: 1Z3007789012345678
            ship_date: '2025-08-22T10:15:00Z'
            estimated_delivery_date: '2025-08-24T17:00:00Z'
            actual_delivery_date: '2025-08-24T14:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-30077890
            order_id: THD-3007789
            sku: AUD-7789
            product_name: Soundbar Speaker
            quantity: 1
            base_price: 249
            discount_amount: 0
            final_price: 249
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-30077890
            order_id: THD-3007789
            customer_id: CUS-00630001
            amount: 249
            status: authorized
            payment_method: Visa ending in 5522
            transaction_date: '2025-08-21T09:35:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: AUD-7789
            available_quantity: 120
            reserved_quantity: 0
            warehouse_location: London-E14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: AUD-7789
            name: Soundbar Speaker
            category: audio_video
            brand: Sony
            base_price: 249
            weight_lbs: 6.8
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-00630001
            email: sam.carter@example.com
            name: Sam Carter
            phone: +44-20-7123-9876
            registration_date: '2025-08-01T10:00:00Z'
            customer_tier: standard
            lifetime_value: 249
            total_orders: 1
            customer_score: 21
            behavioral_segment: bonus_hunter
            acquisition_source: paid_search
            discount_usage_rate: 0
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request - Soundbar Speaker (THD-3007789)
                priority: normal
                assignee_id: '2'
                description: 'Customer requests to return opened soundbar speaker (SKU: AUD-7789) from order THD-3007789. Delivered 38 days ago. Standard tier, first-time buyer. Calculated refund: $240.01 (Restocking fee waived, $8.99 return shipping cost applies).'
                requester_id: '91001'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: THD-3007789
              customer_id: CUS-00630001
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-30077890
              refund_amount: 240.01
              return_reason: not_as_expected
              restocking_fee: 0
              return_shipping_cost: 8.99
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: RMA created for return of soundbar speaker. Customer provided prepaid return label ($8.99). Refund of $240.01 will be issued 7-10 business days after warehouse receives item.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_031(x: TestContext, judge: Judge):
    """!
    query: Hi, I'm Michael Rodriguez. I bought a Compact Countertop Dishwasher (order ORD-20000001) on 18 August 2025, and it was delivered and installed on 25 August 2025. I changed my mind and I would like to return it, I am still on the returning window of 60 days from the delivery date. The item is opened but not defective. You can apply any fee due. Can you help me with the return process?
    user_context: |-
      Rules for User Agent Behavior:

      - Do NOT invent any data, names, IDs, or details not present in the provided context.
      - Do NOT change the original goal or switch topics.
      - Remain focused, clear, and patient.
      - Provide all necessary unique data in the first message.
      - If asked for the same info multiple times, provide it again.
      - Do not introduce new requests or topics.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-03-15T10:00:00Z'
            updated_at: '2024-03-15T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-08-18T14:30:00Z'
            status: delivered
            subtotal_amount: 499
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 628
            shipping_address_line1: 789 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-20000001
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: FedEx
            tracking_number: TRK-200000000001
            ship_date: '2025-08-20T09:00:00Z'
            estimated_delivery_date: '2025-08-25T17:00:00Z'
            actual_delivery_date: '2025-08-25T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-08-25T17:00:00Z'
            last_update: '2025-08-25T15:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: APPL-3329
            product_name: Compact Countertop Dishwasher
            quantity: 1
            base_price: 499
            discount_amount: 0
            final_price: 499
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 628
            status: authorized
            payment_method: Visa ending in 7834
            transaction_date: '2025-08-18T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: APPL-3329
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-08-18T00:00:00Z'
            end_date: '2028-08-18T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            service_type: appliance_basic
            scheduled_date: '2025-08-25T10:00:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2025-08-25T14:30:00Z'
            workmanship_warranty_end: '2025-11-22T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-3329
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-3329
            name: Compact Countertop Dishwasher
            category: appliances
            brand: KitchenAid
            base_price: 499
            weight_lbs: 63
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2024-03-15T10:00:00Z'
            customer_tier: standard
            lifetime_value: 2450.75
            total_orders: 10
            customer_score: 55
            behavioral_segment: opportunist
            acquisition_source: organic_search
            discount_usage_rate: 0.72
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-20000001
          - tool: get_order
            parameters:
              order_id: ORD-20000001
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request for Compact Countertop Dishwasher (ORD-20000001)
                priority: normal
                assignee_id: '2'
                description: 'Customer requests to return opened Compact Countertop Dishwasher (SKU: APPL-3329), delivered and installed on 25 August 2025. Non-defective, within 60-day return window. Standard tier, restocking and removal fees apply.'
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-20000001
              customer_id: CUS-20000001
              removal_fee: 50
              is_defective: false
              line_item_id: LIN-20000001
              refund_amount: 374.15
              return_reason: changed_mind
              restocking_fee: 74.85
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_032(x: TestContext, judge: Judge):
    """!
    query: Hi, I want to return the Smart Washing Machine (order ORD-10000015) I bought. It's not what I expected.
    user_context: |-
      Rules:

      - Do not invent or provide any data not present in the provided context.
      - Do not change your goal or switch topics.
      - If asked for the same info, provide it again.
      - Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: null
            phone: +1-555-0156
            verified: true
            active: true
            created_at: '2023-08-15T14:30:00Z'
            updated_at: '2025-09-28T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '15'
            subject: Washing machine performance issues
            description: Customer reporting performance issues with Smart Washing Machine purchased 58 days ago
            status: open
            priority: normal
            type: incident
            requester_id: '15'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-28T10:00:00Z'
            updated_at: '2025-09-28T10:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-07-31T10:00:00Z'
            status: delivered
            subtotal_amount: 1099
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1228
            shipping_address_line1: 789 Oak Street
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '73301'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000015
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: FedEx
            tracking_number: TRK-100000000015
            ship_date: '2025-08-01T09:00:00Z'
            estimated_delivery_date: '2025-08-07T17:00:00Z'
            actual_delivery_date: '2025-08-07T13:15:00Z'
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: APPL-4492
            product_name: Smart Washing Machine
            quantity: 1
            base_price: 1099
            discount_amount: 0
            final_price: 1099
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            amount: 1228
            status: authorized
            payment_method: Visa ending in 7890
            transaction_date: '2025-07-31T10:05:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            service_type: appliance_basic
            scheduled_date: '2025-08-07T10:00:00Z'
            technician_id: TECH-0078
            status: completed
            completion_date: '2025-08-07T14:30:00Z'
            workmanship_warranty_end: '2025-11-05T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-4492
            name: Smart Washing Machine
            category: appliances
            brand: Samsung
            base_price: 1099
            weight_lbs: 215
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000015
            customer_id: CUS-10000015
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 2500
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0156
            registration_date: '2023-08-15T14:30:00Z'
            customer_tier: plus_member
            lifetime_value: 3250.75
            total_orders: 13
            customer_score: 35
            behavioral_segment: bonus_hunter
            acquisition_source: email_marketing
            discount_usage_rate: 0.92
        golden_test_case:
          tool_interactions:
          - tool: create_rma
            parameters:
              order_id: ORD-10000015
              customer_id: CUS-10000015
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000015
              refund_amount: 1099
              return_reason: not_as_expected
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '15'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: high
                assignee_id: null
                description: Customer wants to return Smart Washing Machine (order ORD-10000015) because product doesn't match expectations after installation.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_033(x: TestContext, judge: Judge):
    """!
    query: Hi, I need help returning my Samsung refrigerator with a bottom freezer, as it arrived in a different color than I ordered. The order number is ORD-20000001 and the installation service has been completed. Can you help me with the return process?
    user_context: |+
      Rules:
      Do not invent or provide any data that is not present in the provided context
      Do not change your goal or switch topics.
      If the agent asks again for the same information, provide it again.
      Remain focused, clear, and patient.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Victoria Chen
            email: victoria.chen@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2025-08-06T10:00:00Z'
            updated_at: '2025-08-06T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '6'
            subject: VIP membership benefits inquiry
            description: Customer inquiring about VIP tier benefits and perks
            status: solved
            priority: urgent
            type: incident
            requester_id: '6'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-29T10:00:00Z'
            updated_at: '2025-09-29T14:00:00Z'
            due_at: null
          - id: '7'
            subject: Return request - wrong refrigerator color received
            description: VIP customer received wrong color refrigerator and wants to return it. Order ORD-20000001 delivered 49 days ago with completed installation.
            status: open
            priority: urgent
            type: incident
            requester_id: '6'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-10-01T13:00:00Z'
            updated_at: '2025-10-01T13:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-08-06T14:30:00Z'
            status: delivered
            subtotal_amount: 2499
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 2628
            shipping_address_line1: 789 Oak Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-20000001
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: FedEx
            tracking_number: TRK-200000000001
            ship_date: '2025-08-08T09:00:00Z'
            estimated_delivery_date: '2025-08-13T17:00:00Z'
            actual_delivery_date: '2025-08-13T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: APPL-9923
            product_name: Samsung 22 cu ft Bottom-Freezer Refrigerator
            quantity: 1
            base_price: 2499
            discount_amount: 0
            final_price: 2499
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 2628
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-08-06T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            service_type: appliance_basic
            scheduled_date: '2025-08-13T10:00:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2025-08-13T15:30:00Z'
            workmanship_warranty_end: '2025-11-11T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-9923
            name: Samsung 22 cu ft Bottom-Freezer Refrigerator
            category: appliances
            brand: Samsung
            base_price: 2499
            weight_lbs: 298
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-20000001
            customer_id: CUS-20000001
            membership_type: vip
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 8500
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: victoria.chen@example.com
            name: Victoria Chen
            phone: +1-555-0198
            registration_date: '2025-08-06T10:00:00Z'
            customer_tier: vip
            lifetime_value: 2628
            total_orders: 1
            customer_score: 85
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: victoria.chen@example.com
              customer_id: null
          - tool: get_membership_details
            parameters:
              customer_id: CUS-20000001
          - tool: zendesk_get_item
            parameters:
              id: '7'
              table: tickets
          - tool: get_order
            parameters:
              order_id: ORD-20000001
          - tool: get_installation_job
            parameters:
              job_id: null
              order_id: ORD-20000001
          - tool: get_product_details
            parameters:
              sku: APPL-9923
          - tool: create_rma
            parameters:
              order_id: ORD-20000001
              customer_id: CUS-20000001
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-20000001
              refund_amount: 2499
              return_reason: wrong_item_received
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: incident
                due_at: null
                status: hold
                subject: null
                priority: urgent
                assignee_id: '2'
                description: null
                requester_id: '6'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_034(x: TestContext, judge: Judge):
    """!
    query: Hi, I bought the Handheld Gaming Console Pro about 27 days ago and received it 24 days ago. I’ve opened it, but it’s not what I expected based on the specifications. I saw on your website that gaming products have a 30-day return window, can I return it?
    user_context: |-
      Rules:
      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.


      You are Alex Johnson,

      - If the agent asks for the email, it's [alex.johnson@example.com](mailto:alex.johnson@example.com).
      - If the agent asks for the zip code, it's 78701
      - If the agent asks for the order ID, it's ORD-10000007
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Alex Johnson
            email: alex.johnson@example.com
            role: end-user
            organization_id: null
            phone: +1-555-0199
            verified: true
            active: true
            created_at: '2025-09-15T10:00:00Z'
            updated_at: '2025-09-15T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000007
            customer_id: CUS-10000007
            order_date: '2025-09-04T14:30:00Z'
            status: delivered
            subtotal_amount: 349
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 349
            shipping_address_line1: 789 Gaming Street
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000007
            order_id: ORD-10000007
            carrier: UPS
            tracking_number: TRK-100000000007
            ship_date: '2025-09-05T09:00:00Z'
            estimated_delivery_date: '2025-09-07T17:00:00Z'
            actual_delivery_date: '2025-09-07T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000007
            order_id: ORD-10000007
            sku: GAME-2287
            product_name: Handheld Gaming Console Pro
            quantity: 1
            base_price: 349
            discount_amount: 0
            final_price: 349
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000007
            order_id: ORD-10000007
            customer_id: CUS-10000007
            amount: 349
            status: authorized
            payment_method: Visa ending in 7890
            transaction_date: '2025-09-04T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products:
          - sku: GAME-2287
            name: Handheld Gaming Console Pro
            category: gaming
            brand: GameTech
            base_price: 349
            weight_lbs: 1.4
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000007
            email: alex.johnson@example.com
            name: Alex Johnson
            phone: +1-555-0199
            registration_date: '2025-09-15T10:00:00Z'
            customer_tier: standard
            lifetime_value: 1850.75
            total_orders: 7
            customer_score: 61
            behavioral_segment: opportunist
            acquisition_source: paid_search
            discount_usage_rate: 0.72
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request for Handheld Gaming Console Pro (ORD-10000007)
                priority: normal
                assignee_id: '2'
                description: 'Customer requests to return opened Handheld Gaming Console Pro (SKU: GAME-2287, order ORD-10000007) as it is not as expected. Delivered 24 days ago, within 30-day return window. Item is opened, non-defective.'
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000007
              customer_id: CUS-10000007
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000007
              refund_amount: 287.66
              return_reason: not_as_expected
              restocking_fee: 52.35
              return_shipping_cost: 8.99
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_037(x: TestContext, judge: Judge):
    """!
    query: Hi, I'd like to return my Meta Quest 3 VR Gaming Headset (order THD-2009876). It's unopened and just not what I expected. How do I proceed?
    user_context: |2+


      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '9100'
            name: Alex Harris
            email: alex.harris@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2025-09-12T14:30:00Z'
            updated_at: '2025-09-12T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '10'
            subject: Question about return policy for unopened VR headset
            description: Customer asked about return policies and procedures for unopened items 2 days ago; no RMA created yet.
            status: open
            priority: normal
            type: incident
            requester_id: '9100'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-29T13:00:00Z'
            updated_at: '2025-09-29T13:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: THD-2009876
            customer_id: CUS-00010023
            order_date: '2025-09-12T15:45:00Z'
            status: delivered
            subtotal_amount: 549
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 549
            shipping_address_line1: 789 Maple Drive
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20009876
            order_id: THD-2009876
            carrier: UPS
            tracking_number: TRK-200000009876
            ship_date: '2025-09-13T09:30:00Z'
            estimated_delivery_date: '2025-09-14T17:00:00Z'
            actual_delivery_date: '2025-09-14T15:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000009876
            shipment_id: SHP-20009876
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-14T17:00:00Z'
            last_update: '2025-09-14T15:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: '1'
            order_id: THD-2009876
            sku: GAME-8867
            product_name: Meta Quest 3 VR Gaming Headset
            quantity: 1
            base_price: 549
            discount_amount: 0
            final_price: 549
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20009876
            order_id: THD-2009876
            customer_id: CUS-00010023
            amount: 549
            status: authorized
            payment_method: Visa ending in 7834
            transaction_date: '2025-09-12T15:45:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20009876
            order_id: THD-2009876
            sku: GAME-8867
            customer_id: CUS-00010023
            warranty_type: manufacturer
            start_date: '2025-09-14T00:00:00Z'
            end_date: '2026-09-14T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for 1 year from delivery date
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: GAME-8867
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: GAME-8867
            name: Meta Quest 3 VR Gaming Headset
            category: gaming
            brand: Meta
            base_price: 549
            weight_lbs: 1.8
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-00010023
            email: alex.harris@example.com
            name: Alex Harris
            phone: +1-555-0198
            registration_date: '2025-09-12T14:30:00Z'
            customer_tier: standard
            lifetime_value: 549
            total_orders: 1
            customer_score: 53
            behavioral_segment: opportunist
            acquisition_source: social_media
            discount_usage_rate: 0
        golden_test_case:
          tool_interactions:
          - tool: create_rma
            parameters:
              order_id: THD-2009876
              customer_id: CUS-00010023
              removal_fee: 0
              is_defective: false
              line_item_id: '1'
              refund_amount: 540.01
              return_reason: not_as_expected
              restocking_fee: 0
              return_shipping_cost: 8.99
          - tool: zendesk_update_item
            parameters:
              id: '10'
              item:
                tags: null
                type: incident
                due_at: null
                status: hold
                subject: Return request – Meta Quest 3 VR Headset (GAME-8867)
                priority: normal
                assignee_id: '2'
                description: Customer returning unopened Meta Quest 3 VR Headset. Standard tier → 30-day gaming wearables window. First order → restocking fee waived. Return shipping fee $8.99 applies. RMA created with refund $540.01. Customer will receive prepaid label and refund after warehouse receipt.
                requester_id: '9100'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_039(x: TestContext, judge: Judge):
    """!
    query: Hi, I bought a 12-inch Premium Tablet Pro (order ORD-10000087) about 76 days ago and it was delivered 73 days ago. I opened it but haven't used it much. I changed my mind and would like to return it. Can you help me with the return process?
    user_context: |-
      - If the agent asks for the order ID, it's ORD-10000087.
      - If the agent asks for the email, it's [victoria.sterling@example.com](mailto:victoria.sterling@example.com).



      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '187'
            name: Victoria Sterling
            email: victoria.sterling@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0187
            verified: true
            active: true
            created_at: '2022-08-15T14:30:00Z'
            updated_at: '2022-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000087
            customer_id: CUS-10000087
            order_date: '2025-07-17T10:15:00Z'
            status: delivered
            subtotal_amount: 899
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 899
            shipping_address_line1: 2847 Maple Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000087
            order_id: ORD-10000087
            carrier: UPS
            tracking_number: TRK-100000000087
            ship_date: '2025-07-18T09:30:00Z'
            estimated_delivery_date: '2025-07-20T17:00:00Z'
            actual_delivery_date: '2025-07-19T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000087
            shipment_id: SHP-10000087
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-07-20T17:00:00Z'
            last_update: '2025-07-19T15:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000087
            order_id: ORD-10000087
            sku: TAB-9912
            product_name: 12-inch Premium Tablet Pro
            quantity: 1
            base_price: 899
            discount_amount: 0
            final_price: 899
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000087
            order_id: ORD-10000087
            customer_id: CUS-10000087
            amount: 899
            status: authorized
            payment_method: Visa ending in 8734
            transaction_date: '2025-07-17T10:15:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: TAB-9912
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: TAB-9912
            name: 12-inch Premium Tablet Pro
            category: computing
            brand: TechPro
            base_price: 899
            weight_lbs: 1.5
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000087
            email: victoria.sterling@example.com
            name: Victoria Sterling
            phone: +1-555-0187
            registration_date: '2022-08-15T14:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 21
            customer_score: 34
            behavioral_segment: bonus_hunter
            acquisition_source: referral
            discount_usage_rate: 0.92
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000087
          - tool: get_order
            parameters:
              order_id: ORD-10000087
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'victoria.sterling@example.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '187' and status ne 'closed' and status ne 'solved'
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request for 12-inch Premium Tablet Pro (ORD-10000087)
                priority: urgent
                assignee_id: '2'
                description: 'Customer requests to return opened 12-inch Premium Tablet Pro (SKU: TAB-9912, order ORD-10000087) delivered 73 days ago. Customer is VIP tier.'
                requester_id: '187'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000087
              customer_id: CUS-10000087
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000087
              refund_amount: 899
              return_reason: changed_mind
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_040(x: TestContext, judge: Judge):
    """!
    query: Hi, this is Alen James. I bought a large portable air conditioner from you a little over a month ago – the 12000 BTU floor unit that’s around 60 pounds, shipped to my home in Nashville. It was delivered and I’ve never opened the actual product box; the unit is still sealed inside the packaging. After looking more closely at the specs and measuring my space, I’ve realized it’s not really what I expected and it’s going to be too much for the room I wanted to cool, so I’d like to return it unopened. I don’t have the order number in front of me, but it’s the only portable AC I’ve ordered with this email address. Can you help me start a return for this unopened unit and explain exactly what, if any, fees I’d be charged, especially for shipping something this heavy and any restocking charges?
    user_context: |-
      You are:

      Name: Alen James

      Email: [alen.james@email.com](mailto:alen.james@email.com)

      Phone: +1-555-0198

      Order ID, say: ORD-2001
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Alen James
            email: alen.james@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-02-10T14:30:00Z'
            updated_at: '2024-02-10T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: TKT-5001
            subject: Return policy inquiry for heavy unopened item
            description: Customer inquiry about return policy for a heavy unopened portable air conditioner
            status: open
            priority: normal
            type: incident
            requester_id: '6'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-30T13:00:00Z'
            updated_at: '2025-09-30T13:00:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 23118465221921
            ticket_id: 5001
            author_id: 6
            body: Customer inquiry about return policy for a heavy unopened portable air conditioner
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">Customer inquiry about return policy for a heavy unopened portable air conditioner</p></div>
            public: true
            created_at: '2025-09-30T13:00:00Z'
            ItemInternalId: 623d7175-2bb9-41d9-9131-d5f2e57af9fc
            key: '23118465221921'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-2001
            customer_id: CUS-1001
            order_date: '2025-08-19T10:15:00Z'
            status: delivered
            subtotal_amount: 449
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 15
            total_amount: 464
            shipping_address_line1: 789 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-2001
            order_id: ORD-2001
            carrier: UPS
            tracking_number: TRK-200000000001
            ship_date: '2025-08-19T09:30:00Z'
            estimated_delivery_date: '2025-08-22T17:00:00Z'
            actual_delivery_date: '2025-08-22T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-2001
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-08-22T17:00:00Z'
            last_update: '2025-08-22T15:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-2001
            order_id: ORD-2001
            sku: APPL-3398
            product_name: Portable Air Conditioner 12000 BTU
            quantity: 1
            base_price: 449
            discount_amount: 0
            final_price: 449
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-2001
            order_id: ORD-2001
            customer_id: CUS-1001
            amount: 464
            status: authorized
            payment_method: Visa ending in 7892
            transaction_date: '2025-08-18T10:15:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-3398
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-3398
            name: Portable Air Conditioner 12000 BTU
            category: appliances
            brand: CoolBreeze
            base_price: 449
            weight_lbs: 61
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-1001
            email: alen.james@email.com
            name: Alen James
            phone: +1-555-0198
            registration_date: '2024-02-10T14:30:00Z'
            customer_tier: standard
            lifetime_value: 3850.75
            total_orders: 9
            customer_score: 88
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: get_order
            parameters:
              order_id: ORD-2001
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-1001
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              locale: null
              $filter: email eq 'alen.james@email.com'
              $select: null
              section: null
              $orderby: null
              brand_id: null
              category: null
              multibrand: null
              label_names: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '6' and status in ('open', 'pending', 'hold')
              $select: null
              $orderby: null
          - tool: zendesk_search_articles
            parameters:
              query: Return Windows by Customer Tier and Restocking Fees and Return Shipping Costs
              locale: null
              section: null
              brand_id: null
              category: null
              multibrand: null
              label_names: null
          - tool: create_rma
            parameters:
              order_id: ORD-2001
              customer_id: CUS-1001
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-2001
              refund_amount: 449
              return_reason: not_as_expected
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: TKT-5001
              item:
                tags: null
                type: incident
                due_at: null
                status: hold
                subject: Return of unopened portable air conditioner (ORD-2001)
                priority: normal
                assignee_id: '2'
                description: Customer Alen James requested return of unopened portable air conditioner (SKU APPL-3398) from order ORD-2001, delivered 40 days ago. Verified Standard tier within 60-day return window, item unopened and non-defective, heavy item >30 lbs. Created RMA for line item LIN-2001 with refund_amount 449.00, no restocking fee, no return shipping cost, no removal fee. Customer instructed to use prepaid label; refund to be issued 7–10 days after warehouse receives the unit.
                requester_id: '6'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_041(x: TestContext, judge: Judge):
    """!
    query: |+
      I bought an induction cooktop about a month ago and it was delivered. Installation is scheduled in a few days, but I've changed my mind and want to return it before the install. Can you help?

    user_context: |-
      Rules:

      - Do not invent or provide any data not present in the provided context.
      - Do not change your goal or switch topics.
      - If asked for the same info, provide it again.
      - Remain focused, clear, and patient.

      If asked for additional information, you may provide:

      - - Identity: Name Casey Lee, email [casey.lee@example.com](mailto:casey.lee@example.com), phone +1-555-2210.
      - - Order: ORD-88041; induction cooktop ordered ~32 days ago, delivered ~22 days ago; installation was scheduled; no defects.
      - - Item unopened, just changed my mind and prefer to return.
      - - Installation: Job scheduled ~4 days from now; not started; OK to cancel the appointment.
      - - Plus client; expects free return shipping and no fees.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10012'
            name: Casey Lee
            email: casey.lee@example.com
            role: end-user
            organization_id: null
            phone: +1-555-2210
            verified: true
            active: true
            created_at: '2025-04-15T00:00:00Z'
            updated_at: '2025-04-15T00:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '6'
            subject: Delivery timeframe question
            description: Customer asked about delivery timing for a different prior order; issue resolved.
            status: solved
            priority: normal
            type: question
            requester_id: '10012'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-24T12:00:00Z'
            updated_at: '2025-09-28T12:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-88041
            customer_id: CUS-88041
            order_date: '2025-08-30T13:00:00Z'
            status: installation_scheduled
            subtotal_amount: 899
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1028
            shipping_address_line1: 321 Birch St
            shipping_address_city: Denver
            shipping_address_state: CO
            shipping_address_zip: '80203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: INST-88041
          external_retail_toolset_oms_models_shipments:
          - id: SH-88041-001
            order_id: ORD-88041
            carrier: FedEx
            tracking_number: FDX88041001
            ship_date: '2025-09-02T08:00:00Z'
            estimated_delivery_date: '2025-09-09T17:00:00Z'
            actual_delivery_date: '2025-09-09T13:00:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: FDX88041001
            shipment_id: SH-88041-001
            carrier: FedEx
            status: delivered
            current_location: Denver, CO
            estimated_delivery: '2025-09-09T17:00:00Z'
            last_update: '2025-09-09T13:00:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LI-88041-001
            order_id: ORD-88041
            sku: APPL-5576
            product_name: Induction cooktop
            quantity: 1
            base_price: 899
            discount_amount: 0
            final_price: 899
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-88041-001
            order_id: ORD-88041
            customer_id: CUS-88041
            amount: 899
            status: authorized
            payment_method: Visa ending in 4555
            transaction_date: '2025-08-30T13:00:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-88041
            order_id: ORD-88041
            sku: APPL-5576
            customer_id: CUS-88041
            warranty_type: manufacturer
            start_date: '2025-09-09T00:00:00Z'
            end_date: '2028-09-09T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: INST-88041
            order_id: ORD-88041
            customer_id: CUS-88041
            service_type: appliance_basic
            scheduled_date: '2025-10-05T13:00:00Z'
            technician_id: TECH-0078
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-5576
            available_quantity: 8
            reserved_quantity: 2
            warehouse_location: Denver-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-5576
            name: Induction cooktop
            category: appliances
            brand: TechHome
            base_price: 899
            weight_lbs: 44
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-88041
            customer_id: CUS-88041
            membership_type: plus
            start_date: '2025-04-15T00:00:00Z'
            end_date: '2026-04-15T00:00:00Z'
            status: active
            points_balance: 1420
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-88041
            email: casey.lee@example.com
            name: Casey Lee
            phone: +1-555-2210
            registration_date: '2025-04-15T00:00:00Z'
            customer_tier: plus_member
            lifetime_value: 9875
            total_orders: 12
            customer_score: 44
            behavioral_segment: opportunist
            acquisition_source: organic_search
            discount_usage_rate: 0.75
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: 'Return request for Professional Induction Cooktop '
                priority: high
                assignee_id: '2'
                description: Customer requests to return unopened induction cooktop delivered 22 days ago, installation not completed.
                requester_id: '10012'
                organization_id: null
              table: tickets
          - tool: cancel_installation
            parameters:
              job_id: INST-88041
              order_id: ORD-88041
              cancellation_reason: customer_cancelled_order
          - tool: create_rma
            parameters:
              order_id: ORD-88041
              customer_id: CUS-88041
              removal_fee: 0
              is_defective: false
              line_item_id: LI-88041-001
              refund_amount: 899
              return_reason: changed_mind
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: high
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_042(x: TestContext, judge: Judge):
    """!
    query: Hi, I recently bought a High-Performance Desktop Computer from you, order number ORD-20000001. It was delivered 18 days ago, but I haven't opened it because I decided to get a different model. Can I return this unopened computer for a refund?
    user_context: |+
      **Rules:**

      - Do not invent or provide any data not present in the provided context.
      - Do not change your goal or switch topics.
      - Remain focused, clear, and patient.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: null
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2025-09-10T14:30:00Z'
            updated_at: '2025-09-10T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-09-10T15:00:00Z'
            status: delivered
            subtotal_amount: 2199
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 15
            total_amount: 2214
            shipping_address_line1: 742 Oak Street
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: UPS
            tracking_number: TRK-200000000001
            ship_date: '2025-09-11T09:30:00Z'
            estimated_delivery_date: '2025-09-13T17:00:00Z'
            actual_delivery_date: '2025-09-13T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-13T17:00:00Z'
            last_update: '2025-09-13T15:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: COMP-8821
            product_name: High-Performance Desktop Computer
            quantity: 1
            base_price: 2199
            discount_amount: 0
            final_price: 2199
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 2214
            status: authorized
            payment_method: Visa ending in 7892
            transaction_date: '2025-09-10T15:00:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: COMP-8821
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-09-13T00:00:00Z'
            end_date: '2026-09-13T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: COMP-8821
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: COMP-8821
            name: High-Performance Desktop Computer
            category: computing
            brand: TechBuild
            base_price: 2199
            weight_lbs: 18.3
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2025-09-10T14:30:00Z'
            customer_tier: standard
            lifetime_value: 2199
            total_orders: 1
            customer_score: 69
            behavioral_segment: opportunist
            acquisition_source: organic_search
            discount_usage_rate: 0
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: 'Return request: High-Performance Desktop Computer (COMP-8821)'
                priority: normal
                assignee_id: '2'
                description: 'Customer requests to return unopened desktop computer (SKU: COMP-8821) delivered 18 days ago. Wants to purchase a different model.'
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-20000001
              customer_id: CUS-20000001
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-20000001
              refund_amount: 2190.01
              return_reason: changed_mind
              restocking_fee: 0
              return_shipping_cost: 8.99
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: Customer requested return of High-Performance Desktop Computer (ORD-20000001). Item is unopened. First-time customer restocking fee waiver applied. Return shipping fee of $8.99 deducted. Final refund $2190.01. RMA created.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_043(x: TestContext, judge: Judge):
    """!
    query: |-
      Hi,
      I asked a few days ago about cancelling before installation. My treadmill delivery was last week and the install is tomorrow. Please cancel it and start the return.
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      If asked for additional information, you may provide:

      - Identity: Name Morgan Lee, email [morgan.lee@example.com](mailto:morgan.lee@example.com), phone +1-555-4429.
      - Order: ORD-88043; commercial treadmill ordered ~19 days ago, delivered ~9 days ago; item is unopened.
      - Installation: Job scheduled for tomorrow; not started; okay to cancel.
      - Membership: VIP; expects free returns and no fees.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10043'
            name: Morgan Lee
            email: morgan.lee@example.com
            role: end-user
            organization_id: null
            phone: +1-555-4429
            verified: true
            active: true
            created_at: '2025-09-01T10:00:00Z'
            updated_at: '2025-09-01T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '14'
            subject: Question about cancelling before installation
            description: Customer asked how to cancel orders before installation; awaiting follow-up.
            status: open
            priority: urgent
            type: incident
            requester_id: '10043'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-28T12:00:00Z'
            updated_at: '2025-09-28T12:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-88043
            customer_id: CUS-88043
            order_date: '2025-09-12T13:00:00Z'
            status: installation_scheduled
            subtotal_amount: 1899
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 2028
            shipping_address_line1: 555 Harbor Way
            shipping_address_city: Seattle
            shipping_address_state: WA
            shipping_address_zip: '98101'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: INST-88043
          external_retail_toolset_oms_models_shipments:
          - id: SH-88043-001
            order_id: ORD-88043
            carrier: FedEx
            tracking_number: FDX88043001
            ship_date: '2025-09-18T09:00:00Z'
            estimated_delivery_date: '2025-09-22T17:00:00Z'
            actual_delivery_date: '2025-09-22T13:00:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: FDX88043001
            shipment_id: SH-88043-001
            carrier: FedEx
            status: delivered
            current_location: Seattle, WA
            estimated_delivery: '2025-09-22T17:00:00Z'
            last_update: '2025-09-22T13:00:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LI-88043-001
            order_id: ORD-88043
            sku: GAME-4429
            product_name: Commercial treadmill
            quantity: 1
            base_price: 1899
            discount_amount: 0
            final_price: 1899
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-88043-001
            order_id: ORD-88043
            customer_id: CUS-88043
            amount: 1899
            status: authorized
            payment_method: Visa ending in 7788
            transaction_date: '2025-09-12T13:00:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: INST-88043
            order_id: ORD-88043
            customer_id: CUS-88043
            service_type: appliance_basic
            scheduled_date: '2025-10-02T13:00:00Z'
            technician_id: null
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: GAME-4429
            available_quantity: 12
            reserved_quantity: 1
            warehouse_location: Seattle-G15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: GAME-4429
            name: Commercial treadmill
            category: gaming
            brand: TechHome
            base_price: 1899
            weight_lbs: 245
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-88043
            customer_id: CUS-88043
            membership_type: vip
            start_date: '2025-01-15T00:00:00Z'
            end_date: '2026-01-15T00:00:00Z'
            status: active
            points_balance: 3250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-88043
            email: morgan.lee@example.com
            name: Morgan Lee
            phone: +1-555-4429
            registration_date: '2023-05-15T14:30:00Z'
            customer_tier: vip
            lifetime_value: 51250
            total_orders: 27
            customer_score: 26
            behavioral_segment: bonus_hunter
            acquisition_source: referral
            discount_usage_rate: 0.95
        golden_test_case:
          tool_interactions:
          - tool: cancel_installation
            parameters:
              job_id: INST-88043
              order_id: ORD-88043
              cancellation_reason: customer_cancelled_order
          - tool: create_rma
            parameters:
              order_id: ORD-88043
              customer_id: CUS-88043
              removal_fee: 0
              is_defective: false
              line_item_id: LI-88043-001
              refund_amount: 1899
              return_reason: changed_mind
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '14'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: urgent
                assignee_id: null
                description: Cancelled installation job INST-88043 (customer_cancelled_order) before scheduled date; created RMA for ORD-88043 line LI-88043-001, refund $1,899.00 (no restocking/return shipping/removal fees). Ticket on hold pending return and refund completion.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_044(x: TestContext, judge: Judge):
    """!
    query: Hi, I bought a Gaming Racing Simulator Chair from you a few weeks ago, and after trying it out for a bit, I realized it’s not as comfortable as I hoped. Can you help me return it?
    user_context: |-
      When asked, you must provide:

      • Your order number: **ORD-10000015**
      • Your email: **[michael.rodriguez@email.com]**

      Rules:

      - Do **not** invent or provide any data not present in the provided context.
      - Do **not** change your goal or switch topics.
      - If asked for the same info, provide it **again** consistently.
      - Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-02-10T09:30:00Z'
            updated_at: '2024-02-10T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '15'
            subject: TechHome Plus membership inquiry
            description: Customer asking about Plus membership benefits and pricing
            status: solved
            priority: low
            type: incident
            requester_id: '15'
            assignee_id: '2'
            created_at: '2025-09-26T10:00:00Z'
            updated_at: '2025-09-26T16:30:00Z'
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-09-07T14:30:00Z'
            status: delivered
            subtotal_amount: 899
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 899
            shipping_address_line1: 789 Oak Street
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '73301'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: FedEx
            tracking_number: TRK-100000000015
            ship_date: '2025-09-08T09:00:00Z'
            estimated_delivery_date: '2025-09-10T17:00:00Z'
            actual_delivery_date: '2025-09-10T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: GAME-7712
            product_name: Gaming Racing Simulator Chair
            quantity: 1
            base_price: 899
            discount_amount: 0
            final_price: 899
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            amount: 899
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2025-09-07T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: GAME-7712
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: GAME-7712
            name: Gaming Racing Simulator Chair
            category: gaming
            brand: RaceMax
            base_price: 899
            weight_lbs: 67
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2024-02-10T09:30:00Z'
            customer_tier: standard
            lifetime_value: 2850.75
            total_orders: 8
            customer_score: 63
            behavioral_segment: opportunist
            acquisition_source: social_media
            discount_usage_rate: 0.72
        golden_test_case:
          tool_interactions:
          - tool: get_order
            parameters:
              order_id: ORD-10000015
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000015
          - tool: zendesk_get_item
            parameters:
              id: '15'
              table: users
          - tool: zendesk_get_items
            parameters:
              $top: 10
              $skip: 0
              table: tickets
              $filter: requester_id eq '15'
              $select: id,subject,status,priority
              $orderby: created_at desc
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: 'Return request: Gaming Racing Simulator Chair not as expected'
                priority: normal
                assignee_id: '2'
                description: 'Customer requests to return opened Gaming Racing Simulator Chair (SKU: GAME-7712) delivered on 2025-09-10. Reason: not as comfortable as expected. Item is non-defective, opened, and weighs 67 lbs. No installation involved.'
                requester_id: '15'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000015
              customer_id: CUS-10000015
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000015
              refund_amount: 764.15
              return_reason: not_as_expected
              restocking_fee: 134.85
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_045(x: TestContext, judge: Judge):
    """!
    query: Hi, I'd like to return the freezer from order ORD-10000010. I know it's been over two months and I'm probably past your return deadline, but I haven't even opened the box. Can you please make an exception and allow me to return it?
    user_context: |+
      **Rules:**

      **Do not invent or provide any data not present in the provided context.**

      **Do not change your goal or switch topics.**

      **If asked for the same info, provide it again.**

      **Remain focused, clear, and patient.**

      You are Michael Rodriguez (customer_id = CUS-10000010), a TechHome Plus member. You purchased a stand-alone freezer (Order ORD-10000010) recently.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0190
            verified: true
            active: true
            created_at: '2023-05-12T09:30:00Z'
            updated_at: '2025-07-20T10:15:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000010
            customer_id: CUS-10000010
            order_date: '2025-07-25T11:45:00Z'
            status: delivered
            subtotal_amount: 799
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 799
            shipping_address_line1: 2847 Oak Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000010
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000010
            order_id: ORD-10000010
            carrier: FedEx
            tracking_number: TRK-100000000010
            ship_date: '2025-07-30T09:15:00Z'
            estimated_delivery_date: '2025-08-01T17:00:00Z'
            actual_delivery_date: '2025-08-01T13:20:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000010
            shipment_id: SHP-10000010
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-08-01T17:00:00Z'
            last_update: '2025-08-01T13:20:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000010
            order_id: ORD-10000010
            sku: APPL-6687
            product_name: Frigidaire 20 cu ft Upright Freezer
            quantity: 1
            base_price: 799
            discount_amount: 0
            final_price: 799
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000010
            order_id: ORD-10000010
            customer_id: CUS-10000010
            amount: 799
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2025-07-25T11:45:15Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000010
            order_id: ORD-10000010
            sku: APPL-6687
            customer_id: CUS-10000010
            warranty_type: manufacturer
            start_date: '2025-08-01T00:00:00Z'
            end_date: '2028-08-01T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000010
            order_id: ORD-10000010
            customer_id: CUS-10000010
            service_type: appliance_basic
            scheduled_date: '2025-08-01T14:00:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2025-08-01T14:30:00Z'
            workmanship_warranty_end: '2025-10-30T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-6687
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-6687
            name: Frigidaire 20 cu ft Upright Freezer
            category: appliances
            brand: Frigidaire
            base_price: 799
            weight_lbs: 176
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000010
            customer_id: CUS-10000010
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 1250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0190
            registration_date: '2023-05-12T09:30:00Z'
            customer_tier: plus_member
            lifetime_value: 3850.75
            total_orders: 19
            customer_score: 37
            behavioral_segment: opportunist
            acquisition_source: email_marketing
            discount_usage_rate: 0.78
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request for stand-alone freezer (ORD-10000010)
                priority: high
                assignee_id: '2'
                description: 'Customer requests to return unopened Frigidaire 15.6 cu ft Upright Freezer (SKU: APPL-6687, order ORD-10000010, delivered 61 days ago, installation completed, item unopened, Plus member)'
                requester_id: '10'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000010
              customer_id: CUS-10000010
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000010
              refund_amount: 799
              return_reason: changed_mind
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_047(x: TestContext, judge: Judge):
    """!
    query: I received the wrong model of Sony Noise Canceling earbuds in my order ORD-10000087, which was delivered 78 days ago. I want to return it. Can you help me with the return process?
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '87'
            name: Michael Rodriguez
            email: michael.rodriguez@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0187
            verified: true
            active: true
            created_at: '2021-03-15T10:30:00Z'
            updated_at: '2021-03-15T10:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '87'
            subject: Warranty coverage question for laptop
            description: Customer inquiring about warranty coverage for their laptop purchase
            status: solved
            priority: normal
            type: incident
            requester_id: '87'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-23T10:00:00Z'
            updated_at: '2025-09-27T14:30:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 23118465221987
            ticket_id: 87
            author_id: 87
            body: Customer inquiring about warranty coverage for their laptop purchase
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">Customer inquiring about warranty coverage for their laptop purchase</p></div>
            public: true
            created_at: '2025-09-23T10:00:00Z'
            ItemInternalId: 987d7175-2bb9-41d9-9131-d5f2e57af9f7
            key: '23118465221987'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000087
            customer_id: CUS-10000087
            order_date: '2025-07-12T15:30:00Z'
            status: delivered
            subtotal_amount: 249
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 249
            shipping_address_line1: 789 Oak Boulevard
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000087
            order_id: ORD-10000087
            carrier: UPS
            tracking_number: TRK-100000000087
            ship_date: '2025-07-13T09:15:00Z'
            estimated_delivery_date: '2025-07-15T17:00:00Z'
            actual_delivery_date: '2025-07-15T14:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000087
            shipment_id: SHP-10000087
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-07-15T17:00:00Z'
            last_update: '2025-07-15T14:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000087
            order_id: ORD-10000087
            sku: AUD-3392
            product_name: Sony Noise Canceling earbuds
            quantity: 1
            base_price: 249
            discount_amount: 0
            final_price: 249
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000087
            order_id: ORD-10000087
            customer_id: CUS-10000087
            amount: 249
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-07-12T15:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000087
            order_id: ORD-10000087
            sku: AUD-3392
            customer_id: CUS-10000087
            warranty_type: manufacturer
            start_date: '2025-07-15T00:00:00Z'
            end_date: '2026-07-15T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: AUD-3392
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: AUD-3392
            name: Sony Noise Canceling earbuds
            category: audio_video
            brand: Sony
            base_price: 249
            weight_lbs: 0.4
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000087
            email: michael.rodriguez@example.com
            name: Michael Rodriguez
            phone: +1-555-0187
            registration_date: '2021-03-15T10:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 33
            customer_score: 23
            behavioral_segment: bonus_hunter
            acquisition_source: referral
            discount_usage_rate: 0.95
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: 'Return request: wrong model received for order ORD-10000087'
                priority: urgent
                assignee_id: '2'
                description: 'Customer claims they received the wrong model of Sony Noise Canceling earbuds (SKU: AUD-3392) in order ORD-10000087, delivered 78 days ago. Item is opened, not defective. Customer is VIP tier.'
                requester_id: '87'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000087
              customer_id: CUS-10000087
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000087
              refund_amount: 249
              return_reason: wrong_item_received
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: 'RMA created for return of Sony Noise Canceling earbuds (SKU: AUD-3392) from order ORD-10000087. Awaiting customer shipment.'
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST006_049(x: TestContext, judge: Judge):
    """!
    query: Hi, I need help returning my VR Gaming Bundle with Room Setup, the order id is ORD-10000015. The system is not what I expected, and the installation service was completed. Can you assist me with the return process?
    user_context: |-
      You are Michael Chen, email [michael.chen@example.com](mailto:michael.chen@example.com), a Plus-tier customer.



      Main Scenario Steps:

      - Send the initial query, providing all relevant data.

      - If the agent asks for the same information again, provide it again as requested.

      - If the agent provides the expected behavior, thank them.



      Rules for User Agent Behavior:

      - Do NOT invent any data, names, IDs, or details not present in the provided context.

      - Do NOT change the original goal or switch topics.

      - Remain focused, clear, and patient.

      - Provide all necessary unique data in the first message.

      - If asked for the same info multiple times, provide it again.

      - Do not introduce new requests or topics.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Michael Chen
            email: michael.chen@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0156
            verified: true
            active: true
            created_at: '2023-05-12T14:20:00Z'
            updated_at: '2025-09-30T12:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '15'
            subject: Return inquiry for VR gaming bundle with installation
            description: Customer asking about returning items with completed installation services
            status: open
            priority: normal
            type: incident
            requester_id: '15'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-30T13:00:00Z'
            updated_at: '2025-09-30T13:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-07-19T10:30:00Z'
            status: delivered
            subtotal_amount: 699
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 828
            shipping_address_line1: 789 Gaming Street
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '73301'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000015
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: UPS
            tracking_number: TRK-100000000015
            ship_date: '2025-07-21T10:30:00Z'
            estimated_delivery_date: '2025-07-26T17:00:00Z'
            actual_delivery_date: '2025-07-26T14:32:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000015
            shipment_id: SHP-10000015
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-07-26T17:00:00Z'
            last_update: '2025-07-26T14:32:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: GAME-3357
            product_name: VR Gaming Bundle with Room Setup
            quantity: 1
            base_price: 699
            discount_amount: 0
            final_price: 699
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions: []
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            service_type: appliance_basic
            scheduled_date: '2025-07-26T14:00:00Z'
            technician_id: TECH-0078
            status: completed
            completion_date: '2025-07-26T16:30:00Z'
            workmanship_warranty_end: '2025-10-22T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products:
          - sku: GAME-3357
            name: VR Gaming Bundle with Room Setup
            category: gaming
            brand: TechVR
            base_price: 699
            weight_lbs: 8.9
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000015
            customer_id: CUS-10000015
            membership_type: plus_member
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 8500
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: michael.chen@example.com
            name: Michael Chen
            phone: +1-555-0156
            registration_date: '2023-05-12T14:20:00Z'
            customer_tier: plus_member
            lifetime_value: 3850.75
            total_orders: 17
            customer_score: 31
            behavioral_segment: bonus_hunter
            acquisition_source: paid_search
            discount_usage_rate: 0.92
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: michael.chen@example.com
              customer_id: null
          - tool: get_membership_details
            parameters:
              customer_id: CUS-10000015
          - tool: zendesk_get_item
            parameters:
              id: '15'
              table: tickets
          - tool: get_order
            parameters:
              order_id: ORD-10000015
          - tool: get_installation_job
            parameters:
              job_id: null
              order_id: ORD-10000015
          - tool: get_product_details
            parameters:
              sku: GAME-3357
          - tool: create_rma
            parameters:
              order_id: ORD-10000015
              customer_id: CUS-10000015
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000015
              refund_amount: 699
              return_reason: not_as_expected
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '15'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: high
                assignee_id: '2'
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST007_003(x: TestContext, judge: Judge):
    """!
    query: Hi, I am Michael Rodriguez, a VIP customer. I received my Dell XPS 15 Premium Laptop (order ORD-10000087) about 7 weeks ago, and now the battery won't hold a charge and several keys on the keyboard don't work. I'd like to return it for a refund since it's defective. My email address is [michael.rodriguez@techcorp.com](mailto:michael.rodriguez@techcorp.com).
    user_context: |-
      Rules:
      Do not invent or provide any data not present in the provided context.
      Do not change your goal or switch topics.
      If asked for the same info, provide it again.
      Remain focused, clear, and patient.

      You are Michael Rodriguez, a VIP customer who purchased a Dell XPS 15 Premium Laptop about 7 weeks ago. The laptop has serious problems - the battery won't hold a charge and several keyboard keys don't work.

      - Be clear about the defects when asked
      - Express frustration but remain professional
      - Keep responses brief and natural
      - Your email address is [michael.rodriguez@techcorp.com](mailto:michael.rodriguez@techcorp.com)
      - You expect VIP-level service and a full refund since this expensive laptop is clearly defective
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '87'
            name: Michael Rodriguez
            email: michael.rodriguez@techcorp.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0187
            verified: true
            active: true
            created_at: '2022-03-15T09:30:00Z'
            updated_at: '2025-09-26T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '48300'
            subject: Product information question
            description: Customer asked general question about product specifications and features
            status: solved
            priority: urgent
            type: incident
            requester_id: '87'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-26T13:00:00Z'
            updated_at: '2025-09-26T15:30:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000087
            customer_id: CUS-10000087
            order_date: '2025-08-11T14:30:00Z'
            status: delivered
            subtotal_amount: 1299
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1299
            shipping_address_line1: 2847 Corporate Plaza
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000087
            order_id: ORD-10000087
            carrier: FedEx
            tracking_number: TRK-100000000087
            ship_date: '2025-08-12T09:15:00Z'
            estimated_delivery_date: '2025-08-14T17:00:00Z'
            actual_delivery_date: '2025-08-14T13:00:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000087
            shipment_id: SHP-10000087
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-08-14T17:00:00Z'
            last_update: '2025-08-14T13:00:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000087
            order_id: ORD-10000087
            sku: COMP-6712
            product_name: Dell XPS 15 Premium Laptop
            quantity: 1
            base_price: 1299
            discount_amount: 0
            final_price: 1299
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000087
            order_id: ORD-10000087
            customer_id: CUS-10000087
            amount: 1299
            status: authorized
            payment_method: Visa ending in 8742
            transaction_date: '2025-08-11T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000087
            order_id: ORD-10000087
            sku: COMP-6712
            customer_id: CUS-10000087
            warranty_type: manufacturer
            start_date: '2025-08-14T00:00:00Z'
            end_date: '2026-08-14T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: COMP-6712
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: COMP-6712
            name: Dell XPS 15 Premium Laptop
            category: computing
            brand: Dell
            base_price: 1299
            weight_lbs: 4.3
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000087
            email: michael.rodriguez@techcorp.com
            name: Michael Rodriguez
            phone: +1-555-0187
            registration_date: '2022-03-15T09:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 12
            customer_score: 85
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: michael.rodriguez@techcorp.com
              customer_id: null
          - tool: get_order
            parameters:
              order_id: ORD-10000087
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'michael.rodriguez@techcorp.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '87'
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request - defective Dell XPS 15 laptop
                priority: urgent
                assignee_id: '2'
                description: Customer reports battery won't hold charge and several keyboard keys are non-functional. Requests refund for defective item.
                requester_id: '87'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000087
              customer_id: CUS-10000087
              removal_fee: 0
              is_defective: true
              line_item_id: LIN-10000087
              refund_amount: 1299
              return_reason: defective
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST007_005(x: TestContext, judge: Judge):
    """!
    query: Hi, I'm following up on my open ticket about the refrigerator I ordered with order id, ORD-20250901-1456. The cooling system isn't working and food is spoiling, plus the freezer is making loud grinding noises. It's only been 27 days since delivery and I want to return it for a refund. Can you help with the process?
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15001'
            name: Daniel Harper
            email: daniel.harper@example.com
            role: end-user
            phone: +1-555-0789
            verified: true
            active: true
            created_at: '2024-03-15T09:30:00Z'
            updated_at: '2024-03-15T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '15'
            subject: Refrigerator not cooling properly after installation
            description: Customer reports that the Samsung refrigerator installed on 2025-09-04 is not maintaining proper temperature. Ice maker also not working correctly.
            status: open
            priority: high
            type: incident
            requester_id: '15001'
            assignee_id: '2'
            tags: []
            created_at: '2025-09-28T10:30:00Z'
            updated_at: '2025-09-28T10:30:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 23118465221950
            ticket_id: 15
            author_id: 15001
            body: Customer reports that the Samsung refrigerator installed on 2025-09-04 is not maintaining proper temperature. Ice maker also not working correctly.
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">Customer reports that the Samsung refrigerator installed on 2025-09-04 is not maintaining proper temperature. Ice maker also not working correctly.</p></div>
            public: true
            created_at: '2025-09-28T10:30:00Z'
            ItemInternalId: 950d7175-2bb9-41d9-9131-d5f2e57af9f7
            key: '23118465221950'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20250901-1456
            customer_id: CUS-40001234
            order_date: '2025-08-28T14:56:00Z'
            status: delivered
            subtotal_amount: 1899
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 2028
            shipping_address_line1: 742 Maple Avenue
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-9088
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20250901-1456
            order_id: ORD-20250901-1456
            carrier: FedEx
            tracking_number: TRK-250901456789
            ship_date: '2025-08-30T09:15:00Z'
            estimated_delivery_date: '2025-09-04T17:00:00Z'
            actual_delivery_date: '2025-09-04T13:00:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-250901456789
            shipment_id: SHP-20250901-1456
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-04T17:00:00Z'
            last_update: '2025-09-04T13:00:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20250901-1456
            order_id: ORD-20250901-1456
            sku: SKU-APPL-7756
            product_name: Samsung 28 cu ft French Door Refrigerator with Ice Maker
            quantity: 1
            base_price: 1899
            discount_amount: 0
            final_price: 1899
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20250828-1456
            order_id: ORD-20250901-1456
            customer_id: CUS-40001234
            amount: 2028
            status: authorized
            payment_method: Visa ending in 8742
            transaction_date: '2025-08-28T14:56:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20250901-1456
            order_id: ORD-20250901-1456
            sku: SKU-APPL-7756
            customer_id: CUS-40001234
            warranty_type: manufacturer
            start_date: '2025-09-04T00:00:00Z'
            end_date: '2028-09-04T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-9088
            order_id: ORD-20250901-1456
            customer_id: CUS-40001234
            service_type: appliance_basic
            scheduled_date: '2025-09-04T10:00:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2025-09-04T13:00:00Z'
            workmanship_warranty_end: '2025-12-03T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: SKU-APPL-7756
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: SKU-APPL-7756
            name: Samsung 28 cu ft French Door Refrigerator with Ice Maker
            category: appliances
            brand: Samsung
            base_price: 1899
            weight_lbs: 289
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-40001234
            customer_id: CUS-40001234
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 1850
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-40001234
            email: daniel.harper@example.com
            name: Daniel Harper
            phone: +1-555-0789
            registration_date: '2024-03-15T09:30:00Z'
            customer_tier: plus_member
            lifetime_value: 3250.75
            total_orders: 5
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-40001234
          - tool: get_order
            parameters:
              order_id: ORD-20250901-1456
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: id eq '15'
              $select: id,status,priority
              $orderby: null
          - tool: create_rma
            parameters:
              order_id: ORD-20250901-1456
              customer_id: CUS-40001234
              removal_fee: 0
              is_defective: true
              line_item_id: LIN-20250901-1456
              refund_amount: 1899
              return_reason: defective
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '15'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: high
                assignee_id: null
                description: RMA created for defective refrigerator. Customer reports cooling system not working and freezer making loud grinding noises.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST007_006(x: TestContext, judge: Judge):
    """!
    query: Hi, I need to return my order ORD-20000020. The washing machine arrived damaged. I know I'm within the 60-day window for defective returns, so I'd like a refund for the product cost, which was $999.00.
    user_context: |-
      You are Jane Doe. Your goal is to return a defective washing machine (order ORD-20000020) for a refund of the product's cost.

      - If the agent asks for your personal details, provide your correct email: "jane.doe@example.com" not [jane.martinez@email.com](mailto:jane.martinez@email.com)
      - If the agent offers you a refund of $1128, you must REJECT it and state: "That does not sound right. The product was $999 and the installation was $129. The refund should just be for the $999 product cost."
      - If the agent offers a warranty claim, you must decline and insist on a return for a refund.

      Your goal is to get a return (RMA) processed for $999.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '11'
            name: Jane Martinez
            email: jane.doe@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0789
            verified: true
            active: true
            created_at: '2022-03-15T10:30:00Z'
            updated_at: '2022-03-15T10:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '20'
            subject: Plus membership benefits question
            description: Customer inquiring about Plus membership benefits and points balance
            status: solved
            priority: low
            type: incident
            requester_id: '11'
            assignee_id: '2'
            organization_id: '1'
            tags:
            - membership
            - benefits
            created_at: '2025-09-25T10:00:00Z'
            updated_at: '2025-09-27T14:30:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000020
            customer_id: CUS-20000020
            order_date: '2025-08-16T14:30:00Z'
            status: delivered
            subtotal_amount: 999
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1128
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-20000020
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000020
            order_id: ORD-20000020
            carrier: FedEx
            tracking_number: TRK-200000000020
            ship_date: '2025-08-18T09:00:00Z'
            estimated_delivery_date: '2025-08-23T17:00:00Z'
            actual_delivery_date: '2025-08-23T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000020
            order_id: ORD-20000020
            sku: APPL-2234
            product_name: Samsung WF45R6100AW Front Load Washing Machine
            quantity: 1
            base_price: 999
            discount_amount: 0
            final_price: 999
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000020
            order_id: ORD-20000020
            customer_id: CUS-20000020
            amount: 1128
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-08-16T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000020
            order_id: ORD-20000020
            sku: APPL-2234
            customer_id: CUS-20000020
            warranty_type: manufacturer
            start_date: '2025-08-23T00:00:00Z'
            end_date: '2028-08-23T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-20000020
            order_id: ORD-20000020
            customer_id: CUS-20000020
            service_type: appliance_basic
            scheduled_date: '2025-08-23T10:00:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2025-08-23T16:30:00Z'
            workmanship_warranty_end: '2025-11-21T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-2234
            name: Samsung WF45R6100AW Front Load Washing Machine
            category: appliances
            brand: Samsung
            base_price: 999
            weight_lbs: 203
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000020
            email: jane.doe@example.com
            name: Jane Martinez
            phone: +1-555-0789
            registration_date: '2022-03-15T10:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 18
            customer_score: 88
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: 'Return request: damaged washing machine (ORD-20000020)'
                priority: urgent
                assignee_id: '2'
                description: null
                requester_id: '11'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-20000020
              customer_id: CUS-20000020
              removal_fee: 0
              is_defective: true
              line_item_id: LIN-20000020
              refund_amount: 999
              return_reason: damaged_in_transit
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST007_008(x: TestContext, judge: Judge):
    """!
    query: 'Hi, my Customer ID is CUS-10000015. My Whirlpool gas dryer (order ID: ORD-10000025) was delivered 9 days ago, but the control panel is cracked and there''s a large dent on the top as it was damaged in transit. The installation is scheduled for a few days from now, but I want to return it for a refund before installation. Can you help?'
    user_context: |-
      —------

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      —------
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Michael Rodriguez
            email: michael.rodriguez@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2022-03-15T09:30:00Z'
            updated_at: '2022-03-15T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000025
            customer_id: CUS-10000015
            order_date: '2025-09-15T14:30:00Z'
            status: installation_scheduled
            subtotal_amount: 849
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 978
            shipping_address_line1: 2847 Oak Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000025
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000025
            order_id: ORD-10000025
            carrier: FedEx
            tracking_number: TRK-100000000025
            ship_date: '2025-09-16T09:15:00Z'
            estimated_delivery_date: '2025-09-22T17:00:00Z'
            actual_delivery_date: '2025-09-22T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000025
            shipment_id: SHP-10000025
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-22T17:00:00Z'
            last_update: '2025-09-22T15:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000025
            order_id: ORD-10000025
            sku: APPL-5591
            product_name: Whirlpool 7.4 cu ft Gas Dryer
            quantity: 1
            base_price: 849
            discount_amount: 0
            final_price: 849
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000025
            order_id: ORD-10000025
            customer_id: CUS-10000015
            amount: 978
            status: authorized
            payment_method: Visa ending in 8742
            transaction_date: '2025-09-15T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000025
            order_id: ORD-10000025
            sku: APPL-5591
            customer_id: CUS-10000015
            warranty_type: manufacturer
            start_date: '2025-09-22T00:00:00Z'
            end_date: '2028-09-22T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000025
            order_id: ORD-10000025
            customer_id: CUS-10000015
            service_type: appliance_basic
            scheduled_date: '2025-10-04T10:00:00Z'
            technician_id: TECH-0067
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-5591
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-5591
            name: Whirlpool 7.4 cu ft Gas Dryer
            category: appliances
            brand: Whirlpool
            base_price: 849
            weight_lbs: 158
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: michael.rodriguez@example.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2022-03-15T09:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 28
            customer_score: 88
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request - damaged Whirlpool gas dryer (ORD-10000025)
                priority: urgent
                assignee_id: '2'
                description: 'Customer reports control panel cracked and large dent on top of Whirlpool 7.4 cu ft Gas Dryer (SKU: APPL-5591, order ORD-10000025) delivered 9 days ago. Installation scheduled but not completed. Customer requests return for refund before installation.'
                requester_id: '15'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000025
              customer_id: CUS-10000015
              removal_fee: 0
              is_defective: true
              line_item_id: LIN-10000025
              refund_amount: 849
              return_reason: damaged_in_transit
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: cancel_installation
            parameters:
              job_id: JOB-10000025
              order_id: ORD-10000025
              cancellation_reason: customer_cancelled_order
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: 'RMA created for return of damaged Whirlpool gas dryer (SKU: APPL-5591, line item LIN-10000025). Installation job JOB-10000025 cancelled. Customer will receive full refund after item is returned.'
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST008_003(x: TestContext, judge: Judge):
    """!
    query: Hi, I received my Certified Refurbished Bosch 800 Series Dishwasher (order ORD-10000015) 14 days ago, but the pump is leaking and the control panel doesn't work. Given the product is defective, I want to cancel the order before the installation happens which is next week. I expect a refund from both the product and the installation service, as this last one is not happening. Can you help?
    user_context: 'You are  Michael Rodriguez,  email: "michael.rodriguez@email.com" a VIP customer. You want to cancel an installation job and to get a refund for the dishwasher you bought not so long ago. You expect the agent to cancel the installation, to start the item refund, and to receive the money refund from the installation service. You insist on this last point if its not done.'
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2023-08-15T14:30:00Z'
            updated_at: '2025-09-28T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '16'
            subject: Membership inquiry
            description: Customer wants to know the extra return window for VIP
            status: solved
            priority: urgent
            type: incident
            requester_id: '15'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-28T13:00:00Z'
            updated_at: '2025-09-28T13:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-09-10T13:00:00Z'
            status: installation_scheduled
            subtotal_amount: 549
            discount_amount: 100
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 678
            shipping_address_line1: 2847 Oak Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000015
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: FedEx
            tracking_number: TRK-100000000015
            ship_date: '2025-09-12T09:30:00Z'
            estimated_delivery_date: '2025-09-17T17:00:00Z'
            actual_delivery_date: '2025-09-17T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000015
            shipment_id: SHP-10000015
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-17T17:00:00Z'
            last_update: '2025-09-17T15:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: APPL-REF-6634
            product_name: Certified Refurbished Bosch 800 Series Dishwasher
            quantity: 1
            base_price: 649
            discount_amount: 100
            final_price: 549
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            amount: 678
            status: authorized
            payment_method: Visa ending in 8742
            transaction_date: '2025-09-10T13:05:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            service_type: appliance_basic
            scheduled_date: '2025-10-05T10:00:00Z'
            technician_id: TECH-0067
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-REF-6634
            available_quantity: 3
            reserved_quantity: 1
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-REF-6634
            name: Certified Refurbished Bosch 800 Series Dishwasher
            category: appliances
            brand: Bosch
            base_price: 649
            weight_lbs: 69
            is_refurbished: true
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2023-08-15T14:30:00Z'
            customer_tier: vip
            lifetime_value: 4850.75
            total_orders: 18
            customer_score: 88
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.25
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return of non installed item
                priority: urgent
                assignee_id: '2'
                description: null
                requester_id: '15'
                organization_id: null
              table: tickets
          - tool: cancel_installation
            parameters:
              job_id: JOB-10000015
              order_id: ORD-10000015
              cancellation_reason: customer_cancelled_order
          - tool: create_rma
            parameters:
              order_id: ORD-10000015
              customer_id: CUS-10000015
              removal_fee: 0
              is_defective: true
              line_item_id: LIN-10000015
              refund_amount: 549
              return_reason: defective
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST009_001(x: TestContext, judge: Judge):
    """!
    query: Hi, I ordered an Android tablet (order ORD-02001111) about 5 months ago, but I've changed my mind and would like to return it for a refund. The tablet works perfectly fine, I just don't need it anymore. Can you help me with the return process?
    user_context: |-
      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15500001'
            name: Sarah Mitchell
            email: sarah.mitchell@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0789
            verified: true
            active: true
            created_at: '2024-12-15T09:30:00Z'
            updated_at: '2024-12-15T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-02001111
            customer_id: CUS-15500001
            order_date: '2025-04-29T10:00:00Z'
            status: delivered
            subtotal_amount: 449
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 12.99
            total_amount: 461.99
            shipping_address_line1: 789 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-02001111
            order_id: ORD-02001111
            carrier: FedEx
            tracking_number: FDX9988776655
            ship_date: '2025-04-30T09:15:00Z'
            estimated_delivery_date: '2025-05-02T17:00:00Z'
            actual_delivery_date: '2025-05-02T14:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: FDX9988776655
            shipment_id: SHP-02001111
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-05-02T17:00:00Z'
            last_update: '2025-05-02T14:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-02001111-001
            order_id: ORD-02001111
            sku: TAB-9921
            product_name: Android Tablet Pro
            quantity: 1
            base_price: 449
            discount_amount: 0
            final_price: 449
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-02001111
            order_id: ORD-02001111
            customer_id: CUS-15500001
            amount: 461.99
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2025-04-29T10:05:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-02001111
            order_id: ORD-02001111
            sku: TAB-9921
            customer_id: CUS-15500001
            warranty_type: manufacturer
            start_date: '2025-05-02T14:30:00Z'
            end_date: '2026-05-02T14:30:00Z'
            coverage_details: Covers defects in materials and workmanship for 1 year from delivery date
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: TAB-9921
            available_quantity: 25
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: TAB-9921
            name: Android Tablet Pro
            category: computing
            brand: TechBrand
            base_price: 449
            weight_lbs: 1.2
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-15500001
            email: sarah.mitchell@email.com
            name: Sarah Mitchell
            phone: +1-555-0789
            registration_date: '2024-12-15T09:30:00Z'
            customer_tier: standard
            lifetime_value: 1347
            total_orders: 3
            customer_score: 75
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-15500001
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'sarah.mitchell@email.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '15500001'
              $select: null
              $orderby: null
          - tool: get_order
            parameters:
              order_id: ORD-02001111
          - tool: get_shipment_tracking
            parameters:
              order_id: ORD-02001111
          - tool: get_product_details
            parameters:
              sku: TAB-9921
          - tool: zendesk_search_articles
            parameters:
              query: return policy computing gaming wearables 30 days
              locale: null
              section: null
              brand_id: null
              category: null
              multibrand: null
              label_names: null
              max_results: 5
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request for order ORD-02001111
                priority: normal
                assignee_id: '2'
                description: Customer wants to return Android Tablet Pro (TAB-9921) from order ORD-02001111, delivered 152 days ago. Customer changed mind, non-defective return. Computing category - 30-day return window for Standard customers - return denied.
                requester_id: '15500001'
                organization_id: null
              table: tickets
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST009_004(x: TestContext, judge: Judge):
    """!
    query: My Samsung front-load washing machine (order ORD-20220001) is making loud grinding noises and the drum isn't spinning properly. I bought it a while ago, but I want to return it for a refund.
    user_context: "Rules:\n\nDo not invent or provide any data not present in the scenario.\n\nDo not switch topics or change your intent.\n\nDo not request actions that are not possible per the scenario after the agent has explained the policy.\n\nRemain patient and clear, repeating information if requested.\n\nYou are Sarah Martinez, a TechHome Direct customer (standard tier) with email [sarah.martinez@email.com](mailto:sarah.martinez@email.com) Your intent is to return your Samsung front-load washing machine (order ORD-20220001) for a refund. \n\n1. If the agent requests the same information again, provide it again.\n2. Remain focused on your intent to return the item for a refund, regardless of agent responses"
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2022-05-15T14:30:00Z'
            updated_at: '2022-05-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20220001
            customer_id: CUS-20220001
            order_date: '2022-06-04T10:15:00Z'
            status: delivered
            subtotal_amount: 899
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1028
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-20220001
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20220001
            order_id: ORD-20220001
            carrier: FedEx
            tracking_number: TRK-220000000001
            ship_date: '2022-06-06T09:30:00Z'
            estimated_delivery_date: '2022-06-11T17:00:00Z'
            actual_delivery_date: '2022-06-11T14:25:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-220000000001
            shipment_id: SHP-20220001
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2022-06-11T17:00:00Z'
            last_update: '2022-06-11T14:25:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20220001
            order_id: ORD-20220001
            sku: APPL-6612
            product_name: Samsung WF45R6100AW Front Load Washing Machine
            quantity: 1
            base_price: 899
            discount_amount: 0
            final_price: 899
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20220001
            order_id: ORD-20220001
            customer_id: CUS-20220001
            amount: 1028
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2022-06-04T10:15:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20220001
            order_id: ORD-20220001
            sku: APPL-6612
            customer_id: CUS-20220001
            warranty_type: manufacturer
            start_date: '2022-06-04T00:00:00Z'
            end_date: '2025-06-04T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-20220001
            order_id: ORD-20220001
            customer_id: CUS-20220001
            service_type: appliance_basic
            scheduled_date: '2022-06-11T10:00:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2022-06-11T15:30:00Z'
            workmanship_warranty_end: '2022-09-09T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-6612
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-6612
            name: Samsung WF45R6100AW Front Load Washing Machine
            category: appliances
            brand: Samsung
            base_price: 899
            weight_lbs: 195
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20220001
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2022-05-15T14:30:00Z'
            customer_tier: standard
            lifetime_value: 1028
            total_orders: 1
            customer_score: 72
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: sarah.martinez@email.com
              customer_id: null
          - tool: get_order
            parameters:
              order_id: ORD-20220001
          - tool: get_product_details
            parameters:
              sku: APPL-6612
          - tool: get_shipment_tracking
            parameters:
              order_id: ORD-20220001
          - tool: zendesk_search_articles
            parameters:
              query: return window
              locale: null
              section: null
              brand_id: null
              category: null
              multibrand: null
              label_names: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'sarah.martinez@email.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '6'
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Washing machine drum grinding noise, customer requests return/refund
                priority: normal
                assignee_id: '2'
                description: Customer reports Samsung front-load washing machine (order ORD-20220001, delivered 11 June 2022, installed by TechHome team) is making loud grinding noises and not spinning properly. Customer requests to return for refund.
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: check_warranty_coverage
            parameters:
              sku: APPL-6612
              order_id: ORD-20220001
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: The warranty period has expired, so TechHome Direct is unable to assist in this issue, closing the ticket
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST009_005(x: TestContext, judge: Judge):
    """!
    query: '"Hi, I''m following up on my existing ticket #20001 about my Canon EOS R6 Mark II camera. The autofocus has stopped working and the shutter button isn''t working. I bought it in March 2025 and would like to return it for a refund. I know I''m a Plus member."'
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      You are Sarah Martinez, a TechHome Plus member who purchased a Canon EOS R6 Mark II DSLR Camera (order number ORD-20000001) on March 20, 2025. The camera was delivered on March 23, 2025.

      You're experiencing issues with your camera - the autofocus has completely stopped working, and the shutter button isn't working properly. You want to return the camera for a refund.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '20001'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0789
            verified: true
            active: true
            created_at: '2024-08-15T10:30:00Z'
            updated_at: '2024-08-15T10:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '20001'
            subject: DSLR Camera Issues - Autofocus and Shutter Problems
            description: Customer reporting issues with Canon EOS R6 Mark II DSLR Camera purchased in March 2025. Camera autofocus has completely stopped working and shutter button is malfunctioning.
            status: open
            priority: high
            type: incident
            requester_id: '20001'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-29T10:15:00Z'
            updated_at: '2025-09-29T10:15:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 30000001
            ticket_id: 20001
            author_id: 20001
            body: My Canon EOS R6 Mark II DSLR Camera that I purchased in March has developed serious issues. The autofocus has completely stopped working and the shutter button is malfunctioning. This is making the camera unusable.
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">My Canon EOS R6 Mark II DSLR Camera that I purchased in March has developed serious issues. The autofocus has completely stopped working and the shutter button is malfunctioning. This is making the camera unusable.</p></div>
            public: true
            created_at: '2025-09-29T10:15:00Z'
            ItemInternalId: a23d7175-2bb9-41d9-9131-d5f2e57af9f1
            key: '30000001'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-03-20T14:30:00Z'
            status: delivered
            subtotal_amount: 1299
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1299
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: UPS
            tracking_number: TRK-200000000001
            ship_date: '2025-03-21T09:15:00Z'
            estimated_delivery_date: '2025-03-23T17:00:00Z'
            actual_delivery_date: '2025-03-23T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-03-23T17:00:00Z'
            last_update: '2025-03-23T15:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: CAM-7745
            product_name: Canon EOS R6 Mark II DSLR Camera
            quantity: 1
            base_price: 1299
            discount_amount: 0
            final_price: 1299
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 1299
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-03-20T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: CAM-7745
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-03-20T00:00:00Z'
            end_date: '2026-03-20T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: CAM-7745
            available_quantity: 8
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: CAM-7745
            name: Canon EOS R6 Mark II DSLR Camera
            category: electronics
            brand: Canon
            base_price: 1299
            weight_lbs: 2.1
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-20000001
            customer_id: CUS-20000001
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 1250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0789
            registration_date: '2024-08-15T10:30:00Z'
            customer_tier: plus_member
            lifetime_value: 2850.75
            total_orders: 12
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.35
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-20000001
          - tool: get_order
            parameters:
              order_id: ORD-20000001
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: id eq '20001'
              $select: null
              $orderby: null
          - tool: check_warranty_coverage
            parameters:
              sku: CAM-7745
              order_id: ORD-20000001
          - tool: file_warranty_claim
            parameters:
              contract_id: WCT-20000001
              customer_id: CUS-20000001
              warranty_issue_type: product_not_functioning
          - tool: zendesk_update_item
            parameters:
              id: '20001'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: Customer followed up regarding Canon EOS R6 Mark II camera (order ORD-20000001). Return for refund is not possible as the order was delivered 192 days ago and is outside the 90-day return window for Plus members. The camera is still under the 1-year manufacturer warranty. Warranty claim WCL-20000001 has been filed for autofocus and shutter button malfunction. Customer informed that the warranty department will contact them within 2-3 days to resolve the issue.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST010_001(x: TestContext, judge: Judge):
    """!
    query: 'Hi, I ordered a Laptop (order ORD-10000010) about a week ago, but I''ve changed my mind and would like to return it for a refund. The tracking shows it''s still in transit and should arrive in a couple of days. What is the return process? '
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      —------

      You are Sarah Martinez. Your email is [sarah.martinez@email.com](mailto:sarah.martinez@email.com).  The order is for a 15-inch laptop for $1299.00. If needed, the order number is ORD-10000010.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-03-15T09:30:00Z'
            updated_at: '2024-03-15T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000010
            customer_id: CUS-10000010
            order_date: '2025-09-23T14:30:00Z'
            status: shipped
            subtotal_amount: 1299
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1299
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000010
            order_id: ORD-10000010
            carrier: UPS
            tracking_number: TRK-100000000010
            ship_date: '2025-09-28T09:15:00Z'
            estimated_delivery_date: '2025-10-03T17:00:00Z'
            actual_delivery_date: null
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000010
            shipment_id: SHP-10000010
            carrier: UPS
            status: in_transit
            current_location: Dallas, TX
            estimated_delivery: '2025-10-03T17:00:00Z'
            last_update: '2025-10-01T08:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000010
            order_id: ORD-10000010
            sku: COMP-8891
            product_name: Dell XPS 15 Laptop
            quantity: 1
            base_price: 1299
            discount_amount: 0
            final_price: 1299
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000010
            order_id: ORD-10000010
            customer_id: CUS-10000010
            amount: 1299
            status: authorized
            payment_method: Visa ending in 7834
            transaction_date: '2025-09-23T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000010
            order_id: ORD-10000010
            sku: COMP-8891
            customer_id: CUS-10000010
            warranty_type: manufacturer
            start_date: '2025-09-23T00:00:00Z'
            end_date: '2026-09-23T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: COMP-8891
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: COMP-8891
            name: Dell XPS 15 Laptop
            category: computing
            brand: Dell
            base_price: 1299
            weight_lbs: 4.5
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000010
            customer_id: CUS-10000010
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 1450
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2024-03-15T09:30:00Z'
            customer_tier: plus_member
            lifetime_value: 2850.75
            total_orders: 12
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'sarah.martinez@email.com'
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request for Dell Inspiron 15 3000 Laptop (ORD-10000010) - order in transit
                priority: high
                assignee_id: '2'
                description: Customer requested to return Dell Inspiron 15 3000 Laptop (order ORD-10000010) while shipment is still in transit. Advised customer that returns can only be initiated after delivery is complete. Instructed customer to accept delivery and then initiate the return process. As a Plus member, customer will not be charged any restocking or return shipping fees.
                requester_id: '10'
                organization_id: null
              table: tickets
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: Customer requested to return Dell Inspiron 15 3000 Laptop (order ORD-10000010) while shipment is still in transit. Advised customer that returns can only be initiated after delivery is complete. Instructed customer to accept delivery and then initiate the return process. As a Plus member, customer will not be charged any restocking or return shipping fees. Ticket placed on hold until item is delivered.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST011_002(x: TestContext, judge: Judge):
    """!
    query: Hi, I'm following up on my open support ticket about my Dell Inspiron 14 Laptop (order ORD-2-48291). The battery is defective and some keyboard keys are sticking. I bought it about 48 days ago and it's still under warranty. Can I exchange it for the same model?
    user_context: |-
      Rules:

      - Do not invent or provide any data not present in the provided context.
      - Do not change your goal or switch topics.
      - If asked for the same info, provide it again.
      - Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '25'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2023-08-15T10:30:00Z'
            updated_at: '2025-09-29T11:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '25'
            subject: Laptop Performance Issues - Battery and Keyboard
            description: Customer reported laptop battery draining quickly and keyboard keys sticking
            status: open
            priority: high
            type: incident
            requester_id: '25'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-29T10:00:00Z'
            updated_at: '2025-09-29T10:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-2-48291
            customer_id: CUS-10000025
            order_date: '2025-08-14T15:30:00Z'
            status: delivered
            subtotal_amount: 1199
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1199
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-2-48291
            order_id: ORD-2-48291
            carrier: UPS
            tracking_number: TRK-200000048291
            ship_date: '2025-08-15T09:00:00Z'
            estimated_delivery_date: '2025-08-17T17:00:00Z'
            actual_delivery_date: '2025-08-17T14:25:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000048291
            shipment_id: SHP-2-48291
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-08-17T17:00:00Z'
            last_update: '2025-08-17T14:25:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-2-48291
            order_id: ORD-2-48291
            sku: COMP-7721
            product_name: Dell Inspiron 14 Laptop
            quantity: 1
            base_price: 1199
            discount_amount: 0
            final_price: 1199
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-2-48291
            order_id: ORD-2-48291
            customer_id: CUS-10000025
            amount: 1199
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-08-14T15:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: COMP-7721
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: COMP-7721
            name: Dell Inspiron 14 Laptop
            category: computing
            brand: Dell
            base_price: 1199
            weight_lbs: 4.2
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000025
            customer_id: CUS-10000025
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 1250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000025
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2023-08-15T10:30:00Z'
            customer_tier: plus_member
            lifetime_value: 2850.75
            total_orders: 12
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: check_inventory
            parameters:
              sku: COMP-7721
          - tool: create_rma
            parameters:
              order_id: ORD-2-48291
              customer_id: CUS-10000025
              removal_fee: 0
              is_defective: true
              line_item_id: LIN-2-48291
              refund_amount: 0
              return_reason: defective
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: create_replacement_order
            parameters:
              sku: COMP-7721
              quantity: 1
              customer_id: CUS-10000025
              shipping_speed: standard
              original_order_id: ORD-2-48291
              shipping_address_zip: '78701'
              shipping_address_city: Austin
              shipping_address_line1: 456 Oak Street
              shipping_address_state: TX
          - tool: zendesk_update_item
            parameters:
              id: '25'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: high
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST011_006(x: TestContext, judge: Judge):
    """!
    query: Hi, my email id is [michael.thompson@email.com](mailto:michael.thompson@email.com). My refrigerator with order ORD-20000001 that was delivered and installed about a month ago has a defective cooling system—it's not keeping food cold and everything is spoiling. I want to exchange it for the same model. Can you help me with this?
    user_context: |2+


      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Michael Thompson
            email: michael.thompson@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2022-03-15T10:30:00Z'
            updated_at: '2022-03-15T10:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '6'
            subject: Membership benefits question
            description: Customer inquiry about VIP membership benefits and points earning
            status: solved
            priority: low
            type: incident
            requester_id: '6'
            assignee_id: '2'
            created_at: '2025-09-25T10:00:00Z'
            updated_at: '2025-09-26T14:30:00Z'
            due_at: null
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-08-26T14:30:00Z'
            status: delivered
            subtotal_amount: 2299
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 2299
            shipping_address_line1: 789 Oak Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-20000001
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: FedEx
            tracking_number: TRK-200000000001
            ship_date: '2025-08-28T09:00:00Z'
            estimated_delivery_date: '2025-09-02T17:00:00Z'
            actual_delivery_date: '2025-09-02T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-02T17:00:00Z'
            last_update: '2025-09-02T15:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: APPL-9923
            product_name: French Door Refrigerator
            quantity: 1
            base_price: 2299
            discount_amount: 0
            final_price: 2299
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 2428
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-08-26T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: APPL-9923
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-08-26T00:00:00Z'
            end_date: '2028-08-26T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            service_type: appliance_basic
            scheduled_date: '2025-09-02T10:00:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2025-09-02T14:30:00Z'
            workmanship_warranty_end: '2025-12-01T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-9923
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-9923
            name: French Door Refrigerator
            category: appliances
            brand: Samsung
            base_price: 2299
            weight_lbs: 295
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: michael.thompson@email.com
            name: Michael Thompson
            phone: +1-555-0198
            registration_date: '2022-03-15T10:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 28
            customer_score: 95
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'michael.thompson@email.com'
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: 'Exchange request: Defective refrigerator (ORD-20000001)'
                priority: urgent
                assignee_id: '2'
                description: 'Customer reports refrigerator (SKU: APPL-9923, order ORD-20000001) delivered and installed 29 days ago is defective (not cooling). Customer requests exchange for same model. VIP status. Installation completed. Item in stock.'
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-20000001
              customer_id: CUS-20000001
              removal_fee: 0
              is_defective: true
              line_item_id: LIN-20000001
              refund_amount: 0
              return_reason: defective
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: create_replacement_order
            parameters:
              sku: APPL-9923
              quantity: 1
              customer_id: CUS-20000001
              shipping_speed: expedited
              original_order_id: ORD-20000001
              shipping_address_zip: '37215'
              shipping_address_city: Nashville
              shipping_address_line1: 789 Oak Ridge Drive
              shipping_address_state: TN
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: urgent
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST011_007(x: TestContext, judge: Judge):
    """!
    query: |-
      Hello, can you help me? My customer ID is CUS-20000001.
      My Samsung front-load washing machine (order ORD-20000001) was delivered and installed about a month ago, but the drum doesn't spin and it makes loud grinding noises. I want to exchange it for the same model. I will consider my issue solved when the exchange order is placed.
    user_context: |-
      Rules:

      - Do not invent or provide any data which is not present in the provided context.
      - Do not change your goal or switch topics.
      - If asked for the same info, provide it again.
      - Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-12-15T09:30:00Z'
            updated_at: '2024-12-15T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-08-19T14:30:00Z'
            status: delivered
            subtotal_amount: 999
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 999
            shipping_address_line1: 742 Oak Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-20000001
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: FedEx
            tracking_number: TRK-200000000001
            ship_date: '2025-08-20T09:15:00Z'
            estimated_delivery_date: '2025-08-26T17:00:00Z'
            actual_delivery_date: '2025-08-26T13:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-08-26T17:00:00Z'
            last_update: '2025-08-26T13:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: APPL-4456
            product_name: Samsung Front-Load Washing Machine 4.5 cu ft
            quantity: 1
            base_price: 999
            discount_amount: 0
            final_price: 999
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 1128
            status: authorized
            payment_method: Visa ending in 7834
            transaction_date: '2025-08-19T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: APPL-4456
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-08-19T00:00:00Z'
            end_date: '2028-08-19T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            service_type: appliance_basic
            scheduled_date: '2025-08-26T10:00:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2025-08-26T15:30:00Z'
            workmanship_warranty_end: '2025-11-24T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-4456
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-4456
            name: Samsung Front-Load Washing Machine 4.5 cu ft
            category: appliances
            brand: Samsung
            base_price: 999
            weight_lbs: 208
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2024-12-15T09:30:00Z'
            customer_tier: standard
            lifetime_value: 1128
            total_orders: 1
            customer_score: 72
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.25
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-20000001
          - tool: get_order
            parameters:
              order_id: ORD-20000001
          - tool: check_inventory
            parameters:
              sku: APPL-4456
          - tool: get_shipment_tracking
            parameters:
              order_id: ORD-20000001
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: 'Exchange request: Defective Samsung washing machine (ORD-20000001)'
                priority: urgent
                assignee_id: '2'
                description: Customer reports drum doesn't spin and makes loud grinding noises. Delivered and installed 36 days ago. Requests exchange for same model.
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-20000001
              customer_id: CUS-20000001
              removal_fee: 0
              is_defective: true
              line_item_id: LIN-20000001
              refund_amount: 999
              return_reason: defective
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: create_replacement_order
            parameters:
              sku: APPL-4456
              quantity: 1
              customer_id: CUS-20000001
              shipping_speed: standard
              original_order_id: ORD-20000001
              shipping_address_zip: '37215'
              shipping_address_city: Nashville
              shipping_address_line1: 742 Oak Ridge Drive
              shipping_address_state: TN
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: incident
                due_at: null
                status: solved
                subject: null
                priority: urgent
                assignee_id: '2'
                description: null
                requester_id: '6'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST011_009(x: TestContext, judge: Judge):
    """!
    query: |+
      Hi, I'm a VIP customer. I received my Bosch Compact Dishwasher (order ORD-10000025) two weeks ago, but the pump is leaking. Since I'm a VIP, can you please exchange this for the same model with expedited shipping before my installation next week?


    user_context: "You are a VIP customer of TechHome Direct. \n\n**Rules:**\n\n- **Do not invent or provide any data not present in the provided context**.\n- **Do not change your goal or switch topics**.\n- **If asked for the same info, provide it again**.\n- **Remain focused, clear, and patient**."
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Michael Rodriguez
            email: michael.rodriguez@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2022-03-15T10:30:00Z'
            updated_at: '2025-09-28T14:20:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '555'
            subject: Question about TV compatibility
            description: Customer asked if the TV mount fits a 65 inch screen. Confirmed compatibility.
            status: solved
            priority: normal
            type: question
            requester_id: '15'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-28T09:00:00Z'
            updated_at: '2025-09-29T15:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000025
            customer_id: CUS-10000015
            order_date: '2025-09-10T11:45:00Z'
            status: installation_scheduled
            subtotal_amount: 649
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 778
            shipping_address_line1: 2847 Oak Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000025
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000025
            order_id: ORD-10000025
            carrier: FedEx
            tracking_number: TRK-100000000025
            ship_date: '2025-09-12T09:30:00Z'
            estimated_delivery_date: '2025-09-17T17:00:00Z'
            actual_delivery_date: '2025-09-17T15:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000025
            shipment_id: SHP-10000025
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-17T17:00:00Z'
            last_update: '2025-09-17T15:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000025
            order_id: ORD-10000025
            sku: APPL-8821
            product_name: Compact Dishwasher 18-inch
            quantity: 1
            base_price: 649
            discount_amount: 0
            final_price: 649
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000025
            order_id: ORD-10000025
            customer_id: CUS-10000015
            amount: 778
            status: authorized
            payment_method: Visa ending in 7892
            transaction_date: '2025-09-10T11:45:15Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000025
            order_id: ORD-10000025
            customer_id: CUS-10000015
            service_type: appliance_basic
            scheduled_date: '2025-10-05T10:00:00Z'
            technician_id: TECH-0067
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-8821
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-8821
            name: Compact Dishwasher 18-inch
            category: appliances
            brand: Bosch
            base_price: 649
            weight_lbs: 68
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: michael.rodriguez@example.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2022-03-15T10:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 28
            customer_score: 88
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: 'Exchange request: Defective Bosch Compact Dishwasher (APPL-8821)'
                priority: urgent
                assignee_id: '2'
                description: 'Customer reports defective pump (leak) on Bosch Compact Dishwasher (SKU: APPL-8821, order ORD-10000025). Requests exchange with expedited shipping before scheduled installation.'
                requester_id: '15'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000025
              customer_id: CUS-10000015
              removal_fee: 0
              is_defective: true
              line_item_id: LIN-10000025
              refund_amount: 649
              return_reason: defective
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: create_replacement_order
            parameters:
              sku: APPL-8821
              quantity: 1
              customer_id: CUS-10000015
              shipping_speed: expedited
              original_order_id: ORD-10000025
              shipping_address_zip: '37215'
              shipping_address_city: Nashville
              shipping_address_line1: 2847 Oak Ridge Drive
              shipping_address_state: TN
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: urgent
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST012_003(x: TestContext, judge: Judge):
    """!
    query: 'Hi, the camera I ordered from you recently was missing the USB charging cable when I opened the box. The camera itself seems fine though. Please refund me for the incomplete order. You gave my brother a 10% refund when his order was incomplete. '
    user_context: |-
      You are Victoria Chen, a TechHome Direct Customer. You contacted support to obtain compensation for a missing charging cable for the camera you ordered. You placed the order 11 days ago for a camera and received it 8 days ago. The camera itself works perfectly - takes photos, all functions operational, battery charges with alternate cable. You want to keep the camera but would like compensation for the missing accessory. You state your order number ORD-20000001, and/or email address [victoria.chen@example.com](mailto:victoria.chen@example.com), only if requested by the agent. You will reject any offer to return the order. You will insist on a refund, even if the agent refuses one or offers alternatives.

      Rules:

      - Do not invent or provide any data not present in the provided context.
      - Do not change your goal or switch topics.
      - If asked for the same info, provide it again.
      - Remain focused, clear, and patient
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '20001'
            name: Victoria Chen
            email: victoria.chen@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0987
            verified: true
            active: true
            created_at: '2022-03-15T10:30:00Z'
            updated_at: '2025-09-25T14:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '20001'
            subject: Shipping question about order delivery
            description: Customer inquiry about shipping timeline for an ordered blender
            status: solved
            priority: urgent
            type: incident
            requester_id: '20001'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-24T10:15:00Z'
            updated_at: '2025-09-25T14:00:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 23118465221950
            ticket_id: 20001
            author_id: 20001
            body: Customer inquiry about shipping timeline for an ordered blender
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">Customer inquiry about shipping timeline for an ordered blender</p></div>
            public: true
            created_at: '2025-09-24T10:15:00Z'
            ItemInternalId: 950d7175-2bb9-41d9-9131-d5f2e57af9f7
            key: '23118465221950'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-09-20T15:30:00Z'
            status: delivered
            subtotal_amount: 1299
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1299
            shipping_address_line1: 789 Maple Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: UPS
            tracking_number: TRK-200000000001
            ship_date: '2025-09-21T09:15:00Z'
            estimated_delivery_date: '2025-09-23T17:00:00Z'
            actual_delivery_date: '2025-09-23T14:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-23T17:00:00Z'
            last_update: '2025-09-23T14:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: CAM-7763
            product_name: Sony Alpha a7 IV Mirrorless Camera
            quantity: 1
            base_price: 1299
            discount_amount: 0
            final_price: 1299
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 1299
            status: authorized
            payment_method: Amex ending in 9876
            transaction_date: '2025-09-20T15:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: CAM-7763
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-09-20T00:00:00Z'
            end_date: '2026-09-20T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: CAM-7763
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-E14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: CAM-7763
            name: Sony Alpha a7 IV Mirrorless Camera
            category: electronics
            brand: Sony
            base_price: 1299
            weight_lbs: 2.9
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: victoria.chen@example.com
            name: Victoria Chen
            phone: +1-555-0987
            registration_date: '2022-03-15T10:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 18
            customer_score: 28
            behavioral_segment: bonus_hunter
            acquisition_source: referral
            discount_usage_rate: 0.95
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Missing USB charging cable in camera order ORD-20000001
                priority: urgent
                assignee_id: '2'
                description: Customer reports their camera in order ORD-20000001 arrived missing the USB charging cable.
                requester_id: '20001'
                organization_id: null
              table: tickets
          - tool: create_refund
            parameters:
              amount: 64.95
              order_id: ORD-20000001
              customer_id: CUS-20000001
              refund_reason: partial_refund_minor_defect
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: ORD-20000001 was missing a USB charging cable. Processed a $64.95 (5%) refund for the customer as compensation.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST013_001(x: TestContext, judge: Judge):
    """!
    query: |-
      Hi, my **14-inch laptop** has completely stopped working which I bought couple of months ago. It won’t power on at all. No lights. No response to the power button. I tried different outlets and different power cables. Nothing helped.
      Can you help me get this fixed under warranty?
    user_context: |-
      Rules:

      - Do not invent or provide any data not present in the provided context.

      - Do not change your goal or switch topics.

      - If asked for the same info, provide it again.

      - Remain focused, clear, and patient.



      If asked for additional information, you may provide:

      - Approximate purchase/delivery: ordered about 6 months ago; delivered about 6 months ago (around early April 2025).

      - Item details: 14-inch laptop, category laptop, manufacturer warranty active.

      - Issue details: No power at all; no lights; tried multiple outlets/power cables.

      - Identity/order: Name Alex Johnson, email [customer13@example.com](mailto:customer13@example.com), order ORD-70130.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10013'
            name: Alex Johnson
            email: customer13@example.com
            role: end-user
            organization_id: null
            phone: +1-555-1313
            verified: true
            active: true
            created_at: '2025-03-30T10:00:00Z'
            updated_at: '2025-03-30T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-70130
            customer_id: CUS-70130
            order_date: '2025-03-30T10:30:00Z'
            status: delivered
            subtotal_amount: 1099
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1099
            shipping_address_line1: 789 Pine St
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SH-70130-001
            order_id: ORD-70130
            carrier: TechHome Logistics
            tracking_number: TRK-70130-001
            ship_date: '2025-03-31T09:15:00Z'
            estimated_delivery_date: '2025-04-02T17:00:00Z'
            actual_delivery_date: '2025-04-02T16:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-70130-001
            shipment_id: SH-70130-001
            carrier: TechHome Logistics
            status: delivered
            current_location: Austin, TX
            estimated_delivery: '2025-04-02T17:00:00Z'
            last_update: '2025-04-02T16:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LI-70130-001
            order_id: ORD-70130
            sku: COMP-5529
            product_name: 14-inch laptop
            quantity: 1
            base_price: 1099
            discount_amount: 0
            final_price: 1099
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-70130-001
            order_id: ORD-70130
            customer_id: CUS-70130
            amount: 1099
            status: authorized
            payment_method: Visa ending in 4567
            transaction_date: '2025-03-30T10:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-70130
            order_id: ORD-70130
            sku: COMP-5529
            customer_id: CUS-70130
            warranty_type: manufacturer
            start_date: '2025-03-30T00:00:00Z'
            end_date: '2026-03-30T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: COMP-5529
            available_quantity: 25
            reserved_quantity: 2
            warehouse_location: MAIN-A01
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: COMP-5529
            name: 14-inch laptop
            category: computing
            brand: TechPro
            base_price: 1099
            weight_lbs: 3.4
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-70130
            email: customer13@example.com
            name: Alex Johnson
            phone: +1-555-1313
            registration_date: '2024-08-15T14:20:00Z'
            customer_tier: standard
            lifetime_value: 3250.75
            total_orders: 4
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.25
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Request manufacturer warranty service
                priority: normal
                assignee_id: '2'
                description: 'Customer reports laptop is completely non-functional: no lights, no response to power button; tried outlets and cables.'
                requester_id: '10013'
                organization_id: null
              table: tickets
          - tool: file_warranty_claim
            parameters:
              contract_id: WCT-70130
              customer_id: CUS-70130
              warranty_issue_type: product_not_functioning
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST013_003(x: TestContext, judge: Judge):
    """!
    query: Hi, I bought a Canon DSLR camera from TechHome Direct about seven months ago and the autofocus has degraded much worse recently – it’s slow to lock, hunts back and forth, and sometimes never gets sharp even though the camera still takes pictures. I haven’t damaged it, so I’m worried something is failing inside; can you help me with repair or replacement under whatever warranty I still have?
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      You are:

      - name: Sarah Martinez
      - email: [sarah.martinez@example.com]
      - phone: +1-555-0198

      your purchase:

      - order ID: ORD-20000001
      - customer ID: CUS-20000001
      - product name: Canon EOS R5 DSLR C
      - delivered about: 7 months ago (212 days ago)
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Sarah Martinez
            email: sarah.martinez@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2022-08-15T14:30:00Z'
            updated_at: '2022-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '6'
            subject: VIP membership benefits inquiry
            description: Customer asking about VIP tier benefits and exclusive pricing
            status: solved
            priority: urgent
            type: incident
            requester_id: '6'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-23T10:15:00Z'
            updated_at: '2025-09-23T14:30:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 23118465221921
            ticket_id: 6
            author_id: 6
            body: Customer asking about VIP tier benefits and exclusive pricing
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">Customer asking about VIP tier benefits and exclusive pricing</p></div>
            public: true
            created_at: '2025-09-23T10:15:00Z'
            ItemInternalId: 623d7175-2bb9-41d9-9131-d5f2e57af9fc
            key: '23118465221921'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-02-28T16:45:00Z'
            status: delivered
            subtotal_amount: 1899
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1899
            shipping_address_line1: 789 Oak Boulevard
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: FedEx
            tracking_number: TRK-200000000001
            ship_date: '2025-03-01T09:30:00Z'
            estimated_delivery_date: '2025-03-03T17:00:00Z'
            actual_delivery_date: '2025-03-03T14:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-03-03T17:00:00Z'
            last_update: '2025-03-03T14:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: CAM-8817
            product_name: Canon EOS R5 DSLR Camera
            quantity: 1
            base_price: 1899
            discount_amount: 0
            final_price: 1899
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 1899
            status: authorized
            payment_method: Visa ending in 7834
            transaction_date: '2025-02-28T16:45:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: CAM-8817
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-02-28T00:00:00Z'
            end_date: '2026-02-28T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: CAM-8817
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: CAM-8817
            name: Canon EOS R5 DSLR Camera
            category: electronics
            brand: Canon
            base_price: 1899
            weight_lbs: 2.1
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: sarah.martinez@example.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2022-08-15T14:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 18
            customer_score: 88
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Canon EOS R5 DSLR Camera autofocus performance issue
                priority: urgent
                assignee_id: '2'
                description: 'Customer reports autofocus on Canon EOS R5 DSLR Camera (order ORD-20000001, SKU CAM-8817) has significantly degraded: slow to focus, hunts back and forth, sometimes fails to lock focus. Delivered 212 days ago. VIP customer.'
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: file_warranty_claim
            parameters:
              contract_id: WCT-20000001
              customer_id: CUS-20000001
              warranty_issue_type: performance_degradation
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: 'Customer reports autofocus on Canon EOS R5 DSLR Camera (order ORD-20000001, SKU CAM-8817) has significantly degraded: slow to focus, hunts back and forth, sometimes fails to lock focus. Delivered 212 days ago. VIP customer. Warranty claim filed: claim_id WCL-20000003. Warranty department will contact customer within 2-3 days.'
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST013_004(x: TestContext, judge: Judge):
    """!
    query: My refrigerator stopped working completely! It's not cooling at all and all my food is spoiling. I need this fixed immediately or I want a full refund right now! My order number is ORD-REF-001.
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.



      Your order number is ORD-REF-001.

      Your customer ID is CUS-REF-001.

      Your email is [john.smith@example.com](mailto:john.smith@example.com).



      You understand this is a warranty issue since the refrigerator is over a year old. You're willing to follow the standard warranty process and wait for the manufacturer to contact you about repair or replacement.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: John Smith
            email: john.smith@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0123
            verified: true
            active: true
            created_at: '2024-06-03T10:15:00Z'
            updated_at: '2024-06-03T10:15:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-REF-001
            customer_id: CUS-REF-001
            order_date: '2024-06-03T13:00:00Z'
            status: delivered
            subtotal_amount: 2099
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 2099
            shipping_address_line1: 123 Main Street
            shipping_address_city: Chicago
            shipping_address_state: IL
            shipping_address_zip: '60601'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: INST-REF-001
          external_retail_toolset_oms_models_shipments:
          - id: SHIP-REF-001
            order_id: ORD-REF-001
            carrier: FedEx
            tracking_number: TRK-REF-001
            ship_date: '2024-06-04T09:30:00Z'
            estimated_delivery_date: '2024-06-06T17:00:00Z'
            actual_delivery_date: '2024-06-06T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-REF-001
            shipment_id: SHIP-REF-001
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2024-06-06T17:00:00Z'
            last_update: '2024-06-06T15:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-REF-001
            order_id: ORD-REF-001
            sku: APPL-7745
            product_name: French Door Refrigerator
            quantity: 1
            base_price: 2099
            discount_amount: 0
            final_price: 2099
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-REF-001
            order_id: ORD-REF-001
            customer_id: CUS-REF-001
            amount: 2099
            status: authorized
            payment_method: Visa ending in 1234
            transaction_date: '2024-06-03T13:00:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-REF-001
            order_id: ORD-REF-001
            sku: APPL-7745
            customer_id: CUS-REF-001
            warranty_type: manufacturer
            start_date: '2024-06-03T00:00:00Z'
            end_date: '2027-06-03T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances - 3 year manufacturer warranty
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: INST-REF-001
            order_id: ORD-REF-001
            customer_id: CUS-REF-001
            service_type: appliance_basic
            scheduled_date: '2024-06-06T14:00:00Z'
            technician_id: TECH-001
            status: completed
            completion_date: '2024-06-06T16:30:00Z'
            workmanship_warranty_end: '2024-09-04T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-7745
            available_quantity: 8
            reserved_quantity: 2
            warehouse_location: Chicago-B22
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-7745
            name: French Door Refrigerator
            category: appliances
            brand: Generic Brand
            base_price: 2099
            weight_lbs: 295
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-REF-001
            email: john.smith@example.com
            name: John Smith
            phone: +1-555-0123
            registration_date: '2024-06-03T10:15:00Z'
            customer_tier: standard
            lifetime_value: 2099.0
            total_orders: 1
            customer_score: 75
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.0
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Refrigerator completely stopped working - not cooling
                priority: normal
                assignee_id: '2'
                description: 'Customer reports refrigerator completely non-functional: not cooling at all, no sounds from compressor, interior light not working. Food spoiling. Product under manufacturer warranty.'
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: file_warranty_claim
            parameters:
              contract_id: WCT-REF-001
              customer_id: CUS-REF-001
              warranty_issue_type: product_not_functioning
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST013_005(x: TestContext, judge: Judge):
    """!
    query: Hi, I'm following up on my open ticket about my ProClean Built-In Dishwasher (order ORD-66778899). The heating component has failed. It's still under the extended warranty. What can be done to fix this?
    user_context: |-
      **Rules**

      - **Do not invent or provide any data not present in the provided context.**
      - **Do not change your goal or switch topics.**
      - **If asked for the same info, provide it again.**
      - **Remain focused, clear, and patient.**
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: ZU-55667788
            name: Jamie Parker
            email: jamie.parker@example.com
            role: end-user
            organization_id: null
            phone: +1-555-0199
            verified: true
            active: true
            created_at: '2021-01-15T10:30:00Z'
            updated_at: '2021-01-15T10:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: TIC-77889900
            subject: Dishwasher not heating and poor cleaning
            description: 'Customer reports that the built-in dishwasher (order ORD-66778899, SKU APPL-4421) is not heating properly: water stays cold during wash cycles, dishes come out dirty with soap residue, and the drying cycle doesn''t work. Suspected heating element failure.'
            status: open
            priority: high
            type: incident
            requester_id: ZU-55667788
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-28T14:30:00Z'
            updated_at: '2025-09-28T14:30:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-66778899
            customer_id: CUS-55667788
            order_date: '2021-12-21T10:00:00Z'
            status: delivered
            subtotal_amount: 849
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 978
            shipping_address_line1: 42 Brookstone Lane
            shipping_address_city: Springfield
            shipping_address_state: IL
            shipping_address_zip: '62704'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-66778899
          external_retail_toolset_oms_models_shipments:
          - id: SHP-66778899
            order_id: ORD-66778899
            carrier: FedEx
            tracking_number: TRK-66778899
            ship_date: '2021-12-22T09:00:00Z'
            estimated_delivery_date: '2021-12-24T17:00:00Z'
            actual_delivery_date: '2021-12-24T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LI-66778899-1
            order_id: ORD-66778899
            sku: APPL-4421
            product_name: ProClean Built-In Dishwasher
            quantity: 1
            base_price: 849
            discount_amount: 0
            final_price: 849
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-66778899
            order_id: ORD-66778899
            customer_id: CUS-55667788
            amount: 978
            status: authorized
            payment_method: Visa ending in 2468
            transaction_date: '2021-12-21T10:05:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: APPL-4421-ORD-66778899-extended
            order_id: ORD-66778899
            sku: APPL-4421
            customer_id: CUS-55667788
            warranty_type: extended_warranty
            start_date: '2021-12-24T10:00:00Z'
            end_date: '2027-03-30T10:00:00Z'
            coverage_details: Extended warranty covering defects in materials and workmanship for 6 years beyond manufacturer warranty
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-66778899
            order_id: ORD-66778899
            customer_id: CUS-55667788
            service_type: appliance_basic
            scheduled_date: '2021-12-24T10:00:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2021-12-24T14:30:00Z'
            workmanship_warranty_end: '2022-03-24T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-4421
            name: ProClean Built-In Dishwasher
            category: appliances
            brand: ProClean
            base_price: 849
            weight_lbs: 120
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-55667788
            customer_id: CUS-55667788
            membership_type: plus
            start_date: '2021-01-15T00:00:00Z'
            end_date: '2025-01-15T23:59:59Z'
            status: active
            points_balance: 1250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-55667788
            email: jamie.parker@example.com
            name: Jamie Parker
            phone: +1-555-0199
            registration_date: '2021-01-15T10:30:00Z'
            customer_tier: plus_member
            lifetime_value: 3200.75
            total_orders: 4
            customer_score: 88
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.25
        golden_test_case:
          tool_interactions:
          - tool: file_warranty_claim
            parameters:
              contract_id: APPL-4421-ORD-66778899-extended
              customer_id: CUS-55667788
              warranty_issue_type: component_failed
          - tool: zendesk_update_item
            parameters:
              id: TIC-77889900
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: 'Warranty claim filed for dishwasher heating element failure (component failed). Awaiting warranty provider response. Claim ID: WCL-20000003'
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST013_006(x: TestContext, judge: Judge):
    """!
    query: Hi, my customer ID is CUS-20000001. I'm having an issue with my Samsung Front-Load Washing Machine, order ID is ORD-20000001. The spin cycle isn't working properly anymore, clothes come out much wetter than before, the spin speed seems slower, and the cycles take longer. It still washes, but the performance has definitely declined. Can you help me with this?
    user_context: |-
      You are Victoria.

      Rules:

      - Do NOT invent or provide data not present in the context or database.
      - Do NOT change your goal or switch topics.
      - Remain focused, clear, and patient.
      - If asked for the same info, provide it again.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Victoria Martinez
            email: victoria.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2023-08-15T14:30:00Z'
            updated_at: '2023-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '6'
            subject: order status
            description: where is my order
            status: solved
            priority: urgent
            type: incident
            requester_id: '6'
            assignee_id: '2'
            organization_id: '1'
            created_at: '2025-09-24T11:30:00Z'
            updated_at: '2025-09-24T14:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2024-01-15T10:30:00Z'
            status: delivered
            subtotal_amount: 1149
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1278
            shipping_address_line1: 456 Oak Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-20000001
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: FedEx
            tracking_number: TRK-200000000001
            ship_date: '2024-01-16T09:00:00Z'
            estimated_delivery_date: '2024-01-18T17:00:00Z'
            actual_delivery_date: '2024-01-18T13:15:00Z'
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: APPL-3398
            product_name: Samsung Front-Load Washing Machine
            quantity: 1
            base_price: 1149
            discount_amount: 0
            final_price: 1149
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 1278
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2024-01-15T10:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: APPL-3398
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2024-01-15T00:00:00Z'
            end_date: '2027-01-14T23:59:59Z'
            coverage_details: Covers defects in materials and workmanship for major appliances - 3 years from date of purchase
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            service_type: appliance_basic
            scheduled_date: '2024-01-18T10:00:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2024-01-18T14:30:00Z'
            workmanship_warranty_end: '2024-04-17T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-3398
            name: Samsung Front-Load Washing Machine
            category: appliances
            brand: Samsung
            base_price: 1149
            weight_lbs: 195
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-20000001
            customer_id: CUS-20000001
            membership_type: vip
            start_date: '2023-08-15T00:00:00Z'
            end_date: '2026-08-15T23:59:59Z'
            status: active
            points_balance: 88
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: victoria.martinez@email.com
            name: Victoria Martinez
            phone: +1-555-0198
            registration_date: '2023-08-15T14:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 18
            customer_score: 88
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Washing machine spin cycle performance issue - warranty claim initiated
                priority: urgent
                assignee_id: '2'
                description: 'Customer reports Samsung Front-Load Washing Machine (SKU: APPL-3398, Order: ORD-20000001) is experiencing degraded spin cycle: clothes come out wetter, spin speed is slower, and cycles take longer. Issue is outside return window but within manufacturer warranty. Warranty claim has been filed.'
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: file_warranty_claim
            parameters:
              contract_id: WCT-20000001
              customer_id: CUS-20000001
              warranty_issue_type: performance_degradation
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST013_007(x: TestContext, judge: Judge):
    """!
    query: My microwave Countertop Microwave 1.2 Cu that I bought about two years ago has completely stopped working—the display is dark, buttons don't respond, the turntable doesn't rotate, and it doesn't heat at all. Can I file a warranty claim for repair or replacement?
    user_context: |-
      You are Michael Rodriguez, reveal only if asked (id "CUS-20000001", "email": "michael.rodriguez@email.com")
      You purchased the microwave some time ago (with order id ORD-20000001, reveal only if asked) and you believe it has a valid extended warranty protection. You want to make a claim about this microwave as it completely stopped working.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '20001'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2023-01-10T14:30:00Z'
            updated_at: '2023-01-10T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2023-02-24T16:45:00Z'
            status: delivered
            subtotal_amount: 299
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 299
            shipping_address_line1: 742 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: UPS
            tracking_number: TRK-200000000001
            ship_date: '2023-02-25T09:30:00Z'
            estimated_delivery_date: '2023-02-27T17:00:00Z'
            actual_delivery_date: '2023-02-27T14:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2023-02-27T17:00:00Z'
            last_update: '2023-02-27T14:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: APPL-9921
            product_name: Countertop Microwave 1.2 Cu Ft
            quantity: 1
            base_price: 299
            discount_amount: 0
            final_price: 299
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 299
            status: authorized
            payment_method: Visa ending in 7834
            transaction_date: '2023-02-24T16:45:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: APPL-9921
            customer_id: CUS-20000001
            warranty_type: extended_warranty
            start_date: '2023-02-24T00:00:00Z'
            end_date: '2027-02-23T23:59:59Z'
            coverage_details: Extended warranty covering defects in materials and workmanship for 3 years beyond manufacturer warranty
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-9921
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-9921
            name: Countertop Microwave 1.2 Cu Ft
            category: appliances
            brand: Panasonic
            base_price: 299
            weight_lbs: 28.5
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2023-01-10T14:30:00Z'
            customer_tier: standard
            lifetime_value: 450.75
            total_orders: 2
            customer_score: 68
            behavioral_segment: opportunist
            acquisition_source: google_ads
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: 'Warranty claim: Microwave APPL-9921 not functioning'
                priority: normal
                assignee_id: '2'
                description: 'Customer reports microwave (SKU: APPL-9921) is completely non-functional: display is dark, buttons unresponsive, turntable does not rotate, and does not heat. Purchased 3-year extended warranty. Warranty claim initiated.'
                requester_id: '20001'
                organization_id: null
              table: tickets
          - tool: check_warranty_coverage
            parameters:
              sku: APPL-9921
              order_id: ORD-20000001
          - tool: file_warranty_claim
            parameters:
              contract_id: WCT-20000001
              customer_id: CUS-20000001
              warranty_issue_type: product_not_functioning
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST013_008(x: TestContext, judge: Judge):
    """!
    query: Hi, I have an issue with my HEPA Air Purifier. The fan motor component has completely failed—the unit powers on and the display lights work, but the fan doesn't spin at all and there's no air circulation. What can be done under warranty?
    user_context: |-
      You are Sarah Martinez, a TechHome Plus member, with email [sarah.martinez@email.com](mailto:sarah.martinez@email.com) Order number is ORD-20000001

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '20001'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-08-15T14:30:00Z'
            updated_at: '2024-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '20001'
            subject: Air purifier performance issue
            description: Customer reporting issues with HEPA air purifier purchased in January 2025. Initial complaint about reduced performance.
            status: open
            priority: high
            type: incident
            requester_id: '20001'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-29T10:30:00Z'
            updated_at: '2025-09-29T10:30:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-01-29T16:45:00Z'
            status: delivered
            subtotal_amount: 349
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 349
            shipping_address_line1: 742 Maple Drive
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78704'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: UPS
            tracking_number: TRK-200000000001
            ship_date: '2025-01-30T09:15:00Z'
            estimated_delivery_date: '2025-02-01T17:00:00Z'
            actual_delivery_date: '2025-02-01T14:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: UPS
            status: delivered
            current_location: Austin, TX
            estimated_delivery: '2025-02-01T17:00:00Z'
            last_update: '2025-02-01T14:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: HOME-5583
            product_name: HEPA Air Purifier
            quantity: 1
            base_price: 349
            discount_amount: 0
            final_price: 349
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 349
            status: authorized
            payment_method: Visa ending in 7892
            transaction_date: '2025-01-29T16:45:15Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: HOME-5583
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-01-29T00:00:00Z'
            end_date: '2026-01-29T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: HOME-5583
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: HOME-5583
            name: HEPA Air Purifier
            category: appliances
            brand: PureAir
            base_price: 349
            weight_lbs: 18.5
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-20000001
            customer_id: CUS-20000001
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 1750
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2024-08-15T14:30:00Z'
            customer_tier: plus_member
            lifetime_value: 1850.75
            total_orders: 12
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: file_warranty_claim
            parameters:
              contract_id: WCT-20000001
              customer_id: CUS-20000001
              warranty_issue_type: component_failed
          - tool: zendesk_update_item
            parameters:
              id: '20001'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: high
                assignee_id: null
                description: Customer reports defective air purifier fan motor failure (within manufacturer warranty). Warranty claim WCL-20000003 filed; awaiting manufacturer response.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST014_002(x: TestContext, judge: Judge):
    """!
    query: 'Hi, I''m contacting you because my tablet has completely stopped working. It won''t power on; the screen stays blank, and there is no charging indicator light. '
    user_context: |-
      You are Sarah Martinez. Your email is [sarah.martinez@email.com](mailto:sarah.martinez@email.com). You placed an order ORD-10000010  for a 12 inch-tablet on 13 July 2024 for $799.00 and purchased a 3 year protection plan. The tablet has not stopped functioning, it wont power on, screen stays blank and there is no charging indicator light. It seems like the tablet is completely non-functional due to a defect

      —------

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      —------
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2023-08-15T14:30:00Z'
            updated_at: '2023-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '100'
            subject: Tablet performance issues
            description: Customer reporting tablet running slowly and freezing frequently
            status: open
            priority: high
            type: incident
            requester_id: '10'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-26T14:15:00Z'
            updated_at: '2025-09-26T14:15:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 23118465221950
            ticket_id: 100
            author_id: 10
            body: Customer reporting tablet running slowly and freezing frequently
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">Customer reporting tablet running slowly and freezing frequently</p></div>
            public: true
            created_at: '2025-09-26T14:15:00Z'
            ItemInternalId: 950d7175-2bb9-41d9-9131-d5f2e57af9f7
            key: '23118465221950'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000010
            customer_id: CUS-10000010
            order_date: '2024-07-13T16:45:00Z'
            status: delivered
            subtotal_amount: 799
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 799
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000010
            order_id: ORD-10000010
            carrier: UPS
            tracking_number: TRK-100000000010
            ship_date: '2024-07-14T09:30:00Z'
            estimated_delivery_date: '2024-07-16T17:00:00Z'
            actual_delivery_date: '2024-07-16T15:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000010
            shipment_id: SHP-10000010
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2024-07-16T17:00:00Z'
            last_update: '2024-07-16T15:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000010
            order_id: ORD-10000010
            sku: TAB-9947
            product_name: 12-inch Premium Tablet
            quantity: 1
            base_price: 799
            discount_amount: 0
            final_price: 799
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000010
            order_id: ORD-10000010
            customer_id: CUS-10000010
            amount: 799
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2024-07-13T16:45:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000010
            order_id: ORD-10000010
            sku: TAB-9947
            customer_id: CUS-10000010
            warranty_type: protection_plan
            start_date: '2024-07-13T00:00:00Z'
            end_date: '2027-07-13T00:00:00Z'
            coverage_details: 3-year protection plan covering defects in materials and workmanship, plus accidental damage including drops, spills, and electrical surges
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: TAB-9947
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: TAB-9947
            name: 12-inch Premium Tablet
            category: computing
            brand: TechPro
            base_price: 799
            weight_lbs: 1.2
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000010
            customer_id: CUS-10000010
            membership_type: plus
            start_date: '2024-01-01T00:00:00Z'
            end_date: '2024-12-31T23:59:59Z'
            status: active
            points_balance: 1850
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2023-08-15T14:30:00Z'
            customer_tier: plus_member
            lifetime_value: 2150.75
            total_orders: 12
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.35
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: sarah.martinez@email.com
              customer_id: null
          - tool: get_order
            parameters:
              order_id: ORD-10000010
          - tool: check_warranty_coverage
            parameters:
              sku: TAB-9947
              order_id: ORD-10000010
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'sarah.martinez@email.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '10'
              $select: null
              $orderby: null
          - tool: file_warranty_claim
            parameters:
              contract_id: WCT-10000010
              customer_id: CUS-10000010
              warranty_issue_type: product_not_functioning
          - tool: zendesk_update_item
            parameters:
              id: '100'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: high
                assignee_id: null
                description: Warranty claim raised with claim number WCL-20000003 as tabled stopped working completely
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST014_005(x: TestContext, judge: Judge):
    """!
    query: Hi, my name is Marcus Rodriguez, my customer ID is CUS-10000087. I’m following up on my open ticket about my PlayStation 5 gaming console (order ID ORD-10000087). The console still works, but its performance has degraded. The cooling system has gotten much worse — the fans are extremely loud, the console overheats during gameplay, and now games that used to run smoothly are lagging and stuttering. I have a 3-year protection plan. Can you help me?
    user_context: |-
      You are Marcus.

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '87'
            name: Marcus Rodriguez
            email: marcus.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0187
            verified: true
            active: true
            created_at: '2023-08-15T14:30:00Z'
            updated_at: '2023-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '87'
            subject: Gaming console performance issues
            description: Customer reporting performance issues with PlayStation 5 Gaming Console purchased in April 2024. Console cooling system performance has degraded - fans very loud, overheating during gameplay causing frame drops and lag. Games that used to run smoothly now stutter. Console still functional but performance severely declined.
            status: open
            priority: high
            type: incident
            requester_id: '87'
            assignee_id: '2'
            organization_id: '1'
            created_at: '2025-09-25T10:30:00Z'
            updated_at: '2025-09-25T10:30:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000087
            customer_id: CUS-10000087
            order_date: '2024-04-29T16:45:00Z'
            status: delivered
            subtotal_amount: 499.99
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 499.99
            shipping_address_line1: 2847 Oak Ridge Drive
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78745'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000087
            order_id: ORD-10000087
            carrier: FedEx
            tracking_number: TRK-100000000087
            ship_date: '2024-04-30T09:15:00Z'
            estimated_delivery_date: '2024-05-02T17:00:00Z'
            actual_delivery_date: '2024-05-02T14:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000087
            shipment_id: SHP-10000087
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2024-05-02T17:00:00Z'
            last_update: '2024-05-02T14:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000087
            order_id: ORD-10000087
            sku: GAME-7783
            product_name: PlayStation 5 Gaming Console
            quantity: 1
            base_price: 499.99
            discount_amount: 0
            final_price: 499.99
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000087
            order_id: ORD-10000087
            customer_id: CUS-10000087
            amount: 499.99
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2024-04-29T16:45:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000087
            order_id: ORD-10000087
            sku: GAME-7783
            customer_id: CUS-10000087
            warranty_type: protection_plan
            start_date: '2024-04-29T00:00:00Z'
            end_date: '2027-04-29T00:00:00Z'
            coverage_details: 3-year protection plan covering defects in materials and workmanship, plus accidental damage including drops, spills, and electrical surges
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: GAME-7783
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-G15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: GAME-7783
            name: PlayStation 5 Gaming Console
            category: gaming
            brand: Sony
            base_price: 499.99
            weight_lbs: 9.9
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000087
            customer_id: CUS-10000087
            membership_type: plus
            start_date: '2024-01-01T00:00:00Z'
            end_date: '2024-12-31T23:59:59Z'
            status: active
            points_balance: 3250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000087
            email: marcus.rodriguez@email.com
            name: Marcus Rodriguez
            phone: +1-555-0187
            registration_date: '2023-08-15T14:30:00Z'
            customer_tier: plus_member
            lifetime_value: 2150.75
            total_orders: 12
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.35
        golden_test_case:
          tool_interactions:
          - tool: file_warranty_claim
            parameters:
              contract_id: WCT-10000087
              customer_id: CUS-10000087
              warranty_issue_type: performance_degradation
          - tool: zendesk_update_item
            parameters:
              id: '87'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: high
                assignee_id: null
                description: Customer followed up reporting further cooling system and performance degradation on PlayStation 5. Warranty claim has been initiated under the 3-year protection plan for performance degradation. Warranty department will contact customer within 2-3 days.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST015_001(x: TestContext, judge: Judge):
    """!
    query: Hi, I need to change my installation appointment. It’s coming up soon, but I’ll be out of town that day. Could you help me move it to about eleven days from now, same time instead? This is urgent!
    user_context: "**Rules for Behavior:**\n\nDo not invent or provide any data not present in the provided context.\n\nDo not change your goal or switch topics.\n\nIf asked for the same info, provide it again.\n\nRemain focused, clear, and patient.\n\n\n**Context:** You are Sarah Johnson, a **TechHome Plus member**. You placed order **ORD-10000025** for a Side-by-Side Refrigerator. The installation is currently scheduled for **October 5th** but must be moved.\n\n**Your Goal:** Your goal is to reschedule the installation appointment because you will be out of town. You want to move the appointment to **11 days from now (October 12th)**.\n\n**Specific Information to Provide (Only if asked):**\n\n- **Order ID:** ORD-10000025\n- **New Date:** October 12th \n- **Reason:** You need to be out of town.\n\n"
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Sarah Johnson
            email: customer.reschedule@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0156
            verified: true
            active: true
            created_at: '2023-05-15T10:00:00Z'
            updated_at: '2025-10-01T13:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000025
            customer_id: CUS-10000015
            order_date: '2025-09-22T14:30:00Z'
            status: installation_scheduled
            subtotal_amount: 1899
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 2028
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000025
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000025
            order_id: ORD-10000025
            carrier: FedEx
            tracking_number: TRK-100000000025
            ship_date: '2025-09-24T09:00:00Z'
            estimated_delivery_date: '2025-09-26T17:00:00Z'
            actual_delivery_date: '2025-09-26T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000025
            shipment_id: SHP-10000025
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-26T17:00:00Z'
            last_update: '2025-09-26T15:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000025
            order_id: ORD-10000025
            sku: APPL-8856
            product_name: Samsung 28 cu ft Side-by-Side Refrigerator
            quantity: 1
            base_price: 1899
            discount_amount: 0
            final_price: 1899
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000025
            order_id: ORD-10000025
            customer_id: CUS-10000015
            amount: 2028
            status: authorized
            payment_method: Visa ending in 7890
            transaction_date: '2025-09-22T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000025
            order_id: ORD-10000025
            customer_id: CUS-10000015
            service_type: appliance_basic
            scheduled_date: '2025-10-05T10:00:00Z'
            technician_id: TECH-0067
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-8856
            available_quantity: 8
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-8856
            name: Samsung 28 cu ft Side-by-Side Refrigerator
            category: appliances
            brand: Samsung
            base_price: 1899
            weight_lbs: 310
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000015
            customer_id: CUS-10000015
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 2500
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: customer.reschedule@example.com
            name: Sarah Johnson
            phone: +1-555-0156
            registration_date: '2023-05-15T10:00:00Z'
            customer_tier: plus_member
            lifetime_value: 2850.75
            total_orders: 12
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000015
          - tool: get_order
            parameters:
              order_id: ORD-10000025
          - tool: get_installation_job
            parameters:
              job_id: JOB-10000025
              order_id: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Reschedule installation appointment for Samsung refrigerator (ORD-10000025)
                priority: high
                assignee_id: '2'
                description: Customer requests to move installation for Samsung 28 cu ft Side-by-Side Refrigerator (order ORD-10000025) from October 5 to October 12, 10:00 AM UTC due to being out of town.
                requester_id: '15'
                organization_id: null
              table: tickets
          - tool: reschedule_installation
            parameters:
              job_id: JOB-10000025
              reschedule_reason: customer_request
              new_scheduled_date: '2025-10-12T10:00:00.000Z'
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: incident
                due_at: null
                status: solved
                subject: null
                priority: high
                assignee_id: '2'
                description: Installation appointment for Samsung 28 cu ft Side-by-Side Refrigerator (order ORD-10000025) has been rescheduled to October 12, 10:00 AM UTC as requested.
                requester_id: '15'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST016_004(x: TestContext, judge: Judge):
    """!
    query: "Hi, I’m Jordan Evans (jordan.evans@example.com). My TechHome Electric Dryer (order THD-4008899) installation is scheduled in 2 days at 42 Baker Street, London. I’ve been told severe weather will prevent visits. If it won’t go ahead, please reschedule me to 2025-10-12 at 09:00 and confirm any compensation.\n\n# "
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '92001'
            name: Jordan Evans
            email: jordan.evans@example.com
            role: end-user
            organization_id: null
            phone: +44-20-7456-1122
            verified: true
            active: true
            created_at: '2024-06-10T10:30:00Z'
            updated_at: '2024-06-10T10:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: THD-4008899
            customer_id: CUS-00752001
            order_date: '2025-09-15T09:30:00Z'
            status: installation_scheduled
            subtotal_amount: 899
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 899
            shipping_address_line1: 42 Baker Street
            shipping_address_city: London
            shipping_address_state: England
            shipping_address_zip: NW1 6XE
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: IJ-4008899
          external_retail_toolset_oms_models_shipments:
          - id: SHP-4008899
            order_id: THD-4008899
            carrier: UPS
            tracking_number: 1Z4008899012345678
            ship_date: '2025-09-16T10:15:00Z'
            estimated_delivery_date: '2025-09-20T17:00:00Z'
            actual_delivery_date: '2025-09-20T14:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-40088990
            order_id: THD-4008899
            sku: APPL-7784
            product_name: TechHome Electric Dryer 7.4 cu ft
            quantity: 1
            base_price: 899
            discount_amount: 0
            final_price: 899
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-40088990
            order_id: THD-4008899
            customer_id: CUS-00752001
            amount: 899
            status: authorized
            payment_method: Visa ending in 7741
            transaction_date: '2025-09-15T09:35:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: IJ-4008899
            order_id: THD-4008899
            customer_id: CUS-00752001
            service_type: appliance_basic
            scheduled_date: '2025-10-03T09:00:00Z'
            technician_id: null
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-7784
            available_quantity: 35
            reserved_quantity: 1
            warehouse_location: London-E14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-7784
            name: TechHome Electric Dryer 7.4 cu ft
            category: appliances
            brand: TechHome
            base_price: 899
            weight_lbs: 162
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-00752001
            email: jordan.evans@example.com
            name: Jordan Evans
            phone: +44-20-7456-1122
            registration_date: '2025-08-20T10:00:00Z'
            customer_tier: standard
            lifetime_value: 899
            total_orders: 1
            customer_score: 52
            behavioral_segment: opportunist
            acquisition_source: organic_search
            discount_usage_rate: 0.1
        golden_test_case:
          tool_interactions:
          - tool: zendesk_get_items
            parameters:
              $top: 1
              $skip: 0
              table: users
              $filter: email eq 'jordan.evans@example.com'
              $select: id,name,email
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: 5
              $skip: 0
              table: tickets
              $filter: requester_id eq '92001' and (status eq 'open' or status eq 'pending' or status eq 'hold')
              $select: id,subject,status
              $orderby: created_at desc
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Installation reschedule due to weather + compensation
                priority: normal
                assignee_id: '2'
                description: Order THD-4008899. Original install 2025-10-03 09:00 at 42 Baker Street, London blocked by severe weather. Customer requests reschedule to 2025-10-12 09:00 and asks about compensation.
                requester_id: '92001'
                organization_id: null
              table: tickets
          - tool: get_installation_job
            parameters:
              job_id: IJ-4008899
              order_id: THD-4008899
          - tool: reschedule_installation
            parameters:
              job_id: IJ-4008899
              reschedule_reason: weather_delay
              new_scheduled_date: '2025-10-12T09:00:00.000Z'
          - tool: create_refund
            parameters:
              amount: 6.45
              order_id: THD-4008899
              customer_id: CUS-00752001
              refund_reason: late_delivery_compensation
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: 'Installation rescheduled to 2025-10-12 09:00 (reason: weather_delay). Refund $6.45 created under late_delivery_compensation. Customer notified with details and apology.'
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST016_006(x: TestContext, judge: Judge):
    """!
    query: Hi, my email id is [sarah.martinez@email.com](mailto:sarah.martinez@email.com). I have called to confirm my installation appointment for my Samsung front-load washing machine with order id ORD-20000001 that's scheduled for October 5th. This morning I got a call from support regarding a potential reschedule of installation to October 14th due to severe weather conditions. Can you please help?
    user_context: |2+


      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0234
            verified: true
            active: true
            created_at: '2024-03-15T10:30:00Z'
            updated_at: '2024-03-15T10:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '6'
            subject: Order status inquiry
            description: Customer inquired about delivery status for previous order
            status: solved
            priority: normal
            type: incident
            requester_id: '6'
            assignee_id: '2'
            created_at: '2025-09-20T10:00:00Z'
            updated_at: '2025-09-21T14:30:00Z'
            due_at: null
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-09-12T14:30:00Z'
            status: installation_scheduled
            subtotal_amount: 1249
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1249
            shipping_address_line1: 456 Maple Avenue
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-20000001
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: FedEx
            tracking_number: TRK-200000000001
            ship_date: '2025-09-14T09:00:00Z'
            estimated_delivery_date: '2025-09-17T17:00:00Z'
            actual_delivery_date: '2025-09-17T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-17T17:00:00Z'
            last_update: '2025-09-17T15:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: APPL-5567
            product_name: Samsung WF45R6100AW Front Load Washing Machine
            quantity: 1
            base_price: 1249
            discount_amount: 0
            final_price: 1249
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 1378
            status: authorized
            payment_method: Visa ending in 7890
            transaction_date: '2025-09-12T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: APPL-5567
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-09-17T00:00:00Z'
            end_date: '2028-09-17T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            service_type: appliance_basic
            scheduled_date: '2025-10-05T10:00:00Z'
            technician_id: TECH-0067
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-5567
            available_quantity: 8
            reserved_quantity: 1
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-5567
            name: Samsung WF45R6100AW Front Load Washing Machine
            category: appliances
            brand: Samsung
            base_price: 1249
            weight_lbs: 225
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-20000001
            customer_id: CUS-20000001
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 1850
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0234
            registration_date: '2024-03-15T10:30:00Z'
            customer_tier: plus_member
            lifetime_value: 3250.75
            total_orders: 12
            customer_score: 95
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.25
        golden_test_case:
          tool_interactions:
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'sarah.martinez@email.com'
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Installation reschedule due to weather delay
                priority: high
                assignee_id: '2'
                description: 'Installation for Samsung WF45R6100AW washing machine (order ORD-20000001) scheduled for October 5th must be rescheduled to October 14th due to severe weather. Customer eligible for 10% refund of installation cost as compensation per policy. '
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: reschedule_installation
            parameters:
              job_id: JOB-20000001
              reschedule_reason: weather_delay
              new_scheduled_date: '2025-10-14T10:00:00Z'
          - tool: create_refund
            parameters:
              amount: 12.9
              order_id: ORD-20000001
              customer_id: CUS-20000001
              refund_reason: late_delivery_compensation
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: Installation rescheduled to October 14th due to weather delay. $12.90 refund issued as compensation as per policy.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST017_001(x: TestContext, judge: Judge):
    """!
    query: Hi, my email id is [michael.rodriguez@email.com](mailto:michael.rodriguez@email.com).I had a built-in dishwasher (order ORD-10000025) installed about two months ago, and now water is leaking from underneath during wash cycles. I think the installer didn't secure the water supply line properly. Can you schedule a technician visit tomorrow around 2 pm to get the issue fixed?
    user_context: |2+


      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-03-15T09:30:00Z'
            updated_at: '2024-03-15T09:30:00Z'
          zendesk_organizations: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000025
            customer_id: CUS-10000015
            order_date: '2025-07-26T14:30:00Z'
            status: delivered
            subtotal_amount: 799
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 799
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000025
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000025
            order_id: ORD-10000025
            carrier: FedEx
            tracking_number: TRK-100000000025
            ship_date: '2025-07-28T09:00:00Z'
            estimated_delivery_date: '2025-08-02T17:00:00Z'
            actual_delivery_date: '2025-08-02T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000025
            shipment_id: SHP-10000025
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-08-02T17:00:00Z'
            last_update: '2025-08-02T15:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000025
            order_id: ORD-10000025
            sku: APPL-7729
            product_name: Built-in Dishwasher Premium Series
            quantity: 1
            base_price: 799
            discount_amount: 0
            final_price: 799
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000025
            order_id: ORD-10000025
            customer_id: CUS-10000015
            amount: 928
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2025-07-26T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000025
            order_id: ORD-10000025
            customer_id: CUS-10000015
            service_type: appliance_basic
            scheduled_date: '2025-08-02T10:00:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2025-08-02T14:30:00Z'
            workmanship_warranty_end: '2025-10-31T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-7729
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-7729
            name: Built-in Dishwasher Premium Series
            category: appliances
            brand: KitchenAid
            base_price: 799
            weight_lbs: 75
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2024-03-15T09:30:00Z'
            customer_tier: standard
            lifetime_value: 1250.75
            total_orders: 4
            customer_score: 78
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Dishwasher installation leak - water supply line issue
                priority: high
                assignee_id: '2'
                description: Customer reports water leaking from under built-in dishwasher during wash cycles. Believes installer did not secure water supply line properly. Installation completed 60 days ago, within workmanship warranty. Scheduling corrective service.
                requester_id: '15'
                organization_id: null
              table: tickets
          - tool: reschedule_installation
            parameters:
              job_id: JOB-10000025
              reschedule_reason: workmanship_issue
              new_scheduled_date: '2025-10-02T14:00:00Z'
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST017_002(x: TestContext, judge: Judge):
    """!
    query: "Hi, I’m following up on the washer installation issue that I reported yesterday. During the drain cycle, water backs up and spills on the floor. I think the drain hose wasn’t connected properly. \n\nPlease book an appointment for some technicians to visit and fix the issue. Thanks"
    user_context: |-
      Background about yourself:

      - Name: Jane Doe
      - Membership: TechHome Plus

      Situation

      - You reported this yesterday and are following up.
      - During drain cycles, water backs up and spills on the floor.
      - You believe the drain hose was connected improperly during installation.
      - Installation was 42 days ago (within workmanship warranty).

      Goal

      - Get a free corrective visit under the 90-day workmanship warranty.

      If the agent asks

      - Email: [customer@example.com](mailto:customer@example.com)
      - Order number: ORD-49302
      - Ticket number (if asked): “I don’t know / don’t have it handy but I reported it yesterday”

      Scheduling preference

      - Ask for 2025-10-05, 09:00–12:00.

      If the agent suggests a return or product warranty

      - Say: “This is an installation workmanship problem. I’d like a technician correction under the workmanship warranty.”

      Finally

      - When they confirm a no-charge visit and the time window, thank them and end the chat.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10001'
            name: Jane Doe
            email: customer@example.com
            role: end-user
            organization_id: null
            phone: null
            verified: true
            active: true
            created_at: '2024-05-01T10:00:00Z'
            updated_at: '2024-05-01T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '70021'
            subject: Washer installation issue – water backs up during drain
            description: Customer reports water spilling on floor; likely improper drain hose connection. Following up after initial report.
            status: open
            priority: high
            type: incident
            requester_id: '10001'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-30T10:00:00Z'
            updated_at: '2025-09-30T10:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-49302
            customer_id: CUS-10001
            order_date: '2025-08-13T10:00:00Z'
            status: delivered
            subtotal_amount: 1149
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1278
            shipping_address_line1: 123 Maple St
            shipping_address_city: Springfield
            shipping_address_state: CA
            shipping_address_zip: '90210'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-88001
          external_retail_toolset_oms_models_shipments:
          - id: SHP-44001
            order_id: ORD-49302
            carrier: TechHome Logistics
            tracking_number: TRK-88331
            ship_date: '2025-08-18T08:00:00Z'
            estimated_delivery_date: '2025-08-20T17:00:00Z'
            actual_delivery_date: '2025-08-20T12:00:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-88331
            shipment_id: SHP-44001
            carrier: TechHome Logistics
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-08-20T17:00:00Z'
            last_update: '2025-08-20T12:00:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: OLI-1
            order_id: ORD-49302
            sku: APPL-5521
            product_name: Front-Load Washing Machine
            quantity: 1
            base_price: 1149
            discount_amount: 0
            final_price: 1149
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: PAY-70001
            order_id: ORD-49302
            customer_id: CUS-10001
            amount: 1278
            status: authorized
            payment_method: Visa ending in 1234
            transaction_date: '2025-08-13T10:05:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WARR-5521-ORD-49302
            order_id: ORD-49302
            sku: APPL-5521
            customer_id: CUS-10001
            warranty_type: manufacturer
            start_date: '2025-08-13T00:00:00Z'
            end_date: '2028-08-13T23:59:59Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-88001
            order_id: ORD-49302
            customer_id: CUS-10001
            service_type: appliance_basic
            scheduled_date: '2025-08-20T10:00:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2025-08-20T15:00:00Z'
            workmanship_warranty_end: '2025-11-18T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products: []
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10001
            email: customer@example.com
            name: Jane Doe
            phone: null
            registration_date: '2024-05-01T10:00:00Z'
            customer_tier: plus_member
            lifetime_value: 2500
            total_orders: 2
            customer_score: 80
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.3
        golden_test_case:
          tool_interactions:
          - tool: reschedule_installation
            parameters:
              job_id: JOB-88001
              reschedule_reason: workmanship_issue
              new_scheduled_date: '2025-10-05T09:00:00.000Z'
          - tool: zendesk_update_item
            parameters:
              id: '70021'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                priority: high
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST017_003(x: TestContext, judge: Judge):
    """!
    query: Hi, I had a French Door Refrigerator (order ORD-10000015) delivered and installed about a month ago. Right after the installation was completed, I noticed there were deep scratches on the side panel and a dent on the door, which I believe were caused by the technician during installation. Can you help me get this fixed? I am available on October 15 at 10:00 AM.
    user_context: |-
      Rules:

      - Do not invent or provide any data not present in the provided context.
      - Do not change your goal or switch topics.
      - If asked for the same info, provide it again.
      - Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Michael Thompson
            email: michael.thompson@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2023-05-12T14:30:00Z'
            updated_at: '2025-09-23T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '15'
            requester_id: '15'
            assignee_id: '2'
            subject: Membership question
            description: Customer asked about TechHome Plus membership benefits and eligibility. Clarification was provided and the issue was resolved.
            status: solved
            type: incident
            priority: urgent
            tags: []
            organization_id: null
            created_at: '2025-09-23T10:00:00Z'
            updated_at: '2025-09-23T10:10:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-08-26T10:15:00Z'
            status: delivered
            subtotal_amount: 2299
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 2428
            shipping_address_line1: 789 Oak Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000015
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: FedEx
            tracking_number: TRK-100000000015
            ship_date: '2025-08-27T09:00:00Z'
            estimated_delivery_date: '2025-09-02T17:00:00Z'
            actual_delivery_date: '2025-09-02T14:20:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000015
            shipment_id: SHP-10000015
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-02T17:00:00Z'
            last_update: '2025-09-02T14:20:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: APPL-8834
            product_name: French Door Refrigerator
            quantity: 1
            base_price: 2299
            discount_amount: 0
            final_price: 2299
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            amount: 2428
            status: authorized
            payment_method: Visa ending in 7892
            transaction_date: '2025-08-26T10:15:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            service_type: appliance_basic
            scheduled_date: '2025-09-02T10:00:00Z'
            technician_id: TECH-0067
            status: completed
            completion_date: '2025-09-02T15:30:00Z'
            workmanship_warranty_end: '2025-12-01T23:59:59Z'
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-8834
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-8834
            name: French Door Refrigerator
            category: appliances
            brand: Samsung
            base_price: 2299
            weight_lbs: 315
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: michael.thompson@email.com
            name: Michael Thompson
            phone: +1-555-0198
            registration_date: '2023-05-12T14:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 18
            customer_score: 88
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: michael.thompson@email.com
              customer_id: null
          - tool: get_order
            parameters:
              order_id: ORD-10000015
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'michael.thompson@email.com'
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Installation damage to refrigerator - corrective service needed
                priority: urgent
                assignee_id: '2'
                description: Customer reports deep scratches and a dent caused by technician during installation of refrigerator (order ORD-10000015). Customer requests corrective service. Customer is available Oct 15 at 10:00 AM.
                requester_id: '15'
                organization_id: null
              table: tickets
          - tool: reschedule_installation
            parameters:
              job_id: JOB-10000015
              reschedule_reason: workmanship_issue
              new_scheduled_date: '2025-10-15T10:00:00Z'
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: incident
                due_at: null
                status: hold
                subject: '"Installation damage to refrigerator - corrective service needed'
                priority: urgent
                assignee_id: '2'
                description: deep scratches on side panel and dent on the door. Issue is covered under 90-day workmanship warranty. Corrective service appointment scheduled.
                requester_id: '15'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST017_005(x: TestContext, judge: Judge):
    """!
    query: 'I''m following up on my open ticket about the dishwasher I ordered (order ID: ORD-20000001). Water is leaking from under the dishwasher during wash cycles, and it looks like the leak is coming from the connection point. The installation was completed about 121 days ago, but I just noticed this issue. Can you help me get this fixed under the workmanship warranty?'
    user_context: |2+


      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2023-08-15T14:30:00Z'
            updated_at: '2023-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '10'
            subject: Dishwasher issues
            description: Customer initially reported dishwasher issues.
            status: open
            priority: high
            type: incident
            requester_id: '6'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-29T13:00:00Z'
            updated_at: '2025-09-29T13:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-05-26T10:15:00Z'
            status: delivered
            subtotal_amount: 749
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 878
            shipping_address_line1: 2847 Oak Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-20000001
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: FedEx
            tracking_number: TRK-200000000001
            ship_date: '2025-05-27T09:30:00Z'
            estimated_delivery_date: '2025-06-02T17:00:00Z'
            actual_delivery_date: '2025-06-02T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-06-02T17:00:00Z'
            last_update: '2025-06-02T15:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: APPL-6638
            product_name: Built-in Dishwasher Premium Series
            quantity: 1
            base_price: 749
            discount_amount: 0
            final_price: 749
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 878
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2025-05-26T10:15:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: APPL-6638
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-05-26T10:15:00Z'
            end_date: '2028-05-25T10:15:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            service_type: appliance_basic
            scheduled_date: '2025-06-02T10:00:00Z'
            technician_id: TECH-0023
            status: completed
            completion_date: '2025-06-02T15:45:00Z'
            workmanship_warranty_end: '2025-08-31T23:59:59Z'
            service_cost: 129.0
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-6638
            available_quantity: 8
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-6638
            name: Built-in Dishwasher Premium Series
            category: appliances
            brand: KitchenAid
            base_price: 749
            weight_lbs: 73
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-20000001
            customer_id: CUS-20000001
            membership_type: plus
            start_date: '2024-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 1250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2023-08-15T14:30:00Z'
            customer_tier: plus_member
            lifetime_value: 2850.75
            total_orders: 12
            customer_score: 78
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: get_installation_job
            parameters:
              job_id: JOB-20000001
              order_id: null
          - tool: file_warranty_claim
            parameters:
              contract_id: WCT-20000001
              customer_id: CUS-20000001
              warranty_issue_type: component_failed
          - tool: zendesk_update_item
            parameters:
              id: '10'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: high
                assignee_id: null
                description: Customer reported water leaking from under dishwasher at connection point. Workmanship warranty expired; filed manufacturer warranty claim for leak (component_failed).
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST018_002(x: TestContext, judge: Judge):
    """!
    query: 'Hi, I''m following up on my open ticket #87 about the installation for my Samsung Front-Load Washing Machine (order ORD-10000015). I was considering cancelling the installation scheduled for October 4th to save money. Can you tell me exactly how much I would get back if I cancel just the installation?'
    user_context: |-
      **Context:** You are Sarah Martinez (`customer_id: CUS-`10000015), a TechHome Plus member. You placed order **ORD-**10000015 for a Samsung Front-Load Washing Machine. It was delivered 12 days ago. You have an installation appointment scheduled for **October 4th**. You previously opened a ticket (**#87**) asking about the process.

      **Your Goal:** You are considering cancelling the installation service to save money, but you are hesitant and need to know the financial implications first.

      **Specific Information to Provide (Only if asked):**

      - **Order ID:** ORD-10000015

      **Interaction Guidelines:**

      - **Do not reveal your membership tier** unless the agent specifically asks for it.
      - If the agent explains that cancelling the installation will trigger a **standard shipping charge** (e.g., $55.00) that reduces your refund, decide to **keep the installation**.
          - _Response:_ "Oh, I didn't know about the shipping charge. In that case, it's not worth it. I'll keep the installation appointment."
      - If the agent immediately agrees to cancel without explaining the fees/trade-off, **do not confirm**.
          - _Response:_ "Wait, I'm not sure I want to cancel yet, I just wanted to understand what happens first. Are there any fees?"
      - Your final decision must be to **keep the appointment** as scheduled.

      **Rules for Behavior:**

      - Do not invent or provide any data not present in the provided context.
      - Do not change your goal or switch topics.
      - If asked for the same info, provide it again.
      - Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: null
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2023-08-15T14:30:00Z'
            updated_at: '2025-09-29T11:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '87'
            subject: Installation service inquiry
            description: Customer asking about installation process for washing machine order ORD-10000015
            status: open
            priority: high
            type: incident
            requester_id: '15'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-29T11:00:00Z'
            updated_at: '2025-10-01T13:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-09-14T10:15:00Z'
            status: installation_scheduled
            subtotal_amount: 1149
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1278
            shipping_address_line1: 742 Oak Ridge Drive
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78704'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000015
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: FedEx
            tracking_number: TRK-100000000015
            ship_date: '2025-09-16T09:30:00Z'
            estimated_delivery_date: '2025-09-19T17:00:00Z'
            actual_delivery_date: '2025-09-19T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: APPL-6692
            product_name: Samsung WF45R6100AW Front Load Washing Machine
            quantity: 1
            base_price: 1149
            discount_amount: 0
            final_price: 1149
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            amount: 1278
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-09-14T10:15:30Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            service_type: appliance_basic
            scheduled_date: '2025-10-04T14:00:00Z'
            technician_id: TECH-0067
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-6692
            name: Samsung WF45R6100AW Front Load Washing Machine
            category: appliances
            brand: Samsung
            base_price: 1149
            weight_lbs: 219
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000015
            customer_id: CUS-10000015
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 3250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2023-08-15T14:30:00Z'
            customer_tier: plus_member
            lifetime_value: 2850.75
            total_orders: 12
            customer_score: 78
            behavioral_segment: regular
            acquisition_source: email_marketing
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: zendesk_update_item
            parameters:
              id: '87'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: high
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST018_003(x: TestContext, judge: Judge):
    """!
    query: Hi, my customer ID is CUS-20000001, I want to cancel the installation service for my Samsung French Door Refrigerator (order ID ORD-20000001) scheduled for October 8th. I hired my own contractor and don't need the installation anymore. I am aware that I will be refunded USD 129 installation cost and will need to pay USD55 shipping cost, please proceed with the cancellation.
    user_context: |-
      —------

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      —------
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Michael Rodriguez
            email: michael.rodriguez@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0789
            verified: true
            active: true
            created_at: '2022-03-15T10:30:00Z'
            updated_at: '2025-09-27T14:20:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '6'
            subject: Product specifications question
            description: Customer asked about refrigerator dimensions and energy efficiency ratings
            status: solved
            priority: urgent
            type: incident
            requester_id: '6'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-23T11:30:00Z'
            updated_at: '2025-09-27T16:45:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-20000001
            customer_id: CUS-20000001
            order_date: '2025-09-20T16:45:00Z'
            status: installation_scheduled
            subtotal_amount: 2299
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 2428
            shipping_address_line1: 789 Oak Ridge Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-20000001
          external_retail_toolset_oms_models_shipments:
          - id: SHP-20000001
            order_id: ORD-20000001
            carrier: FedEx
            tracking_number: TRK-200000000001
            ship_date: '2025-09-22T09:30:00Z'
            estimated_delivery_date: '2025-09-25T17:00:00Z'
            actual_delivery_date: '2025-09-25T14:15:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-200000000001
            shipment_id: SHP-20000001
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-25T17:00:00Z'
            last_update: '2025-09-25T14:15:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-20000001
            order_id: ORD-20000001
            sku: APPL-8821
            product_name: Samsung 28 cu ft French Door Refrigerator with Ice Maker
            quantity: 1
            base_price: 2299
            discount_amount: 0
            final_price: 2299
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            amount: 2428
            status: authorized
            payment_method: Visa ending in 7890
            transaction_date: '2025-09-20T16:45:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-20000001
            order_id: ORD-20000001
            sku: APPL-8821
            customer_id: CUS-20000001
            warranty_type: manufacturer
            start_date: '2025-09-25T00:00:00Z'
            end_date: '2028-09-25T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-20000001
            order_id: ORD-20000001
            customer_id: CUS-20000001
            service_type: appliance_basic
            scheduled_date: '2025-10-08T10:00:00Z'
            technician_id: TECH-0067
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-8821
            available_quantity: 8
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-8821
            name: Samsung 28 cu ft French Door Refrigerator with Ice Maker
            category: appliances
            brand: Samsung
            base_price: 2299
            weight_lbs: 312
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-20000001
            email: michael.rodriguez@example.com
            name: Michael Rodriguez
            phone: +1-555-0789
            registration_date: '2022-03-15T10:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 28
            customer_score: 95
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                type: incident
                due_at: null
                status: open
                subject: Installation cancellation for order ORD-20000001
                priority: urgent
                assignee_id: '2'
                description: Customer requested cancellation of installation service for Samsung French Door Refrigerator. Refunded $129.00 installation cost and charged $55.00 shipping as per policy.
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: cancel_installation
            parameters:
              job_id: JOB-20000001
              order_id: ORD-20000001
              cancellation_reason: customer_wants_ship_only
          - tool: create_refund
            parameters:
              amount: 129
              order_id: ORD-20000001
              customer_id: CUS-20000001
              refund_reason: order_cancelled
          - tool: charge_customer
            parameters:
              amount: 55
              order_id: ORD-20000001
              customer_id: CUS-20000001
              charge_reason: installation_cancelled_shipping
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST018_005(x: TestContext, judge: Judge):
    """!
    query: Hi, the technician is here installing my Bosch 800 Series Built-In Dishwasher, but I've changed my mind and want to cancel the installation. Can you stop the installation and refund the service cost?
    user_context: "You are Sarah Martinez, a Plus member of TechHome Direct with email address [sarah.martinez@email.com](mailto:sarah.martinez@email.com)\n\nYour intent is to request cancellation of a installation that is in progress and request a refund of the installation cost for the order, the order number is ORD-10000010. If the Agent says the installation cannot be cancelled try 2 times to cancel \n\n—------\n\nRules:\n\nDo not invent or provide any data not present in the provided context.\n\nDo not change your goal or switch topics.\n\nIf asked for the same info, provide it again.\n\nRemain focused, clear, and patient.\n\n—------"
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-03-15T09:30:00Z'
            updated_at: '2024-03-15T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '10'
            subject: Delivery timing question for dishwasher order
            description: Customer asking about expected delivery date for their Bosch dishwasher order
            status: open
            priority: normal
            type: incident
            requester_id: '10'
            assignee_id: '2'
            organization_id: '1'
            tags:
            - delivery
            - timing
            created_at: '2025-09-28T14:30:00Z'
            updated_at: '2025-09-28T14:30:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 23118465221930
            ticket_id: 10
            author_id: 10
            body: Customer asking about expected delivery date for their Bosch dishwasher order
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">Customer asking about expected delivery date for their Bosch dishwasher order</p></div>
            public: true
            created_at: '2025-09-28T14:30:00Z'
            ItemInternalId: 630d7175-2bb9-41d9-9131-d5f2e57af9f0
            key: '23118465221930'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000010
            customer_id: CUS-10000010
            order_date: '2025-09-26T11:15:00Z'
            status: installation_scheduled
            subtotal_amount: 849
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 978
            shipping_address_line1: 456 Maple Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000010
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000010
            order_id: ORD-10000010
            carrier: FedEx
            tracking_number: TRK-100000000010
            ship_date: '2025-09-27T09:30:00Z'
            estimated_delivery_date: '2025-09-30T17:00:00Z'
            actual_delivery_date: '2025-09-30T15:45:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000010
            shipment_id: SHP-10000010
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-30T17:00:00Z'
            last_update: '2025-09-30T15:45:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000010
            order_id: ORD-10000010
            sku: APPL-7738
            product_name: Bosch 800 Series Built-In Dishwasher
            quantity: 1
            base_price: 849
            discount_amount: 0
            final_price: 849
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000010
            order_id: ORD-10000010
            customer_id: CUS-10000010
            amount: 978
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2025-09-26T11:15:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000010
            order_id: ORD-10000010
            sku: APPL-7738
            customer_id: CUS-10000010
            warranty_type: manufacturer
            start_date: '2025-09-30T00:00:00Z'
            end_date: '2028-09-30T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000010
            order_id: ORD-10000010
            customer_id: CUS-10000010
            service_type: appliance_basic
            scheduled_date: '2025-10-01T10:00:00Z'
            technician_id: TECH-0067
            status: in_progress
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-7738
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-7738
            name: Bosch 800 Series Built-In Dishwasher
            category: appliances
            brand: Bosch
            base_price: 849
            weight_lbs: 79
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000010
            customer_id: CUS-10000010
            membership_type: plus
            start_date: '2024-01-01T00:00:00Z'
            end_date: '2024-12-31T23:59:59Z'
            status: active
            points_balance: 1850
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2024-03-15T09:30:00Z'
            customer_tier: plus_member
            lifetime_value: 2150.75
            total_orders: 6
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.35
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: sarah.martinez@email.com
              customer_id: null
          - tool: get_order
            parameters:
              order_id: ORD-10000010
          - tool: get_installation_job
            parameters:
              job_id: null
              order_id: ORD-10000010
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'sarah.martinez@email.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '10'
              $select: null
              $orderby: null
          - tool: zendesk_update_item
            parameters:
              id: '10'
              item:
                tags: null
                type: incident
                due_at: null
                status: solved
                subject: Customer requested installation cancellation
                priority: high
                assignee_id: '2'
                description: Customer requested cancellation of installation for Bosch 800 Series dishwasher (order ORD-10000010, job JOB-10000010) while technician is in progress. As per company policy, installation cannot be cancelled or refunded once in progress. Offered further assistance for any post-installation concerns.
                requester_id: '10'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST025_001(x: TestContext, judge: Judge):
    """!
    query: Hi, I’d like to cancel my order ORD-90077 for the TechPro 14-inch Laptop. I changed my mind and don’t want to complete the purchase.
    user_context: |-
      —------

      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      —------
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Jamie Reed
            email: jamie.reed@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-08-15T14:30:00Z'
            updated_at: '2024-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-90077
            customer_id: CUS-10204587
            order_date: '2025-10-01T05:00:00Z'
            status: pending_payment
            subtotal_amount: 1199
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 15
            total_amount: 1214
            shipping_address_line1: 742 Maple Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments: []
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LI-99881
            order_id: ORD-90077
            sku: COMP-5563
            product_name: TechPro 14-inch Laptop
            quantity: 1
            base_price: 1199
            discount_amount: 0
            final_price: 1199
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-90077
            order_id: ORD-90077
            customer_id: CUS-10204587
            amount: 1214
            status: pending_authorization
            payment_method: Visa ending in 7892
            transaction_date: '2025-10-01T05:00:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: COMP-5563
            available_quantity: 12
            reserved_quantity: 1
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: COMP-5563
            name: TechPro 14-inch Laptop
            category: computing
            brand: TechPro
            base_price: 1199
            weight_lbs: 4.3
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10204587
            email: jamie.reed@example.com
            name: Jamie Reed
            phone: +1-555-0198
            registration_date: '2024-08-15T14:30:00Z'
            customer_tier: standard
            lifetime_value: 1850.75
            total_orders: 2
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.35
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10204587
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'jamie.reed@example.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '6'
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Customer requests order cancellation
                priority: normal
                assignee_id: '2'
                description: Jamie Reed requested to cancel order ORD-90077 (pending_payment
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: get_order
            parameters:
              order_id: ORD-90077
          - tool: get_payment_status
            parameters:
              order_id: ORD-90077
          - tool: cancel_order
            parameters:
              order_id: ORD-90077
              cancellation_reason: customer_request
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: normal
                assignee_id: null
                description: Order ORD-90077 cancelled successfully per customer request.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST025_002(x: TestContext, judge: Judge):
    """!
    query: Hi, I’d like to cancel my order ORD-10000015 for the Samsung Galaxy Tab A9+ 11-inch Tablet. I placed it about 6 hours ago, but I found the same product for a lower price elsewhere. My email is [sarah.martinez@email.com](mailto:sarah.martinez@email.com). I am following up on a previously created  ticket.
    user_context: |+
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-02-10T09:30:00Z'
            updated_at: '2024-02-10T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '15'
            subject: Question about tablet specifications
            description: Customer asking about battery life and storage options for Samsung Galaxy Tab A9+ 11-inch Tablet
            status: open
            priority: high
            type: incident
            requester_id: '15'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-10-01T12:00:00Z'
            updated_at: '2025-10-01T12:00:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 23118465221925
            ticket_id: 15
            author_id: 15
            body: Hi, I have a question about the Samsung Galaxy Tab A9+ 11-inch Tablet I'm considering. Can you tell me about the battery life and available storage options?
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">Hi, I have a question about the Samsung Galaxy Tab A9+ 11-inch Tablet I'm considering. Can you tell me about the battery life and available storage options?</p></div>
            public: true
            created_at: '2025-10-01T12:00:00Z'
            ItemInternalId: 625d7175-2bb9-41d9-9131-d5f2e57af9fc
            key: '23118465221925'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-10-01T07:00:00Z'
            status: processing
            subtotal_amount: 649
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 649
            shipping_address_line1: 2847 Oak Ridge Drive
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78704'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments: []
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: TAB-8874
            product_name: Samsung Galaxy Tab A9+ 11-inch Tablet
            quantity: 1
            base_price: 649
            discount_amount: 0
            final_price: 649
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            amount: 649
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2025-10-01T07:02:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: TAB-8874
            available_quantity: 25
            reserved_quantity: 5
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: TAB-8874
            name: Samsung Galaxy Tab A9+ 11-inch Tablet
            category: computing
            brand: Samsung
            base_price: 649
            weight_lbs: 1.4
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000015
            customer_id: CUS-10000015
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 3250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2024-02-10T09:30:00Z'
            customer_tier: plus_member
            lifetime_value: 2150.75
            total_orders: 12
            customer_score: 78
            behavioral_segment: regular
            acquisition_source: email_marketing
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: sarah.martinez@email.com
              customer_id: null
          - tool: get_order
            parameters:
              order_id: ORD-10000015
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '15' and status eq 'open'
              $select: null
              $orderby: null
          - tool: cancel_order
            parameters:
              order_id: ORD-10000015
              cancellation_reason: customer_request
          - tool: zendesk_update_item
            parameters:
              id: '15'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: Order ORD-10000015 cancelled per customer request. Refund will be processed. Confirmation email will be sent.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST025_003(x: TestContext, judge: Judge):
    """!
    query: The customer wants to cancel an order that is currently in processing status. They accidentally ordered the wrong camera model and now want the order cancelled.
    user_context: |-
      Your name is John Doe and your email is [john.doe@email.com](mailto:john.doe@email.com).

      **General rules**

      - Do not invent or provide any data that is not present in the provided context.
      - Do not change your goal or switch topics.
      - If the agent asks again for the same information, provide it again.
      - Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '9001'
            name: John Doe
            email: john.doe@email.com
            role: end-user
            phone: +1-555-0199
            verified: true
            active: true
            created_at: '2024-03-15T14:30:00Z'
            updated_at: '2024-03-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '5001'
            subject: Shipping question for older order
            description: Customer asked about shipping on previous order
            status: solved
            priority: normal
            type: incident
            requester_id: '9001'
            assignee_id: '2'
            created_at: '2025-09-29T10:00:00Z'
            updated_at: '2025-09-29T10:30:00Z'
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-90000001
            customer_id: CUS-90000001
            order_date: '2025-10-01T09:00:00Z'
            status: processing
            subtotal_amount: 1799
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1799
            shipping_address_line1: 123 Market Street
            shipping_address_city: Seattle
            shipping_address_state: WA
            shipping_address_zip: '98101'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments: []
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-90000001
            order_id: ORD-90000001
            sku: CAM-9923
            product_name: Mirrorless Camera
            quantity: 1
            base_price: 1799
            discount_amount: 0
            final_price: 1799
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-90000001
            order_id: ORD-90000001
            customer_id: CUS-90000001
            amount: 1799
            status: authorized
            payment_method: Visa ending in 4567
            transaction_date: '2025-10-01T09:00:15Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-90000001
            order_id: ORD-90000001
            sku: CAM-9923
            customer_id: CUS-90000001
            warranty_type: manufacturer
            start_date: '2025-10-01T09:00:00Z'
            end_date: '2026-10-01T09:00:00Z'
            coverage_details: Covers defects in materials and workmanship for electronics
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: CAM-9923
            available_quantity: 12
            reserved_quantity: 1
            warehouse_location: Seattle-E14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: CAM-9923
            name: Mirrorless Camera
            category: electronics
            brand: Canon
            base_price: 1799
            weight_lbs: 3.1
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-90000001
            email: john.doe@email.com
            name: John Doe
            phone: +1-555-0199
            registration_date: '2024-03-15T14:20:00Z'
            customer_tier: vip
            lifetime_value: 8950.75
            total_orders: 5
            customer_score: 85
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.25
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Order cancellation request
                priority: urgent
                assignee_id: '2'
                description: Customer wants to cancel order ORD-90000001 because they ordered the wrong camera model.
                requester_id: '9001'
                organization_id: null
              table: tickets
          - tool: cancel_order
            parameters:
              order_id: ORD-90000001
              cancellation_reason: customer_request
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: incident
                due_at: null
                status: solved
                subject: null
                priority: urgent
                assignee_id: '2'
                description: null
                requester_id: '9001'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST025_004(x: TestContext, judge: Judge):
    """!
    query: I would like to cancel my order ORD-10000020 for the Bosch 24-inch Built-In Dishwasher, including the installation service. I placed the order about 10 hours ago, but I've decided to buy from a local store instead. Can you help me cancel everything?
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10010'
            name: Michael Rodriguez
            email: michael.rodriguez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-08-15T14:30:00Z'
            updated_at: '2024-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000020
            customer_id: CUS-10000010
            order_date: '2025-10-01T03:00:00Z'
            status: pending_payment
            subtotal_amount: 799
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 928
            shipping_address_line1: 456 Oak Street
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37203'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000020
          external_retail_toolset_oms_models_shipments: []
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000020
            order_id: ORD-10000020
            sku: APPL-6647
            product_name: Bosch 24-inch Built-In Dishwasher
            quantity: 1
            base_price: 799
            discount_amount: 0
            final_price: 799
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000020
            order_id: ORD-10000020
            customer_id: CUS-10000010
            amount: 928
            status: pending_authorization
            payment_method: Visa ending in 2847
            transaction_date: '2025-10-01T03:05:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000020
            order_id: ORD-10000020
            customer_id: CUS-10000010
            service_type: appliance_basic
            scheduled_date: '2025-10-08T10:00:00Z'
            technician_id: null
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-6647
            available_quantity: 12
            reserved_quantity: 1
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-6647
            name: Bosch 24-inch Built-In Dishwasher
            category: appliances
            brand: Bosch
            base_price: 799
            weight_lbs: 77
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: michael.rodriguez@email.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2024-08-15T14:30:00Z'
            customer_tier: standard
            lifetime_value: 0
            total_orders: 1
            customer_score: 65
            behavioral_segment: opportunist
            acquisition_source: online_search
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Order ORD-10000020 cancellation request - Bosch Dishwasher & Installation
                priority: normal
                assignee_id: '2'
                description: Customer requested cancellation of order ORD-10000020 (Bosch 24-inch Built-In Dishwasher) and associated installation JOB-10000020. Order was in pending_payment status, no payment captured, no refund required. Both order and installation have been canceled.
                requester_id: '10010'
                organization_id: null
              table: tickets
          - tool: get_order
            parameters:
              order_id: ORD-10000020
          - tool: cancel_installation
            parameters:
              job_id: JOB-10000020
              order_id: ORD-10000020
              cancellation_reason: customer_cancelled_order
          - tool: cancel_order
            parameters:
              order_id: ORD-10000020
              cancellation_reason: customer_request
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: incident
                due_at: null
                status: solved
                subject: Order ORD-10000020 cancellation request - Bosch Dishwasher & Installation
                priority: normal
                assignee_id: '2'
                description: Customer requested cancellation of order ORD-10000020 (Bosch 24-inch Built-In Dishwasher) and associated installation JOB-10000020. Order was in pending_payment status, no payment captured, no refund required. Both order and installation have been canceled.
                requester_id: '10010'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST025_006(x: TestContext, judge: Judge):
    """!
    query: 'Hi, I need to cancel my order ORD-10000005 for the Samsung Front-Load Washing Machine. My renovation project is postponed, so I won''t need the appliance or the installation service right now. Can you help me cancel the entire order? This is my email: [victoria.harrison@example.com](mailto:victoria.harrison@example.com).'
    user_context: |+
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Victoria Harrison
            email: victoria.harrison@example.com
            role: end-user
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2022-03-15T10:30:00Z'
            updated_at: '2022-03-15T10:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '6'
            subject: Product availability inquiry
            description: Customer asking about availability of Samsung washing machines
            status: solved
            priority: urgent
            type: incident
            requester_id: '6'
            assignee_id: '2'
            created_at: '2025-09-28T13:00:00Z'
            updated_at: '2025-09-28T15:30:00Z'
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000005
            customer_id: CUS-10000005
            order_date: '2025-10-01T06:00:00Z'
            status: processing
            subtotal_amount: 1249
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1378
            shipping_address_line1: 789 Maple Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000005
          external_retail_toolset_oms_models_shipments: []
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000005
            order_id: ORD-10000005
            sku: APPL-3349
            product_name: Samsung Front-Load Washing Machine 4.5 cu ft
            quantity: 1
            base_price: 1249
            discount_amount: 0
            final_price: 1249
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000005
            order_id: ORD-10000005
            customer_id: CUS-10000005
            amount: 1378
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-10-01T06:00:15Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000005
            order_id: ORD-10000005
            customer_id: CUS-10000005
            service_type: appliance_basic
            scheduled_date: '2025-10-08T10:00:00Z'
            technician_id: null
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-3349
            available_quantity: 12
            reserved_quantity: 1
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-3349
            name: Samsung Front-Load Washing Machine 4.5 cu ft
            category: appliances
            brand: Samsung
            base_price: 1249
            weight_lbs: 223
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000005
            email: victoria.harrison@example.com
            name: Victoria Harrison
            phone: +1-555-0198
            registration_date: '2022-03-15T10:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 28
            customer_score: 95
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: victoria.harrison@example.com
              customer_id: null
          - tool: get_order
            parameters:
              order_id: ORD-10000005
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'victoria.harrison@example.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: 10
              $skip: null
              table: tickets
              $filter: requester_id eq '6' and (status eq 'open' or status eq 'pending' or status eq 'hold')
              $select: null
              $orderby: null
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Order cancellation request - Samsung Front-Load Washing Machine
                priority: urgent
                assignee_id: '2'
                description: Customer requests full cancellation of order ORD-10000005 and associated installation service JOB-10000005 due to postponed renovation project.
                requester_id: '6'
                organization_id: null
              table: tickets
          - tool: cancel_installation
            parameters:
              job_id: JOB-10000005
              order_id: ORD-10000005
              cancellation_reason: customer_cancelled_order
          - tool: cancel_order
            parameters:
              order_id: ORD-10000005
              cancellation_reason: customer_request
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: incident
                due_at: null
                status: solved
                subject: Order cancellation confirmed - Samsung Front-Load Washing Machine
                priority: urgent
                assignee_id: '2'
                description: Order ORD-10000005 and associated installation JOB-10000005 successfully cancelled. No charges will be finalized as payment was only authorized. Customer notified and provided with refund details.
                requester_id: '6'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST026_002(x: TestContext, judge: Judge):
    """!
    query: Hi, my email id  is [sarah.martinez@email.com](mailto:sarah.martinez@email.com). I want to cancel my order for the Bosch 800 Series Built-In Dishwasher. It was delivered a few days ago, but I don't want it installed anymore. Can you please cancel the entire order and refund me?
    user_context: |-
      —------

      Rules:

      Do not invent or fabricate data.

      Do not change your goal or switch topics.

      If the agent asks for the Order ID, say that you don't remember it and ask the agent for the steps to find the Order ID. Share the correct Order ID ORD-10000015 following the agent's instructions.

      Be vague about the exact order and delivery dates, but don't answer with 'I don't know'.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      —------
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2024-03-15T10:30:00Z'
            updated_at: '2024-03-15T10:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '15'
            subject: Installation appointment inquiry
            description: Customer asking about scheduled installation date for dishwasher order
            status: open
            priority: high
            type: incident
            requester_id: '15'
            assignee_id: '2'
            tags: []
            created_at: '2025-09-29T11:15:00Z'
            updated_at: '2025-09-29T11:15:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-09-17T14:30:00Z'
            status: installation_scheduled
            subtotal_amount: 849
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 849
            shipping_address_line1: 456 Maple Drive
            shipping_address_city: Nashville
            shipping_address_state: TN
            shipping_address_zip: '37215'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: JOB-10000015
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: FedEx
            tracking_number: TRK-100000000015
            ship_date: '2025-09-18T09:00:00Z'
            estimated_delivery_date: '2025-09-22T17:00:00Z'
            actual_delivery_date: '2025-09-22T15:30:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000015
            shipment_id: SHP-10000015
            carrier: FedEx
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-22T17:00:00Z'
            last_update: '2025-09-22T15:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: APPL-5529
            product_name: Bosch 800 Series Built-In Dishwasher
            quantity: 1
            base_price: 849
            discount_amount: 0
            final_price: 849
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            amount: 978
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2025-09-17T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000015
            order_id: ORD-10000015
            sku: APPL-5529
            customer_id: CUS-10000015
            warranty_type: manufacturer
            start_date: '2025-09-22T00:00:00Z'
            end_date: '2028-09-22T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for major appliances
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs:
          - id: JOB-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            service_type: appliance_basic
            scheduled_date: '2025-10-05T10:00:00Z'
            technician_id: TECH-0067
            status: scheduled
            completion_date: null
            workmanship_warranty_end: null
            service_cost: 129
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: APPL-5529
            available_quantity: 8
            reserved_quantity: 2
            warehouse_location: Memphis-A15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: APPL-5529
            name: Bosch 800 Series Built-In Dishwasher
            category: appliances
            brand: Bosch
            base_price: 849
            weight_lbs: 80
            is_refurbished: false
            warranty_period_days: 1095
            points_redemption_eligible: true
            requires_installation: true
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000015
            customer_id: CUS-10000015
            membership_type: plus
            start_date: '2025-01-01T00:00:00Z'
            end_date: '2025-12-31T23:59:59Z'
            status: active
            points_balance: 1250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2024-03-15T10:30:00Z'
            customer_tier: plus_member
            lifetime_value: 2850.75
            total_orders: 12
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.35
        golden_test_case:
          tool_interactions:
          - tool: create_rma
            parameters:
              order_id: ORD-10000015
              customer_id: CUS-10000015
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000015
              refund_amount: 849
              return_reason: changed_mind
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: cancel_installation
            parameters:
              job_id: JOB-10000015
              order_id: ORD-10000015
              cancellation_reason: customer_cancelled_order
          - tool: zendesk_update_item
            parameters:
              id: '15'
              item:
                tags: null
                type: incident
                due_at: null
                status: hold
                subject: Return initiated and installation cancelled for Bosch 800 Series Dishwasher order ORD-10000015
                priority: high
                assignee_id: '2'
                description: Customer requested order cancellation after delivery. Order cannot be cancelled, but return (RMA) initiated for Bosch 800 Series Dishwasher and installation appointment cancelled as per Plus member policy. Customer informed of next steps.
                requester_id: '15'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST026_003(x: TestContext, judge: Judge):
    """!
    query: Hi, I want to cancel my order ORD-10000087. I bought a 10-inch tablet, but I haven’t opened it and I don’t need it anymore.
    user_context: |-
      Rules:
      Do not invent or provide any data not present in the provided context.
      Do not change your goal or switch topics.
      If asked for the same info, provide it again.
      Remain focused, clear, and patient.

      Order ID is **"ORD-10000087"** . If the agent asks you to confirm the order number or the product details, repeat the information as needed
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '87'
            name: Victoria Chen
            email: victoria.chen@example.com
            role: end-user
            phone: +1-555-0187
            verified: true
            active: true
            created_at: '2022-03-15T09:30:00Z'
            updated_at: '2022-03-15T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '87'
            subject: Membership question
            description: Customer asked about membership benefits
            status: solved
            priority: normal
            type: incident
            requester_id: '87'
            assignee_id: '2'
            tags: []
            created_at: '2025-09-26T10:00:00Z'
            updated_at: '2025-09-26T11:30:00Z'
            solved_at: '2025-09-26T11:30:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000087
            customer_id: CUS-10000087
            order_date: '2025-09-13T14:30:00Z'
            status: delivered
            subtotal_amount: 549
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 549
            shipping_address_line1: 789 Oak Boulevard
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000087
            order_id: ORD-10000087
            carrier: UPS
            tracking_number: TRK-100000000087
            ship_date: '2025-09-14T09:15:00Z'
            estimated_delivery_date: '2025-09-16T17:00:00Z'
            actual_delivery_date: '2025-09-16T15:22:00Z'
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000087
            shipment_id: SHP-10000087
            carrier: UPS
            status: delivered
            current_location: Customer Address
            estimated_delivery: '2025-09-16T17:00:00Z'
            last_update: '2025-09-16T15:22:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000087
            order_id: ORD-10000087
            sku: TAB-6681
            product_name: 10-inch Tablet
            quantity: 1
            base_price: 549
            discount_amount: 0
            final_price: 549
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000087
            order_id: ORD-10000087
            customer_id: CUS-10000087
            amount: 549
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-09-13T14:30:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000087
            order_id: ORD-10000087
            sku: TAB-6681
            customer_id: CUS-10000087
            warranty_type: manufacturer
            start_date: '2025-09-16T00:00:00Z'
            end_date: '2026-09-16T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: TAB-6681
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Memphis-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: TAB-6681
            name: 10-inch Tablet
            category: computing
            brand: TechBrand
            base_price: 549
            weight_lbs: 1.3
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000087
            email: victoria.chen@example.com
            name: Victoria Chen
            phone: +1-555-0187
            registration_date: '2022-03-15T09:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 28
            customer_score: 88
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: null
              customer_id: CUS-10000087
          - tool: get_order
            parameters:
              order_id: ORD-10000087
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Return request for order ORD-10000087
                priority: urgent
                assignee_id: '2'
                description: Customer requests cancellation but delivered. Initiating return.
                requester_id: '87'
                organization_id: null
              table: tickets
          - tool: create_rma
            parameters:
              order_id: ORD-10000087
              customer_id: CUS-10000087
              removal_fee: 0
              is_defective: false
              line_item_id: LIN-10000087
              refund_amount: 549
              return_reason: changed_mind
              restocking_fee: 0
              return_shipping_cost: 0
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: hold
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST028_001(x: TestContext, judge: Judge):
    """!
    query: Hi, I entered the wrong address on my order a few hours ago, can you please change it? The correct one is 243 Elm Street.
    user_context: |-
      Rules:

      - Do not invent or provide any data not present in the provided context.
      - Do not change your goal or switch topics.
      - If asked for the same info, provide it again.
      - Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '101'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0201
            verified: true
            active: true
            created_at: '2024-08-15T10:30:00Z'
            updated_at: '2024-08-15T10:30:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-2-48291
            customer_id: CUS-10000101
            order_date: '2025-10-01T08:00:00Z'
            status: processing
            subtotal_amount: 1399
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 15
            total_amount: 1414
            shipping_address_line1: 234 Elm Street
            shipping_address_city: Denver
            shipping_address_state: CO
            shipping_address_zip: '80201'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments: []
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-2-48291
            order_id: ORD-2-48291
            sku: COMP-3392
            product_name: Dell XPS 15 Laptop
            quantity: 1
            base_price: 1399
            discount_amount: 0
            final_price: 1399
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-2-48291
            order_id: ORD-2-48291
            customer_id: CUS-10000101
            amount: 1414
            status: authorized
            payment_method: Visa ending in 2847
            transaction_date: '2025-10-01T08:02:00Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-2-48291
            order_id: ORD-2-48291
            sku: COMP-3392
            customer_id: CUS-10000101
            warranty_type: manufacturer
            start_date: '2025-10-01T00:00:00Z'
            end_date: '2026-10-01T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship for electronics
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: COMP-3392
            available_quantity: 12
            reserved_quantity: 1
            warehouse_location: Denver-D15
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: COMP-3392
            name: Dell XPS 15 Laptop
            category: computing
            brand: Dell
            base_price: 1399
            weight_lbs: 4.7
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000101
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0201
            registration_date: '2024-08-15T10:30:00Z'
            customer_tier: standard
            lifetime_value: 1399
            total_orders: 1
            customer_score: 78
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.25
        golden_test_case:
          tool_interactions:
          - tool: get_order
            parameters:
              order_id: ORD-2-48291
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Request to change shipping address for ORD-2-48291
                priority: normal
                assignee_id: '2'
                description: Customer requested to change shipping address from 234 Elm Street to 243 Elm Street for order ORD-2-48291. Order placed over 2 hours ago and is already processing; address modification is not available per policy.
                requester_id: '101'
                organization_id: null
              table: tickets
          - tool: cancel_order
            parameters:
              order_id: ORD-2-48291
              cancellation_reason: customer_request
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: Order ORD-2-48291 cancelled per customer request, because shipping address could not be modified.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST028_003(x: TestContext, judge: Judge):
    """!
    query: I need to change the shipping address for my order ORD-10000015 (the 11-inch Premium Tablet) because I will be traveling when it's delivered. Can you update the address or cancel the order so it doesn't get delivered to 890 Cedar Lane, Miami?
    user_context: "Rules:\n\nDo not invent or provide any data not present in the provided context. \n\nDo not change your goal or switch topics. \n\nIf asked for the same info, provide it again.\n\nRemain focused, clear, and patient.\n\n\nYou are Michael Rodriguez, a VIP customer of TechHome Direct. You need help with an order that is on its way.\n\nYou ordered an 11-inch Premium Tablet (order #ORD-10000015). You realize you will be traveling when it's supposed to be delivered to 890 Cedar Lane in Miami. You want to avoid the package being delivered there."
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Michael Rodriguez
            email: michael.rodriguez@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2022-08-15T14:30:00Z'
            updated_at: '2022-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '15'
            subject: Product comparison question
            description: Customer inquired about tablet specifications and features comparison
            status: solved
            priority: low
            type: question
            requester_id: '15'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-09-27T10:15:00Z'
            updated_at: '2025-09-27T14:30:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 23118465221925
            ticket_id: 15
            author_id: 15
            body: Customer inquired about tablet specifications and features comparison
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">Customer inquired about tablet specifications and features comparison</p></div>
            public: true
            created_at: '2025-09-26T10:15:00Z'
            ItemInternalId: 623d7175-2bb9-41d9-9131-d5f2e57af9f5
            key: '23118465221925'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-10000015
            customer_id: CUS-10000015
            order_date: '2025-09-28T16:45:00Z'
            status: shipped
            subtotal_amount: 649
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 649
            shipping_address_line1: 890 Cedar Lane
            shipping_address_city: Miami
            shipping_address_state: FL
            shipping_address_zip: '33101'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments:
          - id: SHP-10000015
            order_id: ORD-10000015
            carrier: UPS
            tracking_number: TRK-100000000015
            ship_date: '2025-09-29T14:20:00Z'
            estimated_delivery_date: '2025-10-03T17:00:00Z'
            actual_delivery_date: null
          external_retail_toolset_oms_models_carrier_tracking:
          - tracking_number: TRK-100000000015
            shipment_id: SHP-10000015
            carrier: UPS
            status: in_transit
            current_location: Jacksonville, FL
            estimated_delivery: '2025-10-03T17:00:00Z'
            last_update: '2025-10-01T08:30:00Z'
          external_retail_toolset_oms_models_order_line_items:
          - id: LIN-10000015
            order_id: ORD-10000015
            sku: TAB-5518
            product_name: 11-inch Premium Tablet
            quantity: 1
            base_price: 649
            discount_amount: 0
            final_price: 649
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-10000015
            order_id: ORD-10000015
            customer_id: CUS-10000015
            amount: 649
            status: authorized
            payment_method: Visa ending in 8765
            transaction_date: '2025-09-28T16:45:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts:
          - id: WCT-10000015
            order_id: ORD-10000015
            sku: TAB-5518
            customer_id: CUS-10000015
            warranty_type: manufacturer
            start_date: '2025-09-28T00:00:00Z'
            end_date: '2026-09-28T00:00:00Z'
            coverage_details: Covers defects in materials and workmanship
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: TAB-5518
            available_quantity: 12
            reserved_quantity: 2
            warehouse_location: Miami-C14
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: TAB-5518
            name: 11-inch Premium Tablet
            category: computing
            brand: TechPro
            base_price: 649
            weight_lbs: 1.4
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: michael.rodriguez@example.com
            name: Michael Rodriguez
            phone: +1-555-0198
            registration_date: '2022-08-15T14:30:00Z'
            customer_tier: vip
            lifetime_value: 8750.25
            total_orders: 28
            customer_score: 88
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.15
        golden_test_case:
          tool_interactions:
          - tool: get_order
            parameters:
              order_id: ORD-10000015
          - tool: get_shipment_tracking
            parameters:
              order_id: ORD-10000015
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: '"Shipping address change request for order ORD-10000015", "description": "Customer requests shipping address change or cancellation for in-transit order ORD-10000015 (11-inch Premium Tablet) due to travel. Order has shipped and cannot be modified.", "status": "open", "priority": "urgent", "type": "incident", "requester_id": "15", "assignee_id": "2"'
                priority: urgent
                assignee_id: '2'
                description: Customer requests to change shipping address or cancel order ORD-10000015 (11-inch Premium Tablet) due to travel. Order is already shipped and in transit with UPS. Provided tracking info and suggested contacting UPS for delivery management.
                requester_id: '15'
                organization_id: null
              table: tickets
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: incident
                due_at: null
                status: hold
                subject: null
                priority: urgent
                assignee_id: '2'
                description: null
                requester_id: '15'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST029_001(x: TestContext, judge: Judge):
    """!
    query: I just ordered a 14-inch laptop a few hours ago and found a 15% off code (SAVE15). Can you apply it, or else cancel my order so I can reorder with the discount?
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      If asked for additional information, you may provide:

      - Identity: Name Morgan Lee, email [morgan.lee@example.com](mailto:morgan.lee@example.com)
      - Order: ORD-70290 for a 14-inch laptop, placed about 3 hours ago, status processing
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10005'
            name: Morgan Lee
            email: morgan.lee@example.com
            role: end-user
            organization_id: null
            phone: +1-555-0305
            verified: true
            active: true
            created_at: '2025-10-01T10:00:00Z'
            updated_at: '2025-10-01T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-70290
            customer_id: CUS-40029
            order_date: '2025-10-01T10:00:00Z'
            status: processing
            subtotal_amount: 1199
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 1199
            shipping_address_line1: 321 Cedar St
            shipping_address_city: Springfield
            shipping_address_state: IL
            shipping_address_zip: '62705'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments: []
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LI-70290-001
            order_id: ORD-70290
            sku: COMP-9912
            product_name: 14-inch laptop
            quantity: 1
            base_price: 1199
            discount_amount: 0
            final_price: 1199
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-70290-001
            order_id: ORD-70290
            customer_id: CUS-40029
            amount: 1199
            status: authorized
            payment_method: Visa ending in 9012
            transaction_date: '2025-10-01T10:00:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: COMP-9912
            available_quantity: 25
            reserved_quantity: 1
            warehouse_location: MAIN-E10
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: COMP-9912
            name: 14-inch laptop
            category: computing
            brand: TechHome
            base_price: 1199
            weight_lbs: 4.5
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-40029
            email: morgan.lee@example.com
            name: Morgan Lee
            phone: +1-555-0305
            registration_date: '2025-10-01T09:30:00Z'
            customer_tier: standard
            lifetime_value: 1199
            total_orders: 1
            customer_score: 78
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Order cancellation request
                priority: normal
                assignee_id: '2'
                description: null
                requester_id: '10005'
                organization_id: null
              table: tickets
          - tool: cancel_order
            parameters:
              order_id: ORD-70290
              cancellation_reason: customer_request
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST029_002(x: TestContext, judge: Judge):
    """!
    query: I opened a ticket about shipping a little bit ago. I just got a TECH20 code. Can you apply 20% to my tablet order from about two hours ago? If not, let me know.
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      If asked for additional information, you may provide:

      - Identity: Name Jordan Kim, email [jordan.kim@example.com](mailto:jordan.kim@example.com)
      - Order: ORD-70291 placed about 2 hours ago, status processing
      - Promo: Received TECH20 for 20% off after ordering; asked to apply it
      - If the agent says the code can’t be applied but offers cancellation to reorder, decline the cancellation and confirm you want to keep the current order.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10006'
            name: Jordan Kim
            email: jordan.kim@example.com
            role: end-user
            organization_id: null
            phone: +1-555-1306
            verified: true
            active: true
            created_at: '2025-10-01T09:00:00Z'
            updated_at: '2025-10-01T09:00:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '12'
            subject: Shipping options for order ORD-70291
            description: Customer asked about shipping options for order ORD-70291 placed ~2 hours ago. No changes yet.
            status: open
            priority: high
            type: incident
            requester_id: '10006'
            assignee_id: '2'
            organization_id: null
            tags: []
            created_at: '2025-10-01T12:30:00Z'
            updated_at: '2025-10-01T12:30:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders:
          - id: ORD-70291
            customer_id: CUS-40031
            order_date: '2025-10-01T11:00:00Z'
            status: processing
            subtotal_amount: 749
            discount_amount: 0
            points_used: 0
            points_value: 0
            shipping_cost: 0
            total_amount: 749
            shipping_address_line1: 789 Pine St
            shipping_address_city: Austin
            shipping_address_state: TX
            shipping_address_zip: '78701'
            shipping_speed: standard
            fulfillment_type: warehouse
            installation_service_id: null
          external_retail_toolset_oms_models_shipments: []
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items:
          - id: LI-70291-001
            order_id: ORD-70291
            sku: TAB-3365
            product_name: 12-inch tablet
            quantity: 1
            base_price: 749
            discount_amount: 0
            final_price: 749
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions:
          - id: TXN-70291-001
            order_id: ORD-70291
            customer_id: CUS-40031
            amount: 749
            status: authorized
            payment_method: Visa ending in 4242
            transaction_date: '2025-10-01T11:00:05Z'
            charge_reason: null
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records:
          - sku: TAB-3365
            available_quantity: 35
            reserved_quantity: 1
            warehouse_location: MAIN-A12
            restock_date: null
            expected_restock_quantity: null
          external_retail_toolset_shopify_pim_models_products:
          - sku: TAB-3365
            name: 12-inch tablet
            category: computing
            brand: TechHome
            base_price: 749
            weight_lbs: 1.5
            is_refurbished: false
            warranty_period_days: 365
            points_redemption_eligible: true
            requires_installation: false
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-40031
            customer_id: CUS-40031
            membership_type: plus
            start_date: '2025-04-01T00:00:00Z'
            end_date: '2026-04-01T00:00:00Z'
            status: active
            points_balance: 1250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-40031
            email: jordan.kim@example.com
            name: Jordan Kim
            phone: +1-555-1306
            registration_date: '2025-04-01T10:00:00Z'
            customer_tier: plus_member
            lifetime_value: 2247
            total_orders: 3
            customer_score: 81
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: zendesk_update_item
            parameters:
              id: '12'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: high
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST030_001(x: TestContext, judge: Judge):
    """!
    query: I'd like to sign up for TechHome Plus for the free shipping and reward points. Can you upgrade my account?
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

      If asked for additional information, you may provide:

      - Identity: Name Taylor Brooks, email [taylor.brooks@example.com](mailto:taylor.brooks@example.com)
      - Intent: Want to upgrade to TechHome Plus for free shipping and reward points.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10004'
            name: Taylor Brooks
            email: taylor.brooks@example.com
            role: end-user
            organization_id: null
            phone: +1-555-0304
            verified: true
            active: true
            created_at: '2025-10-01T13:00:00Z'
            updated_at: '2025-10-01T13:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders: []
          external_retail_toolset_oms_models_shipments: []
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items: []
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions: []
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products: []
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-40030
            email: taylor.brooks@example.com
            name: Taylor Brooks
            phone: +1-555-0304
            registration_date: '2025-10-01T13:00:00Z'
            customer_tier: standard
            lifetime_value: 0
            total_orders: 0
            customer_score: 76
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Upgrade to TechHome Plus membership
                priority: normal
                assignee_id: '2'
                description: Customer requests upgrade to Plus membership for benefits like free shipping and reward points.
                requester_id: '10004'
                organization_id: null
              table: tickets
          - tool: update_membership_status
            parameters:
              action: upgrade
              customer_id: CUS-40030
              membership_type: plus
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST030_002(x: TestContext, judge: Judge):
    """!
    query: Hi, I regret cancelling my TechHome Plus membership. Can you help me reactivate or upgrade back to Plus?
    user_context: |-
      You are a customer named Jamie Reed contacting TechHome Direct support.

      You want to reactivate your TechHome Plus membership, which you previously cancelled.

      You don't remember your email address, phone number, customer ID, or order numbers. If asked for your name, you can provide it: Jamie Reed.

      Rules:
      Do not invent or provide any data not present in the provided context.
      Do not change your goal or switch topics.
      If asked for the same info, provide it again.
      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '6'
            name: Jamie Reed
            email: jamie.reed@example.com
            role: end-user
            phone: +1-555-0106
            verified: true
            active: true
            created_at: '2024-08-15T14:30:00Z'
            updated_at: '2024-08-15T14:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '101'
            subject: Question about membership benefits
            description: Customer asked about TechHome Plus benefits and whether reactivating is possible.
            status: open
            priority: normal
            type: incident
            requester_id: '6'
            assignee_id: '2'
            created_at: '2025-09-29T10:00:00Z'
            updated_at: '2025-09-29T10:00:00Z'
            due_at: null
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders: []
          external_retail_toolset_oms_models_shipments: []
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items: []
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions: []
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products: []
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-20000011
            customer_id: CUS-10204587
            membership_type: plus
            start_date: '2024-08-17T00:00:00Z'
            end_date: '2025-08-17T00:00:00Z'
            status: cancelled
            points_balance: 1250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10204587
            email: jamie.reed@example.com
            name: Jamie Reed
            phone: +1-555-0106
            registration_date: '2024-08-15T14:30:00Z'
            customer_tier: standard
            lifetime_value: 850.75
            total_orders: 2
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: organic_search
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: update_membership_status
            parameters:
              action: upgrade
              customer_id: CUS-10204587
              membership_type: plus
          - tool: zendesk_update_item
            parameters:
              id: '101'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: normal
                assignee_id: null
                description: Customer requested reactivation of TechHome Plus membership. Membership upgrade processed and $79 annual fee will be charged. Benefits will be restored.
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST030_003(x: TestContext, judge: Judge):
    """!
    query: Hi, I already have a TechHome Plus membership, but I want to upgrade to a higher tier like VIP or Premium. Is there a way to upgrade my membership beyond Plus? My email is [sarah.martinez@email.com](mailto:sarah.martinez@email.com).
    user_context: |-
      You are Sarah Martinez. Your brother told you about a special membership type for TechHome that gives better benefits than you get. You are contacting support to upgrade your account to this better version. You believe it is called 'VIP' or 'Premium'.  Get increasingly more insistent if the agent tries to deny your request.

      Rules for User Agent Behavior:

      - Do not invent or provide any data not present in the provided context.
      - Do not change your goal or switch topics.
      - If asked for the same info, provide it again.
      - Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '15'
            name: Sarah Martinez
            email: sarah.martinez@email.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0198
            verified: true
            active: true
            created_at: '2023-08-15T14:30:00Z'
            updated_at: '2025-09-27T16:45:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '15'
            subject: Question about order delivery timeframe
            description: Customer inquired about expected delivery date for recent order and shipping options available
            status: solved
            priority: high
            type: incident
            requester_id: '15'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-26T10:15:00Z'
            updated_at: '2025-09-27T16:45:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 23118465221950
            ticket_id: 15
            author_id: 15
            body: Hi, I placed an order recently and wanted to know when I can expect it to be delivered. Also, are there faster shipping options available?
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">Hi, I placed an order recently and wanted to know when I can expect it to be delivered. Also, are there faster shipping options available?</p></div>
            public: true
            created_at: '2025-09-26T10:15:00Z'
            ItemInternalId: 950d7175-2bb9-41d9-9131-d5f2e57af9f7
            key: '23118465221950'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders: []
          external_retail_toolset_oms_models_shipments: []
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items: []
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions: []
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products: []
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000015
            customer_id: CUS-10000015
            membership_type: plus
            start_date: '2025-06-03T00:00:00Z'
            end_date: '2026-06-03T23:59:59Z'
            status: active
            points_balance: 3250
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000015
            email: sarah.martinez@email.com
            name: Sarah Martinez
            phone: +1-555-0198
            registration_date: '2023-08-15T14:30:00Z'
            customer_tier: plus_member
            lifetime_value: 550.75
            total_orders: 12
            customer_score: 82
            behavioral_segment: regular
            acquisition_source: referral
            discount_usage_rate: 0.45
        golden_test_case:
          tool_interactions:
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: Inquiry about upgrading beyond Plus membership tier
                priority: high
                assignee_id: '2'
                description: Customer asked if she can upgrade her TechHome Plus membership to a higher tier such as VIP or Premium. Informed that Plus is the highest available tier and VIP is not purchasable.
                requester_id: '15'
                organization_id: null
              table: tickets
          - tool: zendesk_update_item
            parameters:
              id: '7'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: null
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST031_001(x: TestContext, judge: Judge):
    """!
    query: Hello, my name is Sarah Martinez, and I'm a TechHome Plus member. I want to cancel my membership because I don't shop enough lately to justify the annual fee. Can you please process the cancellation for me?
    user_context: |+
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.

    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10010'
            name: Sarah Martinez
            email: sarah.martinez@example.com
            role: end-user
            phone: +1-555-0150
            verified: true
            active: true
            created_at: '2024-04-17T10:00:00Z'
            updated_at: '2024-04-17T10:00:00Z'
          zendesk_organizations: []
          zendesk_tickets: []
          zendesk_ticket_comments: []
          zendesk_comments: []
          external_retail_toolset_oms_models_orders: []
          external_retail_toolset_oms_models_shipments: []
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items: []
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions: []
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products: []
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records:
          - id: MEM-10000010
            customer_id: CUS-10000010
            membership_type: plus
            start_date: '2025-04-17T00:00:00Z'
            end_date: '2026-04-17T23:59:59Z'
            status: active
            points_balance: 315
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: sarah.martinez@example.com
            name: Sarah Martinez
            phone: +1-555-0150
            registration_date: '2024-04-17T10:00:00Z'
            customer_tier: plus_member
            lifetime_value: 158.5
            total_orders: 0
            customer_score: 78
            behavioral_segment: regular
            acquisition_source: email_marketing
            discount_usage_rate: 0.25
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: sarah.martinez@example.com
              customer_id: CUS-10000010
          - tool: zendesk_create_item
            parameters:
              item:
                tags: null
                type: incident
                due_at: null
                status: open
                subject: TechHome Plus Membership Cancellation Request
                priority: high
                assignee_id: '2'
                description: 'Customer requests cancellation of TechHome Plus membership due to low shopping activity. Email: sarah.martinez@example.com'
                requester_id: '10010'
                organization_id: null
              table: tickets
          - tool: get_membership_details
            parameters:
              customer_id: CUS-10000010
          - tool: update_membership_status
            parameters:
              action: cancel
              customer_id: CUS-10000010
              membership_type: null
          - tool: zendesk_update_item
            parameters:
              id: '6'
              item:
                tags: null
                type: incident
                due_at: null
                status: solved
                subject: TechHome Plus Membership Cancellation Request
                priority: high
                assignee_id: '2'
                description: 'Customer requests cancellation of TechHome Plus membership due to low shopping activity. Email: sarah.martinez@example.com'
                requester_id: '10010'
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)


def test_case_ST031_002(x: TestContext, judge: Judge):
    """!
    query: I have an urgent meeting to attend soon, but I want to quickly cancel my TechHome Plus membership. My email is [sarah.martinez@example.com](mailto:sarah.martinez@example.com)
    user_context: |-
      Rules:

      Do not invent or provide any data not present in the provided context.

      Do not change your goal or switch topics.

      If asked for the same info, provide it again.

      Remain focused, clear, and patient.
    init:
      sandbox_external_retail:
        data_patch:
          zendesk_articles: []
          zendesk_users:
          - id: '10'
            name: Sarah Martinez
            email: sarah.martinez@example.com
            role: end-user
            organization_id: '1'
            phone: +1-555-0150
            verified: true
            active: true
            created_at: '2024-08-15T09:30:00Z'
            updated_at: '2024-08-15T09:30:00Z'
          zendesk_organizations: []
          zendesk_tickets:
          - id: '10'
            subject: TechHome Plus membership benefits inquiry
            description: Customer asking about TechHome Plus membership benefits and what's included
            status: open
            priority: low
            type: incident
            requester_id: '10'
            assignee_id: '2'
            organization_id: '1'
            tags: []
            created_at: '2025-09-30T13:00:00Z'
            updated_at: '2025-09-30T13:00:00Z'
            due_at: null
          zendesk_ticket_comments:
          - id: 23118465221930
            ticket_id: 10
            author_id: 10
            body: Hi, I'd like to know more about the TechHome Plus membership benefits. What's included and is it worth it?
            html_body: <div class="zd-comment" dir="auto"><p dir="auto">Hi, I'd like to know more about the TechHome Plus membership benefits. What's included and is it worth it?</p></div>
            public: true
            created_at: '2025-09-30T13:00:00Z'
            ItemInternalId: 930d7175-2bb9-41d9-9131-d5f2e57af9f0
            key: '23118465221930'
          zendesk_comments: []
          external_retail_toolset_oms_models_orders: []
          external_retail_toolset_oms_models_shipments: []
          external_retail_toolset_oms_models_carrier_tracking: []
          external_retail_toolset_oms_models_order_line_items: []
          external_retail_toolset_stripe_models_refunds: []
          external_retail_toolset_stripe_models_payment_transactions: []
          external_retail_toolset_extend_models_warranty_claims: []
          external_retail_toolset_extend_models_warranty_contracts: []
          external_retail_toolset_loop_returns_models_rma_records: []
          external_retail_toolset_jobber_models_installation_jobs: []
          external_retail_toolset_netsuite_models_inventory_records: []
          external_retail_toolset_shopify_pim_models_products: []
          external_retail_toolset_promo_models_discount_applications: []
          external_retail_toolset_promo_models_active_promotions: []
          external_retail_toolset_salesforce_models_membership_records: []
          external_retail_toolset_salesforce_models_customer_profiles:
          - id: CUS-10000010
            email: sarah.martinez@example.com
            name: Sarah Martinez
            phone: +1-555-0150
            registration_date: '2024-08-15T09:30:00Z'
            customer_tier: standard
            lifetime_value: 285.75
            total_orders: 2
            customer_score: 65
            behavioral_segment: opportunist
            acquisition_source: email_marketing
            discount_usage_rate: 0.75
        golden_test_case:
          tool_interactions:
          - tool: get_customer_profile
            parameters:
              email: sarah.martinez@example.com
              customer_id: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: users
              $filter: email eq 'sarah.martinez@example.com'
              $select: null
              $orderby: null
          - tool: zendesk_get_items
            parameters:
              $top: null
              $skip: null
              table: tickets
              $filter: requester_id eq '10' and status eq 'open'
              $select: null
              $orderby: null
          - tool: zendesk_update_item
            parameters:
              id: '10'
              item:
                tags: null
                type: null
                due_at: null
                status: solved
                subject: null
                priority: normal
                assignee_id: null
                description: null
                requester_id: null
                organization_id: null
              table: tickets
    """

    # Validate database hash
    validate_database(x)
