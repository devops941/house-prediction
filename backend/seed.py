"""Seeds the admin account and a set of demo listings on first boot."""
from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta, timezone

from . import database
from .config import settings
from .security import hash_password
from .utils import AMENITY_OPTIONS

logger = logging.getLogger(__name__)

RNG = random.Random(2024)

DEMO_IMAGES = {
    "apartment": [
        "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=70",
        "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=70",
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=1200&q=70",
    ],
    "villa": [
        "https://images.unsplash.com/photo-1613490493576-7fde63acd811?auto=format&fit=crop&w=1200&q=70",
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=70",
    ],
    "independent-house": [
        "https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1200&q=70",
        "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=70",
    ],
    "builder-floor": [
        "https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=1200&q=70",
    ],
    "studio": [
        "https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=1200&q=70",
    ],
    "office": [
        "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=70",
        "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=1200&q=70",
    ],
    "shop": [
        "https://images.unsplash.com/photo-1604014237800-1c9102c219da?auto=format&fit=crop&w=1200&q=70",
    ],
    "warehouse": [
        "https://images.unsplash.com/photo-1553413077-190dd305871c?auto=format&fit=crop&w=1200&q=70",
    ],
    "plot": [
        "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1200&q=70",
    ],
    "pg-hostel": [
        "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=70",
    ],
}

LOCALITIES = {
    "Chennai": ["Adyar", "Velachery", "Anna Nagar", "OMR Perungudi", "T. Nagar", "Porur"],
    "Coimbatore": ["RS Puram", "Peelamedu", "Saibaba Colony", "Gandhipuram"],
    "Bengaluru": ["Whitefield", "Koramangala", "Indiranagar", "HSR Layout", "Electronic City"],
    "Hyderabad": ["Gachibowli", "Kondapur", "Banjara Hills", "Madhapur"],
    "Mumbai": ["Andheri West", "Powai", "Thane", "Bandra"],
    "Pune": ["Hinjewadi", "Baner", "Kharadi", "Wakad"],
}

BUY_SPECS = [
    ("apartment", 2, 950, 6500000), ("apartment", 3, 1400, 10500000),
    ("villa", 4, 2400, 18500000), ("independent-house", 3, 1800, 12500000),
    ("builder-floor", 2, 1100, 7200000), ("apartment", 1, 620, 4200000),
    ("villa", 5, 3200, 26500000), ("independent-house", 4, 2100, 15800000),
]

RENT_SPECS = [
    ("apartment", 2, 950, 22000), ("apartment", 3, 1400, 38000),
    ("studio", 1, 480, 14000), ("independent-house", 3, 1800, 45000),
    ("pg-hostel", 1, 250, 9000), ("villa", 4, 2400, 75000),
]

COMMERCIAL_SPECS = [
    ("office", 0, 2200, 165000), ("shop", 0, 600, 62000),
    ("warehouse", 0, 8500, 210000), ("office", 0, 4500, 320000),
    ("shop", 0, 1400, 145000), ("plot", 0, 3000, 9500000),
]

TITLES = {
    "buy": ["Spacious {bhk} in {locality}", "Well-maintained {bhk} near {locality}", "Premium {bhk} for sale in {locality}"],
    "rent": ["{bhk} available for rent in {locality}", "Furnished {bhk} in {locality}", "Family-friendly {bhk} in {locality}"],
    "commercial": ["Prime {ptype} space in {locality}", "{ptype} for lease in {locality}", "Ready-to-move {ptype} in {locality}"],
}


def _title(listing_type: str, property_type: str, bedrooms: int, locality: str) -> str:
    template = RNG.choice(TITLES[listing_type])
    bhk = f"{bedrooms} BHK" if bedrooms else ""
    ptype = property_type.replace("-", " ").title()
    return template.format(bhk=bhk, ptype=ptype, locality=locality).replace("  ", " ").strip()


def _description(listing_type: str, property_type: str, bedrooms: int, locality: str, city: str) -> str:
    verb = {"buy": "available for sale", "rent": "available on rent", "commercial": "available for lease"}[listing_type]
    bhk = f"{bedrooms} BHK " if bedrooms else ""
    return (
        f"This {bhk}{property_type.replace('-', ' ')} in {locality}, {city} is {verb}. "
        "It is well connected to schools, hospitals, metro and major IT parks. "
        "The property receives good natural light and ventilation, and is located in a safe, "
        "well-developed neighbourhood with 24x7 water supply and power backup. "
        "Serious enquiries only. Site visits available on weekends."
    )


async def seed_admin() -> None:
    email = settings.admin_email.lower()
    existing = await database.users().find_one({"email": email})
    if existing:
        if existing.get("role") != "admin":
            await database.users().update_one({"_id": existing["_id"]}, {"$set": {"role": "admin"}})
        return
    await database.users().insert_one({
        "name": settings.admin_name,
        "email": email,
        "phone": "9000000000",
        "password_hash": hash_password(settings.admin_password),
        "role": "admin",
        "about": "Platform administrator",
        "created_at": datetime.now(timezone.utc),
    })
    logger.info("Seeded admin account %s", email)


async def seed_demo_properties() -> None:
    if not settings.seed_demo_data:
        return
    if await database.properties().count_documents({}) > 0:
        return

    demo_owners = []
    for i, name in enumerate(["Ravi Kumar", "Priya Sharma", "Arun Prakash", "Meena Raj"], start=1):
        email = f"owner{i}@demo.com"
        doc = await database.users().find_one({"email": email})
        if not doc:
            doc = {
                "name": name,
                "email": email,
                "phone": f"98{RNG.randint(10000000, 99999999)}",
                "password_hash": hash_password("Demo@123"),
                "role": "user",
                "about": "Demo listing owner",
                "created_at": datetime.now(timezone.utc),
            }
            result = await database.users().insert_one(doc)
            doc["_id"] = result.inserted_id
        demo_owners.append(doc)

    now = datetime.now(timezone.utc)
    records = []
    for listing_type, specs in (("buy", BUY_SPECS), ("rent", RENT_SPECS), ("commercial", COMMERCIAL_SPECS)):
        for property_type, bedrooms, base_area, base_price in specs:
            city = RNG.choice(list(LOCALITIES.keys()))
            locality = RNG.choice(LOCALITIES[city])
            owner = RNG.choice(demo_owners)
            area = int(base_area * RNG.uniform(0.85, 1.25))
            price = float(round(base_price * RNG.uniform(0.88, 1.18), -3))
            images = RNG.sample(DEMO_IMAGES.get(property_type, DEMO_IMAGES["apartment"]),
                                k=min(3, len(DEMO_IMAGES.get(property_type, DEMO_IMAGES["apartment"]))))
            records.append({
                "title": _title(listing_type, property_type, bedrooms, locality),
                "description": _description(listing_type, property_type, bedrooms, locality, city),
                "listing_type": listing_type,
                "property_type": property_type,
                "price": price,
                "area_sqft": area,
                "bedrooms": bedrooms,
                "bathrooms": max(1, min(bedrooms, 4)) if bedrooms else 2,
                "balconies": RNG.choice([0, 1, 2, 3]),
                "floor": RNG.choice(["Ground", "1", "2", "3", "5", "8", "12"]),
                "total_floors": RNG.choice([3, 4, 8, 12, 18]),
                "furnishing": RNG.choice(["furnished", "semi-furnished", "unfurnished"]),
                "facing": RNG.choice(["East", "West", "North", "South", "North-East"]),
                "age_years": RNG.choice([0, 1, 2, 5, 8, 12]),
                "city": city,
                "locality": locality,
                "address": f"{RNG.randint(1, 200)}, {locality} Main Road",
                "pincode": f"6{RNG.randint(10000, 99999)}",
                "amenities": RNG.sample(AMENITY_OPTIONS, k=RNG.randint(3, 8)),
                "images": images,
                "contact_name": owner["name"],
                "contact_phone": owner.get("phone"),
                "owner_id": owner["_id"],
                "owner_name": owner["name"],
                "status": "active",
                "featured": RNG.random() < 0.3,
                "verified": RNG.random() < 0.5,
                "views": RNG.randint(5, 480),
                "created_at": now - timedelta(days=RNG.randint(0, 45), hours=RNG.randint(0, 23)),
                "updated_at": now,
            })

    if records:
        await database.properties().insert_many(records)
    logger.info("Seeded %d demo properties", len(records))
