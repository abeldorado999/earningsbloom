"""
Stock price reaction fetcher using Yahoo Finance (no API key needed).
Fetches the closing price before and after an earnings date,
calculates the % change, and returns it for storage in the DB.
"""
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def get_stock_reaction(ticker: str, earnings_date_str: str) -> dict | None:
    """
    Fetch stock price reaction around earnings date.

    Args:
        ticker: Stock ticker (e.g. "AAPL")
        earnings_date_str: ISO date string "YYYY-MM-DD"

    Returns:
        {
            "change_pct": -4.2,       # % change day after vs day before
            "price_before": 182.50,   # last close before earnings
            "price_after": 175.00,    # first close after earnings
        }
        or None if data unavailable.
    """
    try:
        date = datetime.strptime(earnings_date_str[:10], "%Y-%m-%d")

        # Look back 7 days, ahead 4 days to handle weekends/holidays
        start = date - timedelta(days=7)
        end   = date + timedelta(days=4)

        start_ts = int(start.timestamp())
        end_ts   = int(end.timestamp())

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {
            "period1":  start_ts,
            "period2":  end_ts,
            "interval": "1d",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (EarningsBloom/1.0; contact@earningsbloom.com)"
        }

        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        result = data.get("chart", {}).get("result")
        if not result:
            logger.warning(f"No Yahoo Finance data for {ticker}")
            return None

        result    = result[0]
        timestamps = result.get("timestamp", [])
        closes     = result["indicators"]["quote"][0].get("close", [])

        # Build date → close mapping, filtering None values
        dated = [
            (datetime.fromtimestamp(ts).date(), close)
            for ts, close in zip(timestamps, closes)
            if close is not None
        ]
        dated.sort()

        earnings_date = date.date()
        before = [(d, c) for d, c in dated if d <= earnings_date]
        after  = [(d, c) for d, c in dated if d >  earnings_date]

        if not before or not after:
            logger.warning(f"Insufficient price data around {earnings_date} for {ticker}")
            return None

        price_before = before[-1][1]
        price_after  = after[0][1]
        change_pct   = ((price_after - price_before) / price_before) * 100

        return {
            "change_pct":   round(change_pct,   2),
            "price_before": round(price_before,  2),
            "price_after":  round(price_after,   2),
        }

    except Exception as e:
        logger.warning(f"Stock reaction fetch failed for {ticker}: {e}")
        return None
