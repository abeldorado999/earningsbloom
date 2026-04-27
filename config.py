import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ───────────────────────────────────────────────
GEMINI_API_KEY       = os.getenv("GEMINI_API_KEY")
SUPABASE_URL         = os.getenv("SUPABASE_URL")
SUPABASE_KEY         = os.getenv("SUPABASE_KEY")
FLASK_SECRET_KEY     = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
ADSENSE_PUBLISHER_ID = os.getenv("ADSENSE_PUBLISHER_ID", "")

# ── SEC EDGAR ──────────────────────────────────────────────
SEC_EDGAR_USER_AGENT = os.getenv("SEC_EDGAR_USER_AGENT", "EarningsBloom contact@earningsbloom.com")
SEC_EDGAR_BASE_URL   = "https://efts.sec.gov/LATEST/search-index"
SEC_EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index?q=%22earnings+call%22&dateRange=custom&startdt={start}&enddt={end}&forms=8-K"
SEC_SUBMISSIONS_URL  = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_FILING_URL       = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filename}"

# ── Gemini Models ──────────────────────────────────────────
GEMINI_STAGE1_MODEL = "gemini-2.0-flash"          # Cheap: number extraction
GEMINI_STAGE2_MODEL = "gemini-2.5-flash-preview-04-17"  # Smart: insights & summary

# ── Rate Limiting (stay within free tier) ─────────────────
MAX_GEMINI_CALLS_PER_DAY = 400   # Hard cap; free tier = 500/day for 2.5 Flash

# ── Scheduling ─────────────────────────────────────────────
# Earnings season months: Jan, Feb, Apr, May, Jul, Aug, Oct, Nov
EARNINGS_SEASON_MONTHS = [1, 2, 4, 5, 7, 8, 10, 11]
SCHEDULER_INTERVAL_EARNINGS_SEASON  = 30   # minutes
SCHEDULER_INTERVAL_OFF_SEASON       = 1440 # minutes (once daily)

# ── Site ───────────────────────────────────────────────────
SITE_NAME   = "EarningsBloom"
SITE_URL    = "https://earningsbloom.com"
SITE_TAGLINE = "Every Earnings Call. Summarized by AI. Free."
