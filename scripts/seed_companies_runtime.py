"""
Direct-Mongo company insert that matches the RUNTIME schema exactly.

Writes company documents into the `verifai.companies` collection using
the same field shape the API expects (CompanyPublic / CompanyListItem):
  - uid (unique)
  - company_name
  - role        (a default hiring role title, e.g. "Software Engineer Intern")
  - location    (e.g. "San Francisco, United States")
  - industry
  - logo_url
  - description, website, company_size (optional)
  - follower_count, open_roles_count  (numeric counters)
  - created_at, updated_at            (UTC datetimes)

This seeder inserts BOTH:
  1. 50 fictional companies (COMPANIES list) — using a clearbit logo fallback.
  2. 25+ real top multinational corporations (MNC_COMPANIES list) — using
     the explicit, verified Wikimedia logo URLs.

This does NOT alter any existing collection or schema. It only inserts new
docs into `verifai.companies`. Safe to re-run: it skips companies whose
`uid` already exists. Fictional and MNC companies use different uid
namespaces so they dedupe independently.

Run from the backend directory with the venv active:
    python scripts/seed_companies_runtime.py
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

# Allow `python scripts/seed_companies_runtime.py` to find the `app` package.
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from pymongo import MongoClient

# Uses the same URI the app uses (MONGODB_URI env var, loaded by app.core.config).
# We import the settings object so this script picks up .env automatically.
from app.core.config import settings

DB_NAME = "verifai"
COLL = "companies"
_NS = uuid.NAMESPACE_DNS

INDUSTRIES = [
    "Software & SaaS",
    "Artificial Intelligence",
    "Cybersecurity",
    "Cloud & Infrastructure",
    "Fintech",
    "Healthtech",
    "Edtech",
    "E-commerce & Retail",
    "Automotive",
    "Manufacturing",
    "Banking",
    "Gaming",
    "Blockchain & Web3",
    "Robotics",
    "Aerospace & Defense",
    "Telecom",
    "Government & Public Sector",
]

# 50 (name, city, country) pairs. Logo URLs use clearbit (real public domain pattern).
COMPANIES = [
    ("Northwind Labs",         "San Francisco",   "United States"),
    ("Helios AI",              "New York",        "United States"),
    ("BluePine Security",      "Austin",          "United States"),
    ("Stratus Cloud",          "Seattle",         "United States"),
    ("QuantaPay",              "Chicago",         "United States"),
    ("Vita Health",            "Boston",          "United States"),
    ("Lumen Learn",            "Pittsburgh",      "United States"),
    ("Emporio Engine",         "Los Angeles",     "United States"),
    ("Vector Motors",          "Detroit",         "United States"),
    ("Forge Manufacturing",    "Cleveland",       "United States"),
    ("Atlas Capital",          "Charlotte",       "United States"),
    ("Pixel Forge Studios",    "Los Angeles",     "United States"),
    ("Ledgerline Web3",        "Miami",           "United States"),
    ("Ironhand Robotics",      "Pittsburgh",      "United States"),
    ("Stellar Aero",           "Denver",          "United States"),
    ("Beacon Telecom",         "Atlanta",         "United States"),
    ("Civic Forge",            "Washington",      "United States"),
    ("Maple AI",               "Toronto",         "Canada"),
    ("Polar Cloud",            "Vancouver",       "Canada"),
    ("Maple Fintech",          "Montreal",        "Canada"),
    ("Lakeside Health",        "Ottawa",          "Canada"),
    ("Kelp Studios",           "Halifax",         "Canada"),
    ("Brit Robotics",          "London",          "United Kingdom"),
    ("Thames Pay",             "London",          "United Kingdom"),
    ("Highland AI",            "Edinburgh",       "United Kingdom"),
    ("Cobalt Security",        "Manchester",      "United Kingdom"),
    ("Ridge Learn",            "Bristol",         "United Kingdom"),
    ("Rhine Cloud",            "Berlin",          "Germany"),
    ("Bavarian Motors",        "Munich",          "Germany"),
    ("Elbe Pay",               "Hamburg",         "Germany"),
    ("Bionic Health",          "Frankfurt",       "Germany"),
    ("Seine Studios",          "Paris",           "France"),
    ("Louvre AI",              "Lyon",            "France"),
    ("Vendée Cloud",           "Nantes",          "France"),
    ("Iberia Robotics",        "Madrid",          "Spain"),
    ("Catalan Pay",            "Barcelona",       "Spain"),
    ("Tuscan Studios",         "Milan",           "Italy"),
    ("Lazio Cloud",            "Rome",            "Italy"),
    ("Amstel AI",              "Amsterdam",       "Netherlands"),
    ("Fjord Cloud",            "Oslo",            "Norway"),
    ("Aurora Robotics",        "Stockholm",       "Sweden"),
    ("Baltic Pay",             "Helsinki",        "Finland"),
    ("Zenith AI",              "Tokyo",           "Japan"),
    ("Sakura Studios",         "Osaka",           "Japan"),
    ("Han River Cloud",        "Seoul",           "South Korea"),
    ("Lion City Pay",          "Singapore",       "Singapore"),
    ("Koala Health",           "Sydney",          "Australia"),
    ("Outback Cloud",          "Melbourne",       "Australia"),
    ("Saffron AI",             "Bengaluru",       "India"),
    ("Ganges Studios",         "Mumbai",          "India"),
    ("Cape Robotics",          "Cape Town",       "South Africa"),
]

# 30 real top multinational corporations. Each tuple is:
#   (company_name, headquarters_city, headquarters_country, industry, default_role, logo_url)
#
# Logo URLs are stable Wikimedia Commons hosted images (publicly accessible).
# These entries are merged into the runtime seeder so users see real MNCs alongside
# the fictional seed data.
MNC_COMPANIES = [
    # (company_name, headquarters_city, headquarters_country, industry, default_role, logo_url)
    ("Google",            "Mountain View",   "United States",  "Software & SaaS",          "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/512px-Google_2015_logo.svg.png"),
    ("Microsoft",         "Redmond",         "United States",  "Software & SaaS",          "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/Microsoft_logo_%282012%29.svg/512px-Microsoft_logo_%282012%29.svg.png"),
    ("Apple",             "Cupertino",       "United States",  "Consumer Electronics",     "Hardware Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Apple_logo_black.svg/488px-Apple_logo_black.svg.png"),
    ("Amazon",            "Seattle",         "United States",  "E-commerce & Retail",      "Software Development Engineer", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Amazon_logo.svg/512px-Amazon_logo.svg.png"),
    ("Meta",              "Menlo Park",      "United States",  "Social Media",             "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Meta_Platforms_Inc._logo.svg/512px-Meta_Platforms_Inc._logo.svg.png"),
    ("Netflix",           "Los Gatos",       "United States",  "Media & Entertainment",    "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/512px-Netflix_2015_logo.svg.png"),
    ("Tesla",             "Austin",          "United States",  "Automotive",               "Mechanical Engineer",   "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Tesla_Motors.svg/512px-Tesla_Motors.svg.png"),
    ("NVIDIA",            "Santa Clara",     "United States",  "Semiconductors",           "Hardware Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Nvidia_logo.svg/512px-Nvidia_logo.svg.png"),
    ("Intel",             "Santa Clara",     "United States",  "Semiconductors",           "Hardware Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Intel_logo_%282006-2020%29.svg/512px-Intel_logo_%282006-2020%29.svg.png"),
    ("IBM",               "Armonk",          "United States",  "Software & SaaS",          "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/IBM_logo.svg/512px-IBM_logo.svg.png"),
    ("Oracle",            "Austin",          "United States",  "Software & SaaS",          "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Oracle_logo.svg/512px-Oracle_logo.svg.png"),
    ("Salesforce",        "San Francisco",   "United States",  "Software & SaaS",          "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Salesforce.com_logo.svg/512px-Salesforce.com_logo.svg.png"),
    ("Adobe",             "San Jose",        "United States",  "Software & SaaS",          "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Adobe_Corporate_Wordmark.svg/512px-Adobe_Corporate_Wordmark.svg.png"),
    ("Uber",              "San Francisco",   "United States",  "Transportation",           "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Uber_logo_2018.svg/512px-Uber_logo_2018.svg.png"),
    ("Airbnb",            "San Francisco",   "United States",  "Hospitality",              "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Airbnb_Logo_B%C3%A9lo.svg/512px-Airbnb_Logo_B%C3%A9lo.svg.png"),
    ("Goldman Sachs",     "New York",        "United States",  "Banking",                  "Financial Analyst",     "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Goldman_Sachs.svg/512px-Goldman_Sachs.svg.png"),
    ("JPMorgan Chase",    "New York",        "United States",  "Banking",                  "Financial Analyst",     "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/JPMorgan_Chase.svg/512px-JPMorgan_Chase.svg.png"),
    ("Walmart",           "Bentonville",     "United States",  "E-commerce & Retail",      "Data Analyst",          "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Walmart_logo.svg/512px-Walmart_logo.svg.png"),
    ("McDonald's",        "Chicago",         "United States",  "Food & Beverage",          "Operations Analyst",    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/McDonald%27s_Golden_Arches.svg/512px-McDonald%27s_Golden_Arches.svg.png"),
    ("Coca-Cola",         "Atlanta",         "United States",  "Food & Beverage",          "Marketing Analyst",     "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Coca-Cola_logo.svg/512px-Coca-Cola_logo.svg.png"),
    ("Pfizer",            "New York",        "United States",  "Pharmaceuticals",          "Research Scientist",    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Pfizer_logo.svg/512px-Pfizer_logo.svg.png"),
    ("Johnson & Johnson", "New Brunswick",   "United States",  "Pharmaceuticals",          "Research Scientist",    "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Johnson_%26_Johnson-Logo.svg/512px-Johnson_%26_Johnson-Logo.svg.png"),
    ("Visa",              "San Francisco",   "United States",  "Fintech",                  "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Visa_Inc._logo.svg/512px-Visa_Inc._logo.svg.png"),
    ("Mastercard",        "Purchase",        "United States",  "Fintech",                  "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Mastercard-logo.svg/512px-Mastercard-logo.svg.png"),
    ("Spotify",           "Stockholm",       "Sweden",         "Media & Entertainment",    "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/512px-Spotify_logo_without_text.svg.png"),
    ("Samsung",           "Suwon",           "South Korea",    "Consumer Electronics",     "Hardware Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Samsung_Logo.svg/512px-Samsung_Logo.svg.png"),
    ("Sony",              "Tokyo",           "Japan",          "Consumer Electronics",     "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Sony_logo.svg/512px-Sony_logo.svg.png"),
    ("Toyota",            "Toyota City",     "Japan",          "Automotive",               "Mechanical Engineer",   "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Toyota_carlogo.svg/512px-Toyota_carlogo.svg.png"),
    ("BMW",               "Munich",          "Germany",        "Automotive",               "Mechanical Engineer",   "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/BMW.svg/512px-BMW.svg.png"),
    ("SAP",               "Walldorf",        "Germany",        "Software & SaaS",          "Software Engineer",     "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/SAP_2011_logo.svg/512px-SAP_2011_logo.svg.png"),
]

DEFAULT_ROLES = [
    "Software Engineer",
    "Senior Software Engineer",
    "Machine Learning Engineer",
    "Data Engineer",
    "DevOps Engineer",
    "Security Engineer",
    "Cloud Engineer",
    "Product Manager",
    "Mobile Engineer",
    "Frontend Engineer",
    "Backend Engineer",
    "Full-Stack Engineer",
]

COMPANY_SIZES = ["1-10", "11-50", "51-200", "201-500", "501-1,000", "1,001-5,000", "5,001-10,000", "10,000+"]

# Default sizes for the well-known MNCs (real-world-ish team sizes).
_MNC_COMPANY_SIZES = {
    "Google": "10,000+",
    "Microsoft": "10,000+",
    "Apple": "10,000+",
    "Amazon": "10,000+",
    "Meta": "10,000+",
    "Netflix": "5,001-10,000",
    "Tesla": "10,000+",
    "NVIDIA": "10,000+",
    "Intel": "10,000+",
    "IBM": "10,000+",
    "Oracle": "10,000+",
    "Salesforce": "10,000+",
    "Adobe": "10,000+",
    "Uber": "10,000+",
    "Airbnb": "5,001-10,000",
    "Goldman Sachs": "10,000+",
    "JPMorgan Chase": "10,000+",
    "Walmart": "10,000+",
    "McDonald's": "10,000+",
    "Coca-Cola": "10,000+",
    "Pfizer": "10,000+",
    "Johnson & Johnson": "10,000+",
    "Visa": "10,000+",
    "Mastercard": "10,000+",
    "Spotify": "5,001-10,000",
    "Samsung": "10,000+",
    "Sony": "10,000+",
    "Toyota": "10,000+",
    "BMW": "10,000+",
    "SAP": "10,000+",
}


def _slugify(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "" for c in name).strip() or "company"


def _website_from_slug(slug: str) -> str:
    """Build a best-effort website URL from the slug for fictional/MNC companies."""
    return f"https://{slug}.com"


def build_docs() -> list[dict]:
    now = datetime.now(timezone.utc)
    docs: list[dict] = []

    # --- Fictional companies (uses i-indexed uid namespace; clearbit logo fallback) ---
    for i, (name, city, country) in enumerate(COMPANIES):
        slug = _slugify(name)
        industry = INDUSTRIES[i % len(INDUSTRIES)]
        role = DEFAULT_ROLES[i % len(DEFAULT_ROLES)]
        company_size = COMPANY_SIZES[i % len(COMPANY_SIZES)]
        uid = str(uuid.uuid5(_NS, f"verifai.runtime.company.{slug}.{i}"))

        created = now - timedelta(days=(i * 7) % 720)
        updated = now - timedelta(days=(i * 2) % 30)

        docs.append({
            "uid": uid,
            "company_name": name,
            "role": role,
            "location": f"{city}, {country}",
            "industry": industry,
            "logo_url": f"https://logo.clearbit.com/{slug}.com",
            "description": (
                f"{industry} company based in {city}, {country}. "
                f"Team size: {company_size}. Building reliable, well-engineered products."
            ),
            "website": _website_from_slug(slug),
            "company_size": company_size,
            "follower_count": 0,
            "open_roles_count": 0,
            "created_at": created,
            "updated_at": updated,
        })

    # --- Real-world MNCs (uses name-based uid namespace; explicit logo URL) ---
    for j, (name, city, country, industry, role, logo_url) in enumerate(MNC_COMPANIES):
        slug = _slugify(name)
        company_size = _MNC_COMPANY_SIZES.get(name, "10,000+")
        # Use a separate namespace prefix ("mnc") so MNC uids never collide
        # with the fictional companies' uids and re-runs remain idempotent.
        uid = str(uuid.uuid5(_NS, f"verifai.runtime.company.mnc.{slug}.{_slugify(name)}"))

        # Stagger timestamps so MNC docs appear interspersed in the collection.
        created = now - timedelta(days=((j * 11) + 3) % 720)
        updated = now - timedelta(days=(j * 1) % 30)

        docs.append({
            "uid": uid,
            "company_name": name,
            "role": role,
            "location": f"{city}, {country}",
            "industry": industry,
            "logo_url": logo_url,
            "description": (
                f"Global leader in {industry}, headquartered in {city}, {country}. "
                f"Currently hiring across engineering, product, and operations."
            ),
            "website": _website_from_slug(slug),
            "company_size": company_size,
            "follower_count": 0,
            "open_roles_count": 0,
            "created_at": created,
            "updated_at": updated,
        })

    return docs


def main() -> None:
    if not settings.MONGODB_URI:
        raise SystemExit("MONGODB_URI is not set in .env")

    client = MongoClient(settings.MONGODB_URI)
    coll = client[DB_NAME][COLL]

    docs = build_docs()
    existing_uids = {d["uid"] for d in coll.find({}, {"uid": 1, "_id": 0})}
    to_insert = [d for d in docs if d["uid"] not in existing_uids]

    if not to_insert:
        print(f"No new companies to insert. Existing runtime rows: {len(existing_uids)}")
        return

    # ordered=False so a single dup-key on follower_count index (etc.) doesn't abort the batch.
    result = coll.insert_many(to_insert, ordered=False)
    print(
        f"Inserted {len(result.inserted_ids)} companies into '{DB_NAME}.{COLL}'. "
        f"Skipped {len(docs) - len(to_insert)} already present."
    )


if __name__ == "__main__":
    main()