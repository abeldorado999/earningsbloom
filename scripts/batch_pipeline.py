"""
Batch pipeline — process top companies to seed 25+ earnings pages.
Run: python scripts/batch_pipeline.py
"""
import sys, os, time, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(level=logging.WARNING)  # Suppress info logs for cleaner output

from models.db import get_admin_db, get_company_by_slug
from scraper.orchestrator import process_company

# Top companies by market cap with their DB slugs
# These must already exist in the companies table
TARGET_SLUGS = [
    "microsoft",
    "alphabet",         # Google
    "amazon",
    "nvidia",
    "meta",
    "tesla",
    "jpmorgan-chase",
    "visa",
    "unitedhealth",
    "mastercard",
    "bank-of-america",
    "eli-lilly",
    "netflix",
    "adobe",
    "salesforce",
    "qualcomm",
    "intel",
    "disney",
    "coca-cola",
    "walmart",
]

db = get_admin_db()

# Get all companies from DB to match slugs
all_companies = db.table("companies").select("id,name,ticker,slug,cik").execute().data
slug_map = {c["slug"]: c for c in all_companies}

print("=" * 60)
print("  EarningsBloom — Batch Pipeline")
print(f"  Target: {len(TARGET_SLUGS)} companies")
print("=" * 60)

# Count existing summaries
existing = db.table("summaries").select("id").execute()
print(f"\n  Existing summaries: {len(existing.data)}")
print(f"  Target after batch: {len(existing.data) + len(TARGET_SLUGS)}+\n")

success, skipped, failed = [], [], []

for i, slug in enumerate(TARGET_SLUGS, 1):
    company = slug_map.get(slug)
    if not company:
        print(f"  [{i:02d}/{len(TARGET_SLUGS)}] SKIP  {slug:30s} -- not in DB")
        skipped.append(slug)
        continue

    print(f"  [{i:02d}/{len(TARGET_SLUGS)}] >>  Processing {company['ticker']:6s} {company['name'][:28]}...")
    try:
        quarters = process_company(company, days_back=180)
        if quarters:
            print(f"         OK  {', '.join(quarters)}")
            success.append((company['ticker'], quarters))
        else:
            print(f"         --  No new filings found")
            skipped.append(slug)
    except Exception as e:
        print(f"         !!  ERROR: {str(e)[:60]}")
        failed.append((slug, str(e)[:60]))

    # Rate limit: 3 second pause between companies
    if i < len(TARGET_SLUGS):
        time.sleep(3)

print("\n" + "=" * 60)
print(f"  ✅ Success  : {len(success)}")
print(f"  ⚪ Skipped  : {len(skipped)}")
print(f"  ❌ Failed   : {len(failed)}")

final = db.table("summaries").select("id").execute()
print(f"\n  Total summaries now: {len(final.data)}")
print("=" * 60)

if failed:
    print("\nFailed companies:")
    for slug, err in failed:
        print(f"  {slug}: {err}")
