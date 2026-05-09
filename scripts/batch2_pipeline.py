"""Second batch for remaining companies."""
import sys, os, time, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(level=logging.WARNING)
from dotenv import load_dotenv; load_dotenv()
from models.db import get_admin_db
from scraper.orchestrator import process_company

db = get_admin_db()
all_co = db.table("companies").select("id,name,ticker,slug,cik").execute().data
slug_map = {c["slug"]: c for c in all_co}

targets = [
    "berkshire-hathaway", "exxonmobil", "broadcom", "goldman-sachs",
    "johnson-and-johnson", "pfizer", "paypal", "cloudflare",
    "snowflake", "shopify", "servicenow", "lockheed-martin",
    "moderna", "zoom", "workday", "starbucks", "nike",
]

print("=" * 55)
print("  Second Batch Pipeline")
print("=" * 55)

for slug in targets:
    co = slug_map.get(slug)
    if not co:
        print(f"  SKIP {slug} -- not in DB")
        continue
    name_short = co["name"][:28]
    ticker = co["ticker"]
    print(f"  >> {ticker:<6} {name_short}...", end=" ", flush=True)
    try:
        quarters = process_company(co, days_back=180)
        if quarters:
            print(f"OK  {quarters}")
        else:
            print("-- no filings")
    except Exception as e:
        print(f"!! {str(e)[:50]}")
    time.sleep(2)

final = db.table("summaries").select("id").execute()
print(f"\nTotal summaries now: {len(final.data)}")
