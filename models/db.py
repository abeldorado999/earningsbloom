"""
Database client — wraps Supabase for all DB operations.
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

_client: Client = None

def get_db() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# ── Companies ──────────────────────────────────────────────

def get_all_companies():
    db = get_db()
    res = db.table("companies").select("*").eq("is_active", True).execute()
    return res.data

def get_company_by_slug(slug: str):
    db = get_db()
    res = db.table("companies").select("*").eq("slug", slug).single().execute()
    return res.data

def get_company_by_ticker(ticker: str):
    db = get_db()
    res = db.table("companies").select("*").eq("ticker", ticker.upper()).execute()
    return res.data[0] if res.data else None


# ── Earnings Calls ─────────────────────────────────────────

def get_earnings_by_company(company_id: str):
    db = get_db()
    res = (db.table("earnings_calls")
             .select("*, summaries(*)")
             .eq("company_id", company_id)
             .order("call_date", desc=True)
             .execute())
    return res.data

def get_earnings_detail(company_slug: str, quarter: str):
    """Fetch a single earnings call with its summary."""
    db = get_db()
    company = get_company_by_slug(company_slug)
    if not company:
        return None
    res = (db.table("earnings_calls")
             .select("*, summaries(*), companies(name, ticker, slug, exchange, sector)")
             .eq("company_id", company["id"])
             .eq("quarter", quarter.upper())
             .single()
             .execute())
    return res.data

def get_latest_earnings(limit: int = 12):
    db = get_db()
    res = (db.table("earnings_calls")
             .select("*, summaries(*), companies(name, ticker, slug, exchange, sector)")
             .eq("status", "processed")
             .order("call_date", desc=True)
             .limit(limit)
             .execute())
    return res.data

def upsert_earnings_call(data: dict):
    db = get_db()
    res = db.table("earnings_calls").upsert(data, on_conflict="company_id,quarter").execute()
    return res.data[0] if res.data else None

def upsert_summary(data: dict):
    db = get_db()
    res = db.table("summaries").upsert(data, on_conflict="earnings_call_id,language").execute()
    return res.data[0] if res.data else None

def update_earnings_status(earnings_id: str, status: str):
    db = get_db()
    db.table("earnings_calls").update({"status": status}).eq("id", earnings_id).execute()


# ── API Rate Limiting ──────────────────────────────────────

def get_gemini_calls_today() -> int:
    """Count Gemini calls made today to stay within free tier."""
    from datetime import date
    db = get_db()
    today = date.today().isoformat()
    res = db.table("api_usage").select("call_count").eq("date", today).execute()
    return res.data[0]["call_count"] if res.data else 0

def increment_gemini_calls():
    from datetime import date
    db = get_db()
    today = date.today().isoformat()
    existing = db.table("api_usage").select("id,call_count").eq("date", today).execute()
    if existing.data:
        new_count = existing.data[0]["call_count"] + 1
        db.table("api_usage").update({"call_count": new_count}).eq("date", today).execute()
    else:
        db.table("api_usage").insert({"date": today, "call_count": 1}).execute()
