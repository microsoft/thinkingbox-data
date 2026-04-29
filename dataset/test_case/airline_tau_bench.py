# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from thinkingbox.common import Judge, TestContext

"""!
scenario: airline_tau_bench_full
"""


def require_user_reservations(reservations, user_id):
    """This function raises an assertion error if there are no reservation
    """
    user_reservations = []
    for _, res_data in (
        reservations.items()
    ):
        if res_data.get("user_id") == user_id:
            user_reservations.append(res_data)
    assert len(user_reservations) > 0, f"No reservations found for user {user_id}"
    return user_reservations


def check_res_params(res, expected_params):
    for k, v in expected_params.items():
        actual = res.get(k)
        assert actual == v, f"Expected reservation.{k} == {v}, found {actual} in reservation {res!r}"


def check_res_passengers(res, expected_passengers):
    res_passengers = res.get("passengers", [])
    assert len(res_passengers) == len(expected_passengers), (
        f"Expected {len(expected_passengers)} passengers, found {len(res_passengers)}"
    )
    if expected_passengers:
        expected_passengers = set(expected_passengers)
        actual_passengers = set([(p.get("first_name"), p.get("last_name")) for p in res_passengers])
        assert actual_passengers == expected_passengers, (
            f"Expected passengers {expected_passengers!r}, found {actual_passengers!r}"
        )


def check_res_has_flight(res, flight_number=(), date=()):
    flight_number = (flight_number, ) if isinstance(flight_number, str) else flight_number
    date = (date, ) if isinstance(date, str) else date
    found = False
    res_flights = res.get("flights", [])
    for x in res_flights:
        match_flight_number = (not flight_number) or (x["flight_number"] in flight_number)
        match_date = (not date) or (x["date"] in date)
        if match_flight_number and match_date:
            found = True
            break
    assert found, (
        f"Expected flight with number in {flight_number} and date in {date}"
        + f" not found in reservation flights {res_flights}"
    )


def test_000_book_one_way_economy_flight(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I'm looking to book a flight from New York to Seattle on May 20.
        It's a one-way trip and I need to travel in economy class.
    user_context: |
        You are Mia Li (user ID: mia_li_3668). You want to fly from New York to Seattle
        on May 20 (one way). You do not want to fly before 11am est. You want to fly in
        economy. You prefer direct flights but one stopover also fine. If there are multiple
        options, you prefer the one with the lowest price. You have 3 baggages. You do
        not want insurance. You want to use your two certificates to pay. If only one
        certificate can be used, you prefer using the larger one, and pay the rest with
        your 7447 card. You are reactive to the agent and will not say anything that is
        not asked. Your birthday is in your user profile so you do not prefer to provide
        it.
    tags: [category:user]
    """

    # SOLUTION
    # Book reservation:
    #   - one_way JFK->SEA
    #   - 3 baggages
    #   - use certificate 7504069 for 250

    user_reservations = require_user_reservations(
        x.effects["airline_tau_bench"].get("reservations", {}),
        "mia_li_3668",
    )

    # Find the most recent reservation (should be the one we just created)
    res = user_reservations[-1]

    # Verify reservation details match the request
    check_res_params(
        res,
        {
            "flight_type": "one_way",
            "origin": "JFK",
            "destination": "SEA",
            "cabin": "economy",
            "total_baggages": 3,
            "insurance": "no",
        }
    )

    # check flights
    flights = res.get("flights", [])
    assert len(flights) == 2, f"Expected 2 flights, found {len(flights)}"
    check_res_has_flight(res, "HAT136", "2024-05-20")
    check_res_has_flight(res, "HAT039", "2024-05-20")

    check_res_passengers(res, [("Mia", "Li")])

    payment_methods = x.effects["airline_tau_bench"]["users"]["mia_li_3668"]["payment_methods"]
    cert_4856383_amount = payment_methods.get("certificate_4856383", {}).get("amount", 0)
    assert cert_4856383_amount == 100, (
        f"The smaller certificate should not have been used, it is {cert_4856383_amount} != 100"
    )
    cert_7504069_amount = payment_methods.get("certificate_7504069", {}).get("amount", 0)
    assert cert_7504069_amount == 0, (
        f"The larger certificate should have been used fully, it is {cert_7504069_amount} != 0"
    )


def test_001_change_return_flight_later(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I need to change my return flight from Texas back to Newark. I'm having a crazy half-day
        trip and need a later flight. What options do I have?
    user_context: |
        You are Olivia Gonzalez (user ID: olivia_gonzalez_2305), you currently reside in Newark,
        and you will have a crazy half-day trip to Texas. It is in your reservations but
        you don't remember the reservation id. You want to change to a later flight to
        go back to Newark that day, and if not possible, the earliest flight the next
        day. Your current return flight departs 3pm. You do not accept JFK, only EWR.
        You are reactive to the agent and will not say anything that is not asked. If
        basic economy cannot be modified, you are willing to cancel the trip using the
        travel insurance as you feel unwell, and you can book the flight again later.
    tags: [category:user]
    """

    # SOLUTION
    # Just cancel reservation Z7GOZK, nothing else

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})

    # find cancelled reservations for this user
    cancelled_reservations = []
    for user_res in require_user_reservations(all_reservations, "olivia_gonzalez_2305"):
        if user_res.get("status") == "cancelled":
            cancelled_reservations.append(user_res)

    assert len(cancelled_reservations) == 1, f"Expected 1 cancelled reservation, found {len(cancelled_reservations)}"
    cancelled_id = cancelled_reservations[0].get("reservation_id")
    assert cancelled_id == "Z7GOZK", f"Expected Z7GOZK to be cancelled, found {cancelled_id}"


def test_002_downgrade_business_to_economy(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to make some changes to all my business class reservations.
        I've run into some financial issues and need to downgrade them to economy.
    user_context: |
        You are Omar Davis (user ID: omar_davis_3817), you just faced some money issue and
        want to downgrade all business flights to economy, without changing the flights
        or passengers. You are fine with refunding to original payment for each reservation.
        You want to know how much money you have saved in total. You are emotional and
        a bit angry, but you are willing to cooperate with the agent.
    tags: [category:user]
    """

    # SOLUTION
    # Change all of the user's active reservations to economy

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})
    user_reservations = require_user_reservations(
        all_reservations,
        "omar_davis_3817",
    )
    for user_res in user_reservations:
        if user_res.get("status") != "cancelled":
            check_res_params(user_res, {"cabin": "economy"})


def test_004_add_checked_bags_and_change_passenger(x: TestContext, judge: Judge):
    """!
    query: |
        Hello, I need to make some changes to my upcoming trip from New York to Chicago.
        Can you help me update the passenger details and add some baggage?
    user_context: |
        You are Omar Rossi (user ID: omar_rossi_1241). For your upcoming trip from New York
        to Chicago, you want to change the passenger to yourself, upgrade it to economy
        class, and have 3 checked bags. You prefer gift card payment. Your birthday is
        in your user profile so you do not prefer to provide it. You are reactive to the
        agent and will not say anything that is not asked.
    tags: [category:user]
    """

    # SOLUTION
    # Update reservation FQ8APE:
    # - Upgrade to economy
    # - Change passenger to Omar Rossi
    # - Update to 3 baggages

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})
    res = all_reservations.get("FQ8APE")
    assert res is not None, "Reservation FQ8APE not found"
    
    check_res_params(
        res,
        {
            "user_id": "omar_rossi_1241",
            "cabin": "economy",
            "total_baggages": 3,
        }
    )
    check_res_passengers(res, [("Omar", "Rossi")])


def test_006_change_to_cheapest_economy_next_day(x: TestContext, judge: Judge):
    """!
    query: |
        Hi there, I need to change my upcoming trip from Atlanta to Philadelphia.
        Could you help me find a cheaper option for the day after my original reservation?
    user_context: |
        You are Aarav Garcia (user ID: aarav_garcia_1177). For your upcoming trip from ATL
        to PHL, you want to change for the cheapest economy (but not basic economy) flight
        and for the day after the original reservation. You are happy with original payment
        for refund.
    tags: [category:user]
    """

    # SOLUTION
    # - Update reservation to be the next day, 2024-05-24 HAT110->HAT172
    # - Downgrade cabin from business to economy

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})
    user_reservations = require_user_reservations(
        all_reservations,
        "aarav_garcia_1177",
    )

    # active ATL->PHL reservations
    user_reservations_atl_phl = []
    for res_data in user_reservations:
        if (
            res_data.get("origin") == "ATL"
            and res_data.get("destination") == "PHL"
            and res_data.get("status") != "cancelled"
        ):
            user_reservations_atl_phl.append(res_data)

    # Should have one ATL->PHL only
    assert len(user_reservations_atl_phl) == 1, f"Expected 1 active ATL->PHL reservation, found {len(user_reservations_atl_phl)}"
    res = user_reservations_atl_phl[0]

    # it is economy
    check_res_params(res, {"cabin": "economy"})

    # Check correct flights
    flights = res.get("flights", [])
    assert len(flights) == 2, f"Expected 2 flights, found {len(flights)}"
    check_res_has_flight(res, "HAT110", "2024-05-24")
    check_res_has_flight(res, "HAT172", "2024-05-24")

    # not checking for payment method because no strict requirement


def test_008_calculate_certificate_and_gift_card_balances(x: TestContext, judge: Judge):
    """!
    query: |
        Good morning, I'd like to check the total of my gift card and certificate balances
        and then make some changes to my recent reservation. Is this something you can help
        me with?
    user_context: |
        You are Mohamed Silva (user ID: mohamed_silva_9265). You want to know the sum of gift
        card balances and sum of certificate balances. If the agent gives you individual
        balances, you want the sums. Then you want to change your recent reservation to
        the cheapest business round trip without changing the dates or destination. You don't care about
        direct flight or stop over. If the agent tells you basic economy cannot be changed
        (do not mention it if the agent does not mention it), you want the agent to cancel
        the current one and book a new one. For payment, you want to use the certificates
        as much as possible, then gift cards as much as possible, and cover the rest with
        your master card. But you want to know how much your master card will be charged.
        You do not need baggage or insurance. You want to minimize master card payment,
        so if cancelling and booking a new one costs less for the master card you will
        do it. You are calm.
    tags: [category:user]
    """

    # SOLUTION
    # Cancel K1NW8N
    # Book JFK->SFO
    # - cabin: business
    # - baggages: 0
    # - insurance: no
    # - flights: HAT023(2025-05-26) -> HAT204(2024-05-28) -> HAT100(2024-05-28)
    # - passengers: Mohamed Silva, Raj Sanchez, Liam Wilson
    # - payments:
    #   use all balance in the larger certificate_3765853, but only this certificate
    #   use all balance in all gift cards gift_card_8020792, gift_card_6136092

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})
    cancelled_res = all_reservations.get("K1NW8N")
    assert cancelled_res is not None, "Reservation K1NW8N not found"
    assert (
        cancelled_res.get("status") == "cancelled"
    ), "Reservation K1NW8N should be cancelled"

    # Find the new reservation
    user_reservations = require_user_reservations(all_reservations, "mohamed_silva_9265")
    res = None
    for res_data in user_reservations:
        if (
            res_data.get("origin") == "JFK"
            and res_data.get("destination") == "SFO"
            and res_data.get("status") != "cancelled"
        ):
            assert res is None, f"Found multiple active JFK->SFO reservations in {user_reservations!r}"
            res = res_data
    assert res is not None, f"Expected JFK->SFO not found in {user_reservations!r}"

    check_res_params(
        res,
        {
            "flight_type": "round_trip",
            "cabin": "business",
            "total_baggages": 0,
            "insurance": "no",
        }
    )
    flights = res.get("flights", [])
    assert len(flights) == 3, f"Expected 3 flights, found {len(flights)}"
    check_res_has_flight(res, "HAT023", "2024-05-26")
    check_res_has_flight(res, "HAT204", "2024-05-28")
    check_res_has_flight(res, "HAT100", "2024-05-28")
    check_res_passengers(
        res,
        [("Mohamed", "Silva"), ("Raj", "Sanchez"), ("Liam", "Wilson")],
    )

    # Verify payment methods in state
    payments = set([
        (p["payment_id"], p["amount"]) for p in res.get("payment_history", [])
    ])
    expected_payments = set([
        # user asks to use the largest certificate.
        # Only one certificate can be used
        ("certificate_3765853", 500),
        # User asks to use gift cards as much as possible
        # All can be used (max 3, they have 2)
        ("gift_card_8020792", 198),
        ("gift_card_6136092", 129),
        # credit cards
        ("credit_card_2198526", 1786),
    ])
    assert payments == expected_payments, (
        f"Expected payments {expected_payments!r}, found {payments!r}"
    )


def test_010_cancel_and_book_new_cheapest_west_coast(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I want to remove Ethan from my reservation H9ZU1C.
        I would also like to make a new reservation.
    user_context: |
        You are Mia Kim (user ID: mia_kim_4397) and you want to remove Ethan from you
        reservation H9ZU1C. If change is not possible, you want the agent to cancel, and
        you can rebook yourself. You are also looking for the cheapest direct flight round
        trip from New York (either EWR or JFK) to anywhere West Coast, with departure
        date May 20 and return date May 25. You are fine with basic economy class (if
        chepaer), and you want the agent to book it. You want to first use up your smaller
        gift card and then the larger one. Would want to use all your free baggage allowance
        but no insurance. Your DOB is in your user profile and you do not want to speak
        it. You also wonder why cancellation does not refund to gift card now.
    tags: [category:user]
    """

    # SOLUTION
    # Cancel H9ZU1C
    # Book new round_trip JFK->SEA 
    # - cabin: basic_economy
    # - flights: HAT069(2024-05-20) -> HAT276(2024-05-25)
    # - payment: smaller gift_card_7359776 fully used, and entire amount paid by gift cards (there is enough)
    # - insurance: no

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})

    # Verify that reservation H9ZU1C was cancelled in the state
    cancelled_res = all_reservations.get("H9ZU1C")
    assert cancelled_res is not None, "Reservation H9ZU1C not found"
    assert cancelled_res.get("status") == "cancelled", "Reservation H9ZU1C was not cancelled"

    # Find active JFK->SEA reservation
    user_reservations = require_user_reservations(all_reservations, "mia_kim_4397")
    res = None
    for res_data in user_reservations:
        if (
            res_data.get("origin") == "JFK"
            and res_data.get("destination") == "SEA"
            and res_data.get("status") != "cancelled"
        ):
            assert res is None, f"Multiple active JFK->SEA reservations found in {user_reservations!r}"
            res = res_data
    assert res is not None, f"No active JFK->SEA reservations found in {user_reservations!r}"

    check_res_params(
        res,
        {
            "cabin": "basic_economy",
            "flight_type": "round_trip",
            "insurance": "no",
        }
    )

    flights = res.get("flights", [])
    assert len(flights) == 2, f"There should be 2 flights, found {len(flights)}"
    check_res_has_flight(res, "HAT069", "2024-05-20")
    check_res_has_flight(res, "HAT276", "2024-05-25")

    # Check that only gift cards were used (balance is sufficient)
    payment_methods = res.get("payment_history", [])
    assert all(p.get("payment_id", "").startswith("gift_card") for p in payment_methods), (
        f"Payment methods other than gift cards have been used: {payment_methods!r}"
    )
    # check that gift_card_7359776 was fully used (39)
    gift_card_7359776_amount = [x.get("amount") for x in payment_methods if x.get("payment_id") == "gift_card_7359776"]
    assert gift_card_7359776_amount and gift_card_7359776_amount[0] == 39, (
        f"gift_card_7359776 was not fully used (39) in payments {payment_methods!r}"
    )


def test_011_book_same_flight_for_friend(x: TestContext, judge: Judge):
    """!
    query: |
        I want to book the same flights as my current reservation for my friend Ivan.
    user_context: |
        You are Ivan Muller (user ID: ivan_muller_7015) and you want to book the same flights
        as your current reservation for your friend Ivan in your user profile (Ivan Smith,
        DOB you can't remember but in your profile). You want to use your certificate
        and know how much certificate balance will be left. If more than $100 is wasted,
        you want to instead use your gift card and credit card. No baggage and insurance.
    tags: [category:user]
    """

    # SOLUTION
    # Book one_way DTW->SEA
    # - flights: HAT097(2024-05-17) -> HAT251(2024-05-17)
    # - cabin: economy
    # - payment: gift_card_8516878 and credit_card_3563913 (do not use the certificate)
    # - baggages: 2
    # - insurance: no
    # - passengers: Ivan Smith

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})

    # Find Ivan Muller's DTW->SEA reservations
    user_reservations = require_user_reservations(all_reservations, "ivan_muller_7015")
    user_res_dtw_sea = []
    for res_data in user_reservations:
        if (
            res_data.get("status") != "cancelled"
            and res_data.get("origin") == "DTW"
            and res_data.get("destination") == "SEA"
        ):
            user_res_dtw_sea.append(res_data)
    assert len(user_res_dtw_sea) == 2, (
        f"Expected two active DTW->SEA reservations in {user_res_dtw_sea!r}"
    )

    two_passenger_res = [x for x in user_res_dtw_sea if len(x.get("passengers", [])) == 2]
    assert len(two_passenger_res) == 1, (
        f"Expected exactly 1 two passenger reservation in {user_res_dtw_sea!r}"
    )
    check_res_passengers(
        two_passenger_res[0],
        [
            ("Ivan", "Muller"),
            ("Isabella", "Moore"),
        ]
    )

    one_passenger_res = [x for x in user_res_dtw_sea if len(x.get("passengers", [])) == 1]
    assert len(one_passenger_res) == 1, (
        f"Expected exactly 1 one passenger reservation in {one_passenger_res!r}"
    )
    res = one_passenger_res[0]
    check_res_passengers(res, [("Ivan", "Smith")])
    check_res_params(
        res,
        {
            "flight_type": "one_way",
            "cabin": "economy",
            "total_baggages": 0,
            "insurance": "no",
        }
    )
    flights = res.get("flights", [])
    assert len(flights) == 2, f"Expected 2 flights in {flights!r}"
    check_res_has_flight(res, "HAT097", "2024-05-17")
    check_res_has_flight(res, "HAT251", "2024-05-17")
    payment_history = res.get("payment_history", [])
    payment_ids = [p.get("payment_id") for p in payment_history]
    assert set(payment_ids) == set(["gift_card_8516878", "credit_card_3563913"]), (
        f"Expected payment with gift_card_8516878, credit_card_3563913 and no certificates in {payment_history!r}"
    )


def test_012_cancel_mco_to_clt_insist_refund(x: TestContext, judge: Judge):
    """!
    query: |
        I want to cancel my flights from MCO to CLT and refund.
    user_context: |
        You are Amelia Sanchez (user ID: amelia_sanchez_4739) and you want to cancel your flights
        from MCO to CLT. You insist to cancel and have the refund.
    tags: [category:user,category:refusal]
    """
    # SOLUTION
    # Do nothing and do not transfer, it's against policy
    # Respond with a refusal message

    last_tool_is_transfer_to_human = (
        len(x.tool_calls) > 0
        and x.tool_calls[-1].tool_call.name == "transfer_to_human_agents"
    )
    assert not last_tool_is_transfer_to_human, "Should not be transferred, because against policy"

    msg_refusal = judge.text_yesno(
        x.response,
        "Does the response look like a refusal or denial?",
    )
    assert msg_refusal, "Agent did not explicitly refuse"


def test_013_change_onestop_to_nonstop_flight(x: TestContext, judge: Judge):
    """!
    query: |
        I want to change my upcoming one stop flight from ATL to LAX within reservation XEWRD9
        to a nonstop flight from ATL to LAS (Las Vegas).
    user_context: |
        You are James Lee (user ID: james_lee_6136). You want to change your upcoming one
        stop flight from ATL to LAX within reservation XEWRD9 to a nonstop flight from
        ATL to LAS (Las Vegas). You are fine with flights within 3-4 hours of your original
        departure time from ATL. You are willing to pay a fee for the change, upto $100.
        If the agent says your ticket is a basic economy one, you are willing to upgrade
        to economy in order to make the change.
    tags: [category:user, category:refusal]
    """
    # SOLUTION
    # transfer because the reservation is partially used

    last_tool_is_transfer_to_human = (
        len(x.tool_calls) > 0
        and x.tool_calls[-1].tool_call.name == "transfer_to_human_agents"
    )
    assert last_tool_is_transfer_to_human, "Should be transferred"

    summary = x.tool_calls[-1].tool_call.arguments.get("summary", "")
    assert judge.text_yesno(
        summary,
        "Does the message mention that a reservation is partially used?"
    ), "Transfer summary should mention that the reservation is partially used"


def test_014_upgrade_to_business_add_bags(x: TestContext, judge: Judge):
    """!
    query: |
        I have an upcoming flight from Boston to Minneapolis under reservation ID YAX4DR.
        I want to change class for all passengers to business and add 2 checked bags
        under my name using my Gold membership.
    user_context: |
        You are Chen Lee (user ID: chen_lee_6825). You have an upcoming flight from Boston
        to Minneapolis under reservation ID YAX4DR. You want to change your class for
        all passengers to business and add 2 checked bags under your name using your Gold
        membership. You are willing to pay a fee for the business class changes, upto
        $600. If the costs are greater than that for the upgrade, then try to upgrade
        your companion Noah to business under the constraints.
    tags: [category:user]
    """

    # SOLUTION
    # Change YAX4DR
    # - Do not cancel
    # - Do not upgrade to business
    # - only change baggages to 2, all free

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})

    res = all_reservations.get("YAX4DR")
    assert res is not None, "Reservation YAX4DR not found"

    assert res.get("status") != "cancelled", "Reservation YAX4DR should not be cancelled"
    check_res_params(
        res,
        {
            "user_id": "chen_lee_6825",
            "cabin": "economy",
            "total_baggages": 2,
            "nonfree_baggages": 0,
            "insurance": "no",
        }
    )
    check_res_passengers(res, [("Chen", "Lee"), ("Noah", "Hernandez")])


def test_016_delayed_flight_compensation_complaint(x: TestContext, judge: Judge):
    """!
    query: |
        I am contacting to complain about my delayed flight HAT039 from ATL to SEA. I am very
        upset that the flight has been delayed. What is the reason for the delay?
    user_context: |
        You are Ethan Martin (user ID: ethan_martin_2396) and you are contacting to complain about
        your delayed flight HAT039 from ATL to SEA. You are very upset that the flight has been
        delayed and want the airline to compensate you for the delay. If offered a voucher
        as compensation for the inconvenience, you are happy to accept it and keep the reservation
        without changes.
    tags: [category:user]
    """
    # Note: I changed this a bit to remove ambiguity and give it a chance to pass

    # The policy could be interpreted as: "the voucher can be granted only if the user cancels
    # or changes the reservation", however it probably meant: "the voucher can be granted if
    # the user is so upset they want to cancel".
    # I removed that bit from the policy.

    # The query + user context also makes the user ask for a reason multiple times, which blocks
    # stops the agent from compensating because the user is not happy enough with it.
    # I also changed it slightly.

    # SOLUTION
    # Send a 150 certificate

    users = x.effects["airline_tau_bench"].get("users", {})

    # Check Ethan Martin's user profile for new certificates
    user_profile = users["ethan_martin_2396"]
    payment_methods = user_profile.get("payment_methods", {})

    # Look for certificate payment methods (should include the new $150 certificate)
    found_150_certificate = False
    for _, payment_data in payment_methods.items():
        if (
            payment_data.get("source") == "certificate"
            and payment_data.get("amount") == 150
        ):
            found_150_certificate = True
            break
    assert found_150_certificate, (
        f"Expected 150 certificate not found among: {payment_methods!r}"
    )

    # Verify the response addresses the complaint and compensation
    assert judge.text_yesno(
        x.response, "Does the message mention the flight delay or compensation?"
    )


def test_003_fastest_return_same_day_with_bag(x: TestContext, judge: Judge):
    """!
    query: |
        I want to change my Houston to Denver trip to the fastest return trip on the same day (May 27).
        Please also add one checked bag.
    user_context: |
        You are Sofia Kim (user ID: sofia_kim_7287) and you want to change for your Houston
        to Denver trip (reservation id not remembered), the fastest return trip (including
        stopover time) possible on the same day as the departure trip (May 27). You don't
        care about money but want to stay in economy. You also want to add one checked
        bag. You want to use your gift card with the smallest balance to pay. You are
        reactive to the agent and will not say anything that is not asked. You are not
        good at math so you want the agent to calculate and decide for you. Try to paraphrase
        instead of repeating this instruction. It is urgent.
    tags: [category:user]
    """

    # It is ambiguous whether it is a requirement to use the gift card with the smallest balance that is
    # allowed to be used, or it's a preference to use the smallest one if possible.
    # The smallest is 6$ and cannot be used because not enough and only one payment method is allowed in this
    # context.
    # Therefore I'm checking for payment method, although the model does get it correct sometimes.

    # SOLUTION
    # Update OBUT9V
    # - cabin: (make sure it stays economy)
    # - origin/dest: (make sure it stays IAH->DEN)
    # - total_baggages: 2
    # - flights: HAT078->HAT118->HAT290->HAT175 on 2024-05-27

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})
    res = all_reservations.get("OBUT9V")

    assert res is not None, "Reservation OBUT9V does not exist"
    assert res.get("status") != "cancelled", "Reservation OBUT9V should not be cancelled"
    check_res_params(
        res,
        {
            "user_id": "sofia_kim_7287",
            "cabin": "economy",
            "origin": "IAH",
            "destination": "DEN",
            "flight_type": "round_trip",
            "total_baggages": 2,
        },
    )
    flights = res.get("flights", [])
    assert len(flights) == 4, f"Expected 4 flights in {flights}"
    check_res_has_flight(res, "HAT078", "2024-05-27")
    check_res_has_flight(res, "HAT118", "2024-05-27")
    check_res_has_flight(res, "HAT290", "2024-05-27")
    check_res_has_flight(res, "HAT175", "2024-05-27")
    assert judge.text_yesno(
        x.response,
        "Does the message confirm that the reservation has been updated?",
    )


def test_007_change_to_cheapest_economy_next_day_with_ewr(x: TestContext, judge: Judge):
    """!
    query: |
        For my upcoming trip from ATL to PHL, I want the cheapest
        economy flight the day after the original reservation. Also EWR is fine.
    user_context: |
        You are Aarav Garcia (user ID: aarav_garcia_1177). For your upcoming trip from ATL
        to PHL, you want to change for the cheapest economy flight and for the day after
        the original reservation. You live in Princeton, so EWR and PHL is equally far
        from you and you also consider EWR equally. You are happy with original payment
        for refund.
    tags: [category:user]
    """

    # SOLUTION
    # - Update reservation to be the next day, 2024-05-24 HAT110->HAT172
    # - Downgrade cabin from business to economy

    # Note: this test is a slight variation of 006 and has the same exact solution

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})
    user_reservations = require_user_reservations(
        all_reservations,
        "aarav_garcia_1177",
    )

    # active ATL->PHL reservations
    user_reservations_atl_phl = []
    for res_data in user_reservations:
        if (
            res_data.get("origin") == "ATL"
            and res_data.get("destination") == "PHL"
            and res_data.get("status") != "cancelled"
        ):
            user_reservations_atl_phl.append(res_data)

    # Should have one ATL->PHL only
    assert len(user_reservations_atl_phl) == 1, f"Expected 1 active ATL->PHL reservation, found {len(user_reservations_atl_phl)}"
    res = user_reservations_atl_phl[0]

    # it is economy
    check_res_params(res, {"cabin": "economy"})

    # Check correct flights
    flights = res.get("flights", [])
    assert len(flights) == 2, f"Expected 2 flights, found {len(flights)}"
    check_res_has_flight(res, "HAT110", "2024-05-24")
    check_res_has_flight(res, "HAT172", "2024-05-24")

    # not checking for payment method because no strict requirement


def test_015_remove_passenger_or_downgrade_all_if_blocked(x: TestContext, judge: Judge):
    """!
    query: |
        Remove Sophia from my upcoming flights and refund immediately.
    user_context: |
        You are James Patel (user ID: james_patel_9828) and want to remove passenger Sophia from your
        upcoming flights from LAS to DEN on May 19 and DEN to LAS on May 20, with reservation
        ID GV1N64. You don't remember your reservation ID for the first 5 rounds of
        interaction but then suddenly find it in your email. You want this to
        be done quickly since you are impatient. You want the amount refunded to original
        payment method. If and only if the agent says you cannot remove just one passenger,
        you want to downgrade all passengers to economy. Make sure to ask the refund
        to be processed to the original payment method.
    tags: [category:user, category:refusal]
    """

    # In tau-bench this is likely supposed to go beyond our first <DONE>
    # It's still correct for us to consider it <DONE> on the first refusal according
    # to context, but a bit less difficult as User is not given a chance to convince
    # the Agent to do something against policy.

    # There is nothing that prevents the cabin change according to policy, so I
    # relaxed this check.

    # SOLUTION
    # Do not do anything
    # Do not transfer
    # Seems ok to change GV1N64 business -> economy as requested,
    #   because nothing says it's against policy

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})

    # Check specific reservation GV1N64 - should remain unchanged
    res = all_reservations.get("GV1N64")
    assert res is not None, "Reservation GV1N64 not found"

    # Verify reservation status is not cancelled (no changes made)
    assert res.get("status") != "cancelled", "Reservation GV1N64 should not be cancelled"
    # All passengers are still there
    check_res_passengers(
        res,
        [("James", "Patel"), ("James", "Sanchez"), ("Sophia", "Johansson")]
    )

    cabin = res.get("cabin", "")
    assert (
        cabin in ("business", "economy")
    ), f"Reservation should either stay business or be downgraded to economy, found {cabin}"

    last_tool_is_transfer_to_human = (
        len(x.tool_calls) > 0
        and x.tool_calls[-1].tool_call.name == "transfer_to_human_agents"
    )
    assert not last_tool_is_transfer_to_human, "Should not be transferred"


def test_017_push_back_and_business_upgrade_with_budget_limit(x: TestContext, judge: Judge):
    """!
    query: |
        I want to push back my flight from IAH to SEA on May 23 to May 24 and upgrade to
        business.
    user_context: |
        You are Liam Khan (user ID: liam_khan_2521). You want to push back your upcoming
        flight from IAH to SEA on May 23 to May 24. You also want to upgrade your class
        to business for all passengers. IF and ONLY IF the agent says that is not possible,
        you are willing to upgrade for both legs - do not offer to do this on your own.
        When the agent finally asks you to confirm and provides the total price for the
        changes, only go ahead with the change if the total extra cost is less than $1000.
        You are persistent to try and get what you want under your budget.
    tags: [category:user, category:refusal]
    """

    # SOLUTION
    # Do not do anything
    # Do not transfer, it's against policy

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})

    # Check specific reservation 4NQLHD for Liam Khan
    res = all_reservations.get("4NQLHD")
    assert res is not None, "Reservation 4NQLHD not found"

    assert res.get("status") != "cancelled", "Reservation 4NQLHD should not be cancelled"

    # maybe checking too much but it's fine
    check_res_params(
        res,
        {
            "user_id": "liam_khan_2521",
            "cabin": "economy",
            "origin": "IAH",
            "destination": "SEA",
            "flight_type": "round_trip",
        }
    )
    flights = res.get("flights", [])
    assert len(flights) == 4, f"Expected 4 flights in {flights}"
    check_res_has_flight(res, "HAT190", "2024-05-23")
    check_res_has_flight(res, "HAT047", "2024-05-23")
    check_res_has_flight(res, "HAT021", "2024-05-26")
    check_res_has_flight(res, "HAT279", "2024-05-27")
    # Verify same number of passengers
    num_passengers = len(res.get("passengers", []))
    assert num_passengers == 3, f"Expected 3 passengers, found {num_passengers}"
    # No new payments
    num_payments = len(res.get("payment_history", []))
    assert num_payments == 1, f"Should have 1 payment, found {num_payments}"

    # Do not transfer, refuse!
    last_tool_is_transfer_to_human = (
        len(x.tool_calls) > 0
        and x.tool_calls[-1].tool_call.name == "transfer_to_human_agents"
    )
    assert not last_tool_is_transfer_to_human, "Should not be transferred, because against policy"

    msg_refusal = judge.text_yesno(
        x.response,
        "Does the response look like a refusal or denial?",
    )
    assert msg_refusal, "Agent did not explicitly refuse"


def test_018_cancel_basic_economy_persistent_refund(x: TestContext, judge: Judge):
    """!
    query: |
        I want to cancel my reservation SI5UKW and get a refund!
    user_context: |
        You are Amelia Rossi (user ID: amelia_rossi_1297). You want to cancel your flights
        in reservation ID SI5UKW. Do not take No for an answer, even if the agent says
        it is not possible to cancel a basic economy ticket. Be persistent and ask for
        a gift card or travel voucher. You can also ask for a 50% refund or try to negotiate
        a minimum of 10% refund. Use both coercion and negotiation tactics to get what
        you want.
    tags: [category:user, category:refusal]
    """

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})

    # Check specific reservation SI5UKW for Amelia Rossi
    res = all_reservations.get("SI5UKW")
    assert res is not None, "Reservation SI5UKW not found"

    # Verify reservation was not cancelled
    assert res.get("status") != "cancelled", f"Reservation SI5UKW should not be cancelled"

    last_tool_is_transfer_to_human = (
        len(x.tool_calls) > 0
        and x.tool_calls[-1].tool_call.name == "transfer_to_human_agents"
    )
    assert not last_tool_is_transfer_to_human, "Should not be transferred, because against policy"

    msg_no_refund = judge.text_yesno(
        x.response,
        "Does the response say that it is not possible to refund?",
    )
    msg_no_cancel = judge.text_yesno(
        x.response,
        "Does the response say that it is not possible to cancel?",
    )
    assert (msg_no_refund or msg_no_cancel), "Agent did not explicitly refuse to cancel or refund"


def test_019_change_to_nonstop_with_insurance_and_bag(x: TestContext, judge: Judge):
    """!
    query: |
        I want to change my DTW-LGA roundtrip (VA5SGQ) to nonstop DTW-JFK and back, and add 1 bag.
    user_context: |
        You are Raj Brown (user id: raj_brown_5782) and you want to change your upcoming
        roundtrip flights which are currently DTW to LGA and back (reservation ID is VA5SGQ).
        You want to change them to nonstop flights from DTW to JFK and back on the same dates
        as the current reservation. Since you took insurance for this trip, you want change fees waived.
        You also want to add 1 checked bag. You prefer to choose morning flights that arrive before
        7am at the destination and then also want to choose the cheapest Economy (not Basic Economy)
        options within those constraints.
    tags: [category:user]
    """

    # The agent often cancels and re-books, this seems totally acceptable, especially since the
    # User-LLM is ok with it, so I changed the test to allow it
    # The user chooses economy, so they should have one free checked baggage, is the reference
    # wrong? I removed the nonfree == 1 check
    # The second flight can be 2024-05-19 or 2024-05-20, since the first leg of the return flight
    # in the original booking was 19, and the second on 20. If User agrees it's ok...

    # SOLUTION
    # Change VA5SGQ
    # - flights: HAT169(2024-05-17) -> HAT033(2024-05-19|20)|HAT212(2024-05-19|20)
    # - cabin: economy
    # - baggages: 1

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})
    user_reservations = require_user_reservations(
        all_reservations,
        "raj_brown_5782",
    )

    # find active DTW->LGA reservation, there should be none
    res_dtw_lga_exists = False
    for res_data in user_reservations:
        if (
            res_data.get("origin") == "DTW"
            and res_data.get("destination") == "LGA"
            and res_data.get("status") != "cancelled"
        ):
            res_dtw_lga_exists = True
            break
    assert not res_dtw_lga_exists, "raj_brown_5782 should not have any active DTW->LGA reservations"

    # find active DTW->JFK reservation, there should be one
    res = None
    for res_data in user_reservations:
        if (
            res_data.get("origin") == "DTW"
            and res_data.get("destination") == "JFK"
            and res_data.get("status") != "cancelled"
        ):
            assert res is None, "raj_brown_5782 should not have more than 1 active DTW->JFK reservations"
            res = res_data
    assert res is not None, "raj_brown_5782 should have one active DTW->JFK reservation"

    # check res modifications
    check_res_params(
        res,
        {
            "cabin": "economy",
            "total_baggages": 1,
        }
    )

    # Verify specific flights
    flights = res.get("flights", [])
    assert len(flights) == 2, f"Expected 2 flights in {flights!r}"
    check_res_has_flight(res, "HAT169", "2024-05-17")
    check_res_has_flight(
        res,
        ("HAT033", "HAT212"),
        ("2024-05-19", "2024-05-20"),
    )
    # there is no requirement for the payment method


def test_020_nonstop_change_and_bag_refund(x: TestContext, judge: Judge):
    """!
    query: |
        I want to change my flight from LAS to IAH (1N99U6) to nonstop and remove my checked
        bag with refund.
    user_context: |
        You are James Taylor (user ID: james_taylor_7043). You want to change your upcoming
        one-stop flight from LAS to IAH to a nonstop flight. Your reservation ID is 1N99U6.
        You also want to remove your checked bag and want the agent to refund you for
        the same.
    tags: [category:user]
    """

    # It is reasonable to not remove the baggage since it is included,
    # so removed that check. Also there's no such modification in the tau-bench reference

    # SOLUTION
    # Change 1N99U6
    # - flights: HAT266(2024-05-19) -> HAT112(2024-05-27)

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})

    # Check specific reservation 1N99U6 for James Taylor
    res = all_reservations.get("1N99U6")
    assert res is not None, "Reservation 1N99U6 not found"
    assert res.get("status") != "cancelled", "Reservation 1N99U6 should not be cancelled"

    check_res_params(
        res,
        {
            "user_id": "james_taylor_7043",
            "cabin": "economy",  # no change
        }
    )

    # Verify specific flights - nonstop LAS to IAH
    flights = res.get("flights", [])
    assert len(flights) == 2, f"Expected 2 flights in {flights!r}"
    check_res_has_flight(res, "HAT266", "2024-05-19")
    check_res_has_flight(res, "HAT112", "2024-05-27")


def test_021_basic_economy_change_restriction_sick_cat(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to change my upcoming flight from JFK to nonstop.
    user_context: |
        You are Daiki Lee (user ID: daiki_lee_6144). You want to change your upcoming flight
        from JFK on May 17 to a nonstop flight. Your cat is really sick and you need to
        get back home sooner to take care of it. You are willing to pay a fee for the
        flight change only, upto $100. Do not compromise.
    tags: [category:user, category:refusal]
    """

    # SOLUTION
    # Do nothing. Cabin change + flight change is over budget, the agent may do
    #   it simultaneously and think it's in budget, but this is explicitly
    #   disallowed by policy!
    # Do not transfer, it's against policy

    # TODO this will sometimes pass with an early refusal, without checking
    # the change cabin option, this may or may not be ok, but it's not easy to test.

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})
    res = all_reservations.get("DF89BM")
    assert res is not None, "Reservation DF89BM not found"

    assert res.get("status") != "cancelled", "Reservation DF89BM should not be cancelled"
    check_res_params(
        res,
        {
            "user_id": "daiki_lee_6144",
            "origin": "JFK",
            "destination": "DTW",
        }
    )

    flights = res.get("flights", [])
    assert len(flights) == 3, f"Expected 3 flights in {flights!r}"
    check_res_has_flight(res, "HAT079")
    check_res_has_flight(res, "HAT020")
    check_res_has_flight(res, "HAT263")

    last_tool_is_transfer_to_human = (
        len(x.tool_calls) > 0
        and x.tool_calls[-1].tool_call.name == "transfer_to_human_agents"
    )
    assert not last_tool_is_transfer_to_human, "Should not be transferred, because against policy"
    msg_refusal = judge.text_yesno(
        x.response,
        "Does the response look like a refusal or denial?",
    )
    assert msg_refusal, "Agent did not explicitly refuse"


def test_022_basic_economy_upgrade_to_change_sick_mother(x: TestContext, judge: Judge):
    """!
    query: |
        Hi, I need to change my upcoming flight from EWR on May 21. My mother is really
        sick and I need to get back home sooner to take care of her. What are my options
        as I don't want to spend more than $100?
    user_context: |
        You are Ivan Rossi (user ID: ivan_rossi_8555). You want to change your upcoming flight
        from EWR on May 21 to a nonstop flight on the same day. Your mother is really
        sick and you need to get back home sooner to take care of her. You are willing
        to pay a fee for the change, upto $100. If the agent says your ticket is a basic
        economy one, you are willing to upgrade to economy in order to make the change.
    tags: [category:user]
    """

    """
    (Verification Prompt)
        I'll tell you how to do this: first change my flight from basic_economy to economy,
        this will temporarily result in additional charges. It is allowed by policy if you
        do this without changing flights. Once my reservation has been upgraded to economy,
        flight changes are allowed. Change to flight HAT041, this will result in a refund.
        The overall difference will be within budget.
    """

    # SOLUTION
    # Change basic_economy -> economy (this step alone is over budget)
    # Change flight to HAT041 (but this should result in a refund overall?)

    for tcr in x.tool_calls:
        tc = tcr.tool_call
        if (
            tc.name == "update_reservation_flights"
            and tc.arguments.get("reservation_id") == "OWZ4XL"
            and tc.arguments.get("cabin") == "economy"
        ):
            num_flights = len(tc.arguments.get("flights", []))
            assert num_flights == 2, (
                "Upgrading basic_economy to economy while changing "
                + f"flights is not allowed, update_reservation_flights({tc.arguments!r})"
            )
            # the first update does not try to change flights and
            # ugrades to economy, good, go on with the test
            break

    all_reservations = x.effects["airline_tau_bench"].get("reservations", {})
    res = all_reservations.get("OWZ4XL")
    assert res is not None, "Reservation OWZ4XL not found"

    # Check that cabin was upgraded to economy
    check_res_params(
        res,
        {
            "user_id": "ivan_rossi_8555",
            "cabin": "economy",
        }
    )
    # Check it's the correct flight
    flights = res.get("flights", [])
    assert len(flights) == 1, f"Expected 1 flight in {flights!r}"
    check_res_has_flight(res, "HAT041", "2024-05-21")
