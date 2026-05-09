"""
Backfill stock price reactions for all existing summaries.
Reads all processed earnings_calls, fetches stock price reaction,
and updates summary_data with the results.

Run once:
  python -m scripts.backfill_stock_prices
"""
import os
import sys
import json
import logging
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pipeline.stock_price import get_stock_reaction
from models.db import get_admin_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)


def backfill():
    db = get_admin_db()

    # Fetch all processed earnings with their company ticker and summary
    logger.info("Fetching all processed earnings calls...")
    rows = (
        db.table("earnings_calls")
        .select("id, call_date, quarter, companies(ticker, name), summaries(id, summary_data)")
        .eq("status", "processed")
        .execute()
    )

    earnings = rows.data or []
    logger.info(f"Found {len(earnings)} processed earnings calls.")

    updated = 0
    skipped = 0
    failed  = 0

    for e in earnings:
        company   = e.get("companies") or {}
        ticker    = company.get("ticker", "")
        name      = company.get("name", "")
        call_date = e.get("call_date", "")
        quarter   = e.get("quarter", "")
        summaries = e.get("summaries") or []

        if not ticker or not call_date or not summaries:
            skipped += 1
            continue

        summary = summaries[0] if isinstance(summaries, list) else summaries
        summary_id   = summary.get("id")
        summary_data = summary.get("summary_data") or {}

        # Skip if already has price_reaction
        if "price_reaction" in summary_data:
            logger.info(f"  ⏭  {name} {quarter} already has price_reaction, skipping")
            skipped += 1
            continue

        logger.info(f"  📈 Fetching price for {name} ({ticker}) on {call_date}...")

        # Rate limit: 1 request per second to be polite to Yahoo Finance
        time.sleep(1)

        stock_data = get_stock_reaction(ticker, call_date)
        if not stock_data:
            logger.warning(f"  ⚠️  No price data for {ticker} on {call_date}")
            failed += 1
            continue

        # Merge price data into existing summary_data
        summary_data["price_reaction"] = stock_data["change_pct"]
        summary_data["price_before"]   = stock_data["price_before"]
        summary_data["price_after"]    = stock_data["price_after"]

        # Update the summary record
        db.table("summaries").update(
            {"summary_data": summary_data}
        ).eq("id", summary_id).execute()

        reaction_str = f"{stock_data['change_pct']:+.2f}%"
        logger.info(f"  ✅ {name} {quarter}: Stock {reaction_str}")
        updated += 1

    logger.info(f"\n{'='*50}")
    logger.info(f"Backfill complete:")
    logger.info(f"  Updated : {updated}")
    logger.info(f"  Skipped : {skipped}")
    logger.info(f"  Failed  : {failed}")


if __name__ == "__main__":
    backfill()
