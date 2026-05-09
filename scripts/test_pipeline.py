"""
Quick one-time test: scrape + process Apple's latest earnings call.
Run: python scripts/test_pipeline.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.db import get_company_by_slug
from scraper.orchestrator import process_company

print("=" * 55)
print("  EarningsBloom — Pipeline Test (Apple Inc.)")
print("=" * 55)

company = get_company_by_slug("apple")
if not company:
    print("ERROR: Apple not found in DB. Run seed script first.")
    sys.exit(1)

print(f"\nCompany: {company['name']} (CIK: {company['cik']})")
print("Checking SEC EDGAR for recent 8-K filings (last 180 days)...")
print("-" * 55)

quarters = process_company(company, days_back=180)

print("-" * 55)
if quarters:
    print(f"\nSUCCESS! Processed: {', '.join(quarters)}")
    print(f"\nView it at: http://127.0.0.1:8080/earnings/apple/{quarters[0].lower()}")
else:
    print("\nNo new earnings calls found in the last 180 days.")
    print("Trying Tesla instead...")

    tesla = get_company_by_slug("tesla")
    if tesla:
        quarters = process_company(tesla, days_back=180)
        if quarters:
            print(f"\nSUCCESS! Processed Tesla: {', '.join(quarters)}")
            print(f"\nView it at: http://127.0.0.1:8080/earnings/tesla/{quarters[0].lower()}")
        else:
            print("No recent filings for Tesla either.")
