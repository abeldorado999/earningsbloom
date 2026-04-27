"""
EarningsBloom — Main Flask Application
AI-powered earnings call summarizer
"""
import logging
import math
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, abort
from models.db import (
    get_all_companies, get_company_by_slug,
    get_earnings_by_company, get_earnings_detail, get_latest_earnings,
)
from scraper.scheduler import start_scheduler, stop_scheduler
from config import SITE_NAME, SITE_URL, SITE_TAGLINE, ADSENSE_PUBLISHER_ID

# ── Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── App Init ───────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = __import__("config").FLASK_SECRET_KEY

# ── Jinja globals ──────────────────────────────────────────
app.jinja_env.globals.update(
    site_name=SITE_NAME,
    site_url=SITE_URL,
    site_tagline=SITE_TAGLINE,
    adsense_id=ADSENSE_PUBLISHER_ID,
    current_year=datetime.now().year,
)


# ── Template filters ───────────────────────────────────────
@app.template_filter("sentiment_color")
def sentiment_color(sentiment: str) -> str:
    return {"bullish": "green", "bearish": "red", "neutral": "amber"}.get(
        (sentiment or "neutral").lower(), "amber"
    )

@app.template_filter("sentiment_emoji")
def sentiment_emoji(sentiment: str) -> str:
    return {"bullish": "🟢", "bearish": "🔴", "neutral": "🟡"}.get(
        (sentiment or "neutral").lower(), "🟡"
    )

@app.template_filter("beat_label")
def beat_label(beat) -> str:
    if beat is True:  return "✅ Beat"
    if beat is False: return "❌ Miss"
    return "—"

@app.template_filter("quarter_display")
def quarter_display(quarter: str) -> str:
    """Q2-2026 → Q2 FY2026"""
    if not quarter: return ""
    parts = quarter.split("-")
    return f"{parts[0]} FY{parts[1]}" if len(parts) == 2 else quarter


# ── Routes ─────────────────────────────────────────────────

@app.route("/")
def index():
    latest = get_latest_earnings(limit=12)
    return render_template("index.html",
        earnings=latest,
        page_title=f"{SITE_NAME} — {SITE_TAGLINE}",
        meta_description=(
            "Free AI-powered earnings call summaries for every public company. "
            "Get instant TLDR, revenue vs estimates, CEO guidance and sentiment — "
            "no paywall, no sign-up."
        ),
    )


@app.route("/company/<slug>")
def company(slug: str):
    company = get_company_by_slug(slug)
    if not company:
        abort(404)
    earnings = get_earnings_by_company(company["id"])
    return render_template("company.html",
        company=company,
        earnings=earnings,
        page_title=f"{company['name']} Earnings Call Summaries | {SITE_NAME}",
        meta_description=(
            f"All {company['name']} ({company['ticker']}) earnings call summaries. "
            f"AI-generated TLDR, revenue vs estimates, and CEO guidance for every quarter. Free."
        ),
    )


@app.route("/earnings/<company_slug>/<quarter>")
def earnings_detail(company_slug: str, quarter: str):
    detail = get_earnings_detail(company_slug, quarter.upper())
    if not detail or not detail.get("summaries"):
        abort(404)

    company  = detail.get("companies", {})
    summary  = detail["summaries"][0] if isinstance(detail.get("summaries"), list) else detail.get("summaries", {})
    q_display = quarter_display(quarter.upper())

    # Build rich title for SEO
    beat_str = ""
    if summary.get("revenue_beat") is True:  beat_str = "Revenue Beat, "
    if summary.get("revenue_beat") is False: beat_str = "Revenue Miss, "
    sentiment_str = (summary.get("sentiment") or "").capitalize()

    page_title = (
        f"{company.get('name','Company')} {q_display} Earnings Summary"
        f" — {beat_str}{sentiment_str} Outlook | {SITE_NAME}"
    )
    meta_desc = (
        f"{company.get('name','')} reported {summary.get('revenue_actual','N/A')} revenue "
        f"in {q_display}. AI summary: top wins, concerns, CEO guidance & key quotes. Free."
    )

    return render_template("earnings_detail.html",
        company=company,
        earnings=detail,
        summary=summary,
        quarter=quarter.upper(),
        quarter_display=q_display,
        page_title=page_title,
        meta_description=meta_desc,
        canonical_url=f"{SITE_URL}/earnings/{company_slug}/{quarter.lower()}",
    )


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    results = []
    if query and len(query) >= 2:
        all_companies = get_all_companies()
        q_lower = query.lower()
        results = [
            c for c in all_companies
            if q_lower in c["name"].lower() or q_lower in c["ticker"].lower()
        ]
    return render_template("search.html",
        query=query,
        results=results,
        page_title=f"Search — {SITE_NAME}",
        meta_description=f"Search for earnings call summaries across thousands of companies.",
    )


@app.route("/sector/<sector>")
def sector(sector: str):
    all_companies = get_all_companies()
    sector_companies = [c for c in all_companies if c.get("sector","").lower() == sector.lower()]
    return render_template("sector.html",
        sector=sector.title(),
        companies=sector_companies,
        page_title=f"{sector.title()} Earnings Summaries | {SITE_NAME}",
        meta_description=(
            f"AI-powered earnings call summaries for all {sector.title()} companies. "
            f"Free revenue vs estimate analysis, CEO guidance, and sentiment."
        ),
    )


@app.route("/companies")
def companies():
    all_companies = get_all_companies()
    # Group by sector
    sectors = {}
    for c in all_companies:
        s = c.get("sector", "Other")
        sectors.setdefault(s, []).append(c)
    return render_template("companies.html",
        sectors=sectors,
        total=len(all_companies),
        page_title=f"All Companies — {SITE_NAME}",
        meta_description="Browse all companies with AI-powered earnings call summaries on EarningsBloom.",
    )


@app.route("/about")
def about():
    return render_template("about.html",
        page_title=f"About — {SITE_NAME}",
        meta_description=f"Learn how {SITE_NAME} uses AI to summarize earnings calls from public companies instantly.",
    )


# ── Sitemap ────────────────────────────────────────────────

@app.route("/sitemap.xml")
def sitemap():
    companies = get_all_companies()
    latest    = get_latest_earnings(limit=500)

    static_urls = [
        {"loc": SITE_URL + "/",          "priority": "1.0", "changefreq": "daily"},
        {"loc": SITE_URL + "/companies", "priority": "0.8", "changefreq": "weekly"},
        {"loc": SITE_URL + "/about",     "priority": "0.5", "changefreq": "monthly"},
    ]
    company_urls = [
        {"loc": f"{SITE_URL}/company/{c['slug']}", "priority": "0.8", "changefreq": "quarterly"}
        for c in companies
    ]
    earnings_urls = [
        {
            "loc": f"{SITE_URL}/earnings/{e['companies']['slug']}/{e['quarter'].lower()}",
            "priority": "0.9",
            "changefreq": "yearly",
            "lastmod": e.get("call_date", date.today().isoformat()),
        }
        for e in latest if e.get("companies")
    ]

    all_urls = static_urls + company_urls + earnings_urls
    xml = render_template("sitemap.xml", urls=all_urls)
    return app.response_class(xml, mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    txt = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    return app.response_class(txt, mimetype="text/plain")


# ── Error handlers ─────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", page_title=f"Page Not Found — {SITE_NAME}"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("404.html", page_title=f"Server Error — {SITE_NAME}"), 500


# ── Startup ────────────────────────────────────────────────

@app.before_request
def _start_scheduler_once():
    """Start background scheduler on first request."""
    if not hasattr(app, "_scheduler_started"):
        start_scheduler()
        app._scheduler_started = True


if __name__ == "__main__":
    app.run(debug=True, port=8080, use_reloader=False)
