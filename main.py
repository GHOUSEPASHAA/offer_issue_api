from fastapi import FastAPI
from faker import Faker
import random
import hashlib
from datetime import datetime, timedelta
import requests
import uuid
import uvicorn

app = FastAPI(title="BOSS Offer API")

fake = Faker()

# Casino codes found within the CSV dataset
properties = {
    "BMC": "Blue Meridian Casino",
    "RLC": "Red Lantern Casino",
    "GPC": "Glass Palm Casino"
}

# The blueprint configuration for offers, making text strings fully dynamic
basic_offers_blueprint = [
    {
        "OFFER_CATEGORY": "Freeplay",
        "OFFER_CHANNEL": "ONLINE",
        "OFFER_REWARD_TYPE": "Electronic Promo Credit to Machine",
        "OFFER_REWARD_NAME": "@MW0220770",
        "OFFER_REWARD_AMOUNT": 10.0,
        "TEMPLATE_TYPE": "SINGLE_DAY",
        "TEXT_PREFIX": "$10 Free Play"
    },
    {
        "OFFER_CATEGORY": "Freeplay",
        "OFFER_CHANNEL": "express-offers",
        "OFFER_REWARD_TYPE": "Electronic Promo Credit to Machine",
        "OFFER_REWARD_NAME": "M!0AD98747",
        "OFFER_REWARD_AMOUNT": 5.0,
        "TEMPLATE_TYPE": "RANGE",
        "TEXT_PREFIX": "$5 Free Play",
        "DAYS_EXTENSION": 6
    },
    {
        "OFFER_CATEGORY": "Food Credit",
        "OFFER_CHANNEL": "express-offers",
        "OFFER_REWARD_TYPE": "Food & Beverage",
        "OFFER_REWARD_NAME": "M!0AI79539",
        "OFFER_REWARD_AMOUNT": 15.0,
        "TEMPLATE_TYPE": "RANGE",
        "TEXT_PREFIX": "$15 Food Credit",
        "DAYS_EXTENSION": 6
    },
    {
        "OFFER_CATEGORY": "Hotel",
        "OFFER_CHANNEL": "comp",
        "OFFER_REWARD_TYPE": "Room",
        "OFFER_REWARD_NAME": "B0525GENRM",
        "OFFER_REWARD_AMOUNT": 45.0,
        "TEMPLATE_TYPE": "RANGE",
        "TEXT_PREFIX": "Standard 2 Comp Nights Baseline",
        "DAYS_EXTENSION": 30
    }
]

elite_offers_blueprint = [
    {
        "OFFER_CATEGORY": "Event",
        "OFFER_CHANNEL": "drawing",
        "OFFER_REWARD_TYPE": "Unassigned or Unknown Award",
        "OFFER_REWARD_NAME": "!BCV15FPW1",
        "OFFER_REWARD_AMOUNT": 15.0,
        "TEMPLATE_TYPE": "STATIC",
        "TEXT_PREFIX": "CVB Why Not? Wed $15FP Wk1"
    },
    {
        "OFFER_CATEGORY": "Freeplay",
        "OFFER_CHANNEL": "express-offers",
        "OFFER_REWARD_TYPE": "Electronic Promo Credit to Machine",
        "OFFER_REWARD_NAME": "M!0AK77172",
        "OFFER_REWARD_AMOUNT": 50.0,
        "TEMPLATE_TYPE": "RANGE",
        "TEXT_PREFIX": "$50 Free Play",
        "DAYS_EXTENSION": 6
    },
    {
        "OFFER_CATEGORY": "Freeplay",
        "OFFER_CHANNEL": "ONLINE",
        "OFFER_REWARD_TYPE": "Electronic Promo Credit to Machine",
        "OFFER_REWARD_NAME": "@MW0263590",
        "OFFER_REWARD_AMOUNT": 100.0,
        "TEMPLATE_TYPE": "SINGLE_DAY",
        "TEXT_PREFIX": "$100 Free Play"
    },
    {
        "OFFER_CATEGORY": "Food Credit",
        "OFFER_CHANNEL": "express-offers",
        "OFFER_REWARD_TYPE": "Food & Beverage",
        "OFFER_REWARD_NAME": "M!0AL82147",
        "OFFER_REWARD_AMOUNT": 20.0,
        "TEMPLATE_TYPE": "RANGE",
        "TEXT_PREFIX": "$20 Food Credit",
        "DAYS_EXTENSION": 34
    },
    {
        "OFFER_CATEGORY": "Sweepstakes",
        "OFFER_CHANNEL": "drawing",
        "OFFER_REWARD_TYPE": "Merchandise",
        "OFFER_REWARD_NAME": "!HMSCOV",
        "OFFER_REWARD_AMOUNT": 17.2,
        "TEMPLATE_TYPE": "STATIC",
        "TEXT_PREFIX": "WCH MSC Cruise Ocean View"
    }
]


def generate_person_id(activeclubid):
    return str(
        int(
            hashlib.md5(
                ("BOSS" + str(activeclubid)).encode()
            ).hexdigest(),
            16
        ) % 90000 + 10000
    )


def generate_base_boss_offer(activeclubid):
    person_id = generate_person_id(activeclubid)
    property_code = random.choice(list(properties.keys()))
    property_name = properties[property_code]

    # Generate the base target date 
    order_timestamp = (
        datetime.now()
        - timedelta(
            days=random.randint(1, 30),
            hours=random.randint(1, 12)
        )
    )

    # Establish demographic tiers matching data behavior
    club_level = random.choices(["Basic", "Elite"], weights=[0.65, 0.35], k=1)[0]

    if club_level == "Basic":
        tier_points = float(random.choices([0, random.randint(1, 1500)], weights=[0.60, 0.40], k=1)[0])
        base_points_bal = float(random.randint(0, 100))
        blueprint = random.choice(basic_offers_blueprint)
    else:
        tier_points = float(random.choice([22803, 36365, 44207, random.randint(20000, 48000)]))
        base_points_bal = float(random.randint(15, 250))
        blueprint = random.choice(elite_offers_blueprint)

    # --- NEW ADDITION: CALCULATE DYNAMIC DATES BASED ON GAMING_DATE ---
    start_date_str = order_timestamp.strftime("%m/%d")
    
    if blueprint["TEMPLATE_TYPE"] == "SINGLE_DAY":
        # Matches: $100 Free Play (11/18-11/18) where dates equal the gaming date
        dynamic_text = f"{blueprint['TEXT_PREFIX']} ({start_date_str}-{start_date_str})"
    elif blueprint["TEMPLATE_TYPE"] == "RANGE":
        # Matches: $20 Food Credit (12/02-01/05) where it dynamically projects outward
        end_date = order_timestamp + timedelta(days=blueprint["DAYS_EXTENSION"])
        end_date_str = end_date.strftime("%m/%d")
        dynamic_text = f"{blueprint['TEXT_PREFIX']}  ({start_date_str}-{end_date_str})"
    else:
        # Handles standalone structural text templates (like cruise sweepstakes draws)
        dynamic_text = blueprint["TEXT_PREFIX"]
    # ------------------------------------------------------------------

    event_id = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()
    event_group_id = hashlib.md5(str(activeclubid).encode()).hexdigest()
    source_person_key = hashlib.md5(("BOSS" + str(activeclubid)).encode()).hexdigest()

    try:
        active_club_id_val = str(activeclubid)
    except (ValueError, TypeError):
        active_club_id_val = activeclubid

    return {
        "EVENT_TIMESTAMP": order_timestamp.isoformat() + "Z",
        "EVENT_TIMESTAMP": order_timestamp.isoformat() + "Z",
        "EVENT_TIMESTAMP_PROPERTY": order_timestamp.isoformat() + "Z",
        "EVENT_TIMESTAMP_PROPERTY_TIMEZONE": "America/Chicago",
        "DURATION": 0,
        "GAMING_DATE": order_timestamp.strftime("%m/%d/%Y"),
        "GAMING_DATE_TIMEZONE": "America/Chicago",
        "SOURCE_PERSON_KEY": source_person_key,
        "PERSON_ID": int(person_id),
        "ACTIVE_CLUB_ID": active_club_id_val,
        "CLUB_LEVEL": club_level,
        "TIER_POINTS": tier_points,
        "BASE_POINTS_BAL": base_points_bal,
        "SOURCE": "CMP",
        "ENTITY": "OFFER",
        "ACTION": "ISSUE",
        "ENTITY_ACTION": "OFFER:ISSUE",
        "DETAILS": dynamic_text,  # Dynamically constructed text field
        "EVENT_ID": event_id,
        "EVENT_GROUP_ID": event_group_id,
        "PROPERTY_NAME": property_name,
        "PROPERTY_CODE": property_code,
        "PROPERTY_ACCOUNTING_CODE": property_code,
        "SF_PROPERTY_ID": property_code,
        "PROPERTY_ID": property_code,
        "PROPERTY_ADDR1": fake.street_address(),
        "PROPERTY_ADDR2": fake.secondary_address(),
        "PROPERTY_CITY": fake.city(),
        "PROPERTY_STATE": fake.state(),
        "PROPERTY_COUNTRY": "USA",
        "PROPERTY_POSTAL_CODE": fake.postcode(),
        "TRANSACTION_AMOUNT": None,
        "PLAYER_VALUE": None,
        "CMP_CATEGORY": blueprint["OFFER_CATEGORY"],
        "OFFER_REF": None,
        "OFFER_REWARD_ID": float(random.randint(110000000, 115000000)),
        "OFFER_REWARD_AMOUNT": blueprint["OFFER_REWARD_AMOUNT"],
        "OFFER_REWARD_TYPE": blueprint["OFFER_REWARD_TYPE"],
        "OFFER_REWARD_NAME": blueprint["OFFER_REWARD_NAME"],
        "OFFER_IS_ONETIME_PRIZE": False,
        "OFFER_EARN_TYPE": random.choice(["Points", "WScore"]),
        "OFFER_EARN_AMOUNT": float(random.choice([0.0, 1.0])),
        "OFFER_IS_CASHBACK": False,
        "OFFER_PRIZE_NAME": dynamic_text,  # Dynamically constructed text field
        "OFFER_PRIZE_LEVEL": 0.0,
        "OFFER_REWARD_VALUE": 0.0,
        "PROMOTION_EVENT_DETAIL": dynamic_text,  # Dynamically constructed text field
        "METADATA": None,
        "TIMESERIES_CMP_OFFER_KEY": hashlib.md5((blueprint["OFFER_REWARD_NAME"] + str(event_id)).encode()).hexdigest(),
        "LAST_SYNCED": datetime.now().isoformat() + "Z",
        "LOAD_TIMESTAMP": None,
        "DW_TASKID": random.randint(1000, 9999),
        "DW_USERID": random.randint(10000, 99999),
        "OFFER_CATEGORY": blueprint["OFFER_CATEGORY"],
        "OFFER_CHANNEL": blueprint["OFFER_CHANNEL"]
    }


@app.get("/v1/offer-issue")
async def boss_offer():
    api_url = (
        "https://casino-api-ob26.onrender.com/"
        "v1/player-activity"
    )

    response = requests.get(api_url)
    player_data = response.json()

    unique_activeclubids = []
    seen = set()

    for row in player_data:
        activeclubid = row["ACTIVECLUBID"]

        if activeclubid not in seen:
            seen.add(activeclubid)
            unique_activeclubids.append(activeclubid)

        if len(unique_activeclubids) == 50:
            break

    final_records = []
    for activeclubid in unique_activeclubids:
        final_records.append(
            generate_base_boss_offer(activeclubid)
        )

    return final_records


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8006
    )
