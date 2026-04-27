"""
One-time script to seed the database with top US companies.
Run once: python scripts/seed_companies.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.db import get_db
import uuid

# Top 50 US companies by market cap + search volume
# Format: (name, ticker, exchange, sector, cik, slug)
COMPANIES = [
    # Technology
    ("Apple Inc.",              "AAPL",  "NASDAQ", "Technology",        "0000320193", "apple"),
    ("Microsoft Corporation",   "MSFT",  "NASDAQ", "Technology",        "0000789019", "microsoft"),
    ("NVIDIA Corporation",      "NVDA",  "NASDAQ", "Technology",        "0001045810", "nvidia"),
    ("Alphabet Inc.",           "GOOGL", "NASDAQ", "Technology",        "0001652044", "alphabet"),
    ("Meta Platforms Inc.",     "META",  "NASDAQ", "Technology",        "0001326801", "meta"),
    ("Amazon.com Inc.",         "AMZN",  "NASDAQ", "Technology",        "0001018724", "amazon"),
    ("Tesla Inc.",              "TSLA",  "NASDAQ", "Automotive/Tech",   "0001318605", "tesla"),
    ("Salesforce Inc.",         "CRM",   "NYSE",   "Technology",        "0001108524", "salesforce"),
    ("Adobe Inc.",              "ADBE",  "NASDAQ", "Technology",        "0000796343", "adobe"),
    ("Intel Corporation",       "INTC",  "NASDAQ", "Technology",        "0000050863", "intel"),
    ("Advanced Micro Devices",  "AMD",   "NASDAQ", "Technology",        "0000002488", "amd"),
    ("Palantir Technologies",   "PLTR",  "NYSE",   "Technology",        "0001321655", "palantir"),
    ("Snowflake Inc.",          "SNOW",  "NYSE",   "Technology",        "0001640147", "snowflake"),
    ("Cloudflare Inc.",         "NET",   "NYSE",   "Technology",        "0001477333", "cloudflare"),
    ("ServiceNow Inc.",         "NOW",   "NYSE",   "Technology",        "0001373715", "servicenow"),
    # Finance
    ("JPMorgan Chase & Co.",    "JPM",   "NYSE",   "Finance",           "0000019617", "jpmorgan-chase"),
    ("Goldman Sachs Group",     "GS",    "NYSE",   "Finance",           "0000886982", "goldman-sachs"),
    ("Visa Inc.",               "V",     "NYSE",   "Finance",           "0001403161", "visa"),
    ("Mastercard Inc.",         "MA",    "NYSE",   "Finance",           "0001141391", "mastercard"),
    ("Berkshire Hathaway",      "BRK.B", "NYSE",   "Finance",           "0001067983", "berkshire-hathaway"),
    ("Bank of America Corp.",   "BAC",   "NYSE",   "Finance",           "0000070858", "bank-of-america"),
    ("PayPal Holdings Inc.",    "PYPL",  "NASDAQ", "Finance",           "0001633917", "paypal"),
    # Healthcare
    ("Johnson & Johnson",       "JNJ",   "NYSE",   "Healthcare",        "0000200406", "johnson-and-johnson"),
    ("Eli Lilly and Co.",       "LLY",   "NYSE",   "Healthcare",        "0000059478", "eli-lilly"),
    ("UnitedHealth Group",      "UNH",   "NYSE",   "Healthcare",        "0000731766", "unitedhealth"),
    ("Pfizer Inc.",             "PFE",   "NYSE",   "Healthcare",        "0000078003", "pfizer"),
    ("Moderna Inc.",            "MRNA",  "NASDAQ", "Healthcare",        "0001682852", "moderna"),
    # Consumer
    ("Walmart Inc.",            "WMT",   "NYSE",   "Consumer",          "0000104169", "walmart"),
    ("McDonald's Corporation",  "MCD",   "NYSE",   "Consumer",          "0000063908", "mcdonalds"),
    ("Nike Inc.",               "NKE",   "NYSE",   "Consumer",          "0000320187", "nike"),
    ("Coca-Cola Co.",           "KO",    "NYSE",   "Consumer",          "0000021344", "coca-cola"),
    ("Starbucks Corporation",   "SBUX",  "NASDAQ", "Consumer",          "0000829224", "starbucks"),
    ("Netflix Inc.",            "NFLX",  "NASDAQ", "Entertainment",     "0001065280", "netflix"),
    ("Disney (The Walt) Co.",   "DIS",   "NYSE",   "Entertainment",     "0001001039", "disney"),
    # Energy
    ("ExxonMobil Corporation",  "XOM",   "NYSE",   "Energy",            "0000034088", "exxonmobil"),
    ("Chevron Corporation",     "CVX",   "NYSE",   "Energy",            "0000093410", "chevron"),
    # Telecom
    ("AT&T Inc.",               "T",     "NYSE",   "Telecom",           "0000732717", "att"),
    ("Verizon Communications",  "VZ",    "NYSE",   "Telecom",           "0000732712", "verizon"),
    # Aerospace & Defense
    ("Boeing Co.",              "BA",    "NYSE",   "Aerospace",         "0000012927", "boeing"),
    ("Lockheed Martin Corp.",   "LMT",   "NYSE",   "Aerospace",         "0000936468", "lockheed-martin"),
    # Semiconductor
    ("TSMC (Taiwan Semi.)",     "TSM",   "NYSE",   "Semiconductors",    "0001046179", "tsmc"),
    ("Broadcom Inc.",           "AVGO",  "NASDAQ", "Semiconductors",    "0001730168", "broadcom"),
    ("Qualcomm Inc.",           "QCOM",  "NASDAQ", "Semiconductors",    "0000804328", "qualcomm"),
    # E-Commerce / Retail
    ("Shopify Inc.",            "SHOP",  "NYSE",   "E-Commerce",        "0001594805", "shopify"),
    ("eBay Inc.",               "EBAY",  "NASDAQ", "E-Commerce",        "0001065088", "ebay"),
    # Cloud / SaaS
    ("Workday Inc.",            "WDAY",  "NASDAQ", "Cloud/SaaS",        "0001327811", "workday"),
    ("Databricks",              "DBRX",  "PRIVATE","AI/Data",           None,          "databricks"),
    ("Twilio Inc.",             "TWLO",  "NYSE",   "Cloud/SaaS",        "0001418819", "twilio"),
    ("HubSpot Inc.",            "HUBS",  "NYSE",   "Cloud/SaaS",        "0001404655", "hubspot"),
    ("Zoom Video Comm.",        "ZM",    "NASDAQ", "Cloud/SaaS",        "0001585521", "zoom"),
]


def seed():
    db = get_db()
    inserted = 0
    skipped  = 0

    for name, ticker, exchange, sector, cik, slug in COMPANIES:
        if cik is None:
            # Private company — skip (no SEC filings)
            skipped += 1
            continue

        record = {
            "id":        str(uuid.uuid4()),
            "name":      name,
            "ticker":    ticker,
            "exchange":  exchange,
            "sector":    sector,
            "cik":       cik.lstrip("0"),  # Store without leading zeros
            "slug":      slug,
            "is_active": True,
        }

        try:
            # Upsert by slug so running twice is safe
            db.table("companies").upsert(record, on_conflict="slug").execute()
            print(f"  ✅  {ticker:6s} — {name}")
            inserted += 1
        except Exception as e:
            print(f"  ❌  {ticker:6s} — {name}: {e}")
            skipped += 1

    print(f"\nDone. {inserted} companies inserted/updated, {skipped} skipped.")


if __name__ == "__main__":
    print("Seeding companies into Supabase...\n")
    seed()
