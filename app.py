"""
EarningsBloom — Main Flask Application
AI-powered earnings call summarizer
"""
import logging
import math
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, abort, redirect, url_for
from models.db import (
    get_all_companies, get_company_by_slug,
    get_earnings_by_company, get_earnings_detail, get_latest_earnings,
    get_prev_quarter_summary,
)
from blog_posts import BLOG_POSTS
from config import SITE_NAME, SITE_URL, SITE_TAGLINE, ADSENSE_PUBLISHER_ID, GA_MEASUREMENT_ID
import os

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
@app.context_processor
def inject_globals():
    return dict(
        site_name=SITE_NAME,
        site_url=SITE_URL,
        site_tagline=SITE_TAGLINE,
        adsense_id=ADSENSE_PUBLISHER_ID,
        ga_id=GA_MEASUREMENT_ID,
        current_year=datetime.now().year,
    )


# ── Canonical redirect (www → non-www, http → https) ──────
@app.before_request
def canonical_redirect():
    """Force https:// and strip www. for SEO canonical URLs."""
    host = request.host  # e.g. www.earningsbloom.com or earningsbloom.com
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)

    needs_www_strip  = host.startswith("www.")
    needs_https      = (scheme == "http")

    if needs_www_strip or needs_https:
        new_host = host[4:] if needs_www_strip else host
        url = f"https://{new_host}{request.full_path.rstrip('?')}"
        return redirect(url, code=301)


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

    # Fetch previous quarter for QoQ comparison
    company_id   = detail.get("company_id") or (company.get("id") if isinstance(company, dict) else None)
    current_date = detail.get("call_date", "")
    prev_summary = None
    if company_id and current_date:
        try:
            prev_summary = get_prev_quarter_summary(company_id, current_date)
        except Exception:
            pass

    return render_template("earnings_detail.html",
        company=company,
        earnings=detail,
        summary=summary,
        prev_summary=prev_summary,
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


@app.route("/privacy")
def privacy():
    return render_template("privacy.html",
        page_title=f"Privacy Policy — {SITE_NAME}",
        meta_description="EarningsBloom Privacy Policy — how we collect, use and protect your data.",
    )


@app.route("/terms")
def terms():
    return render_template("terms.html",
        page_title=f"Terms & Conditions — {SITE_NAME}",
        meta_description="EarningsBloom Terms & Conditions — rules governing use of the site and its AI-generated content.",
    )


@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html",
        page_title=f"Financial Disclaimer — {SITE_NAME}",
        meta_description="EarningsBloom Financial Disclaimer — AI summaries are not financial advice. Always verify with official SEC filings.",
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # In production, send email via SendGrid/Mailgun.
        # For now, just log it and show success.
        name    = request.form.get("name", "")
        email   = request.form.get("email", "")
        subject = request.form.get("subject", "")
        message = request.form.get("message", "")
        logger.info(f"Contact form: from={email} name={name} subject={subject} msg={message[:80]}")
        return render_template("contact.html",
            sent=True,
            page_title=f"Contact — {SITE_NAME}",
            meta_description="Contact EarningsBloom — report errors, ask questions, or request features.",
        )
    return render_template("contact.html",
        sent=False,
        page_title=f"Contact — {SITE_NAME}",
        meta_description="Contact EarningsBloom — report errors, ask questions, or request features.",
    )


@app.route("/blog")
def blog_index():
    return render_template("blog_index.html",
        posts=BLOG_POSTS,
        page_title=f"Investor Education & Guides — {SITE_NAME}",
        meta_description="Free beginner guides on earnings reports, EPS, revenue, and investing concepts. Plain English, no jargon.",
    )


@app.route("/blog/<slug>")
def blog_post(slug: str):
    post = next((p for p in BLOG_POSTS if p["slug"] == slug), None)
    if not post:
        abort(404)
    related = [p for p in BLOG_POSTS if p["slug"] in post.get("related_slugs", [])]
    return render_template("blog_post.html",
        post=post,
        related=related,
        page_title=f"{post['title']} — {SITE_NAME}",
        meta_description=post["meta_description"],
    )


# ── Sitemap ─────────────────────────────────────────────

@app.route("/sitemap.xml")
def sitemap():
    companies = get_all_companies()
    latest    = get_latest_earnings(limit=500)

    today = date.today().isoformat()
    static_urls = [
        {"loc": SITE_URL + "/",           "priority": "1.0", "changefreq": "daily",   "lastmod": today},
        {"loc": SITE_URL + "/companies",  "priority": "0.8", "changefreq": "weekly",  "lastmod": today},
        {"loc": SITE_URL + "/about",      "priority": "0.6", "changefreq": "monthly"},
        {"loc": SITE_URL + "/contact",    "priority": "0.5", "changefreq": "monthly"},
        {"loc": SITE_URL + "/blog",       "priority": "0.7", "changefreq": "weekly",  "lastmod": today},
        {"loc": SITE_URL + "/privacy",    "priority": "0.3", "changefreq": "yearly"},
        {"loc": SITE_URL + "/terms",      "priority": "0.3", "changefreq": "yearly"},
        {"loc": SITE_URL + "/disclaimer", "priority": "0.3", "changefreq": "yearly"},
    ]
    blog_urls = [
        {"loc": f"{SITE_URL}/blog/{p['slug']}", "priority": "0.7", "changefreq": "monthly",
         "lastmod": p["published"]}
        for p in BLOG_POSTS
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
            "lastmod": str(e.get("call_date", today))[:10],
        }
        for e in latest if e.get("companies")
    ]

    all_urls = static_urls + blog_urls + company_urls + earnings_urls
    xml = render_template("sitemap.xml", urls=all_urls)
    return app.response_class(xml, mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    txt = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    return app.response_class(txt, mimetype="text/plain")


# ── Pipeline Trigger (called by GCP Cloud Scheduler) ──────

PIPELINE_SECRET = os.environ.get("PIPELINE_SECRET", "")

@app.route("/api/run-pipeline", methods=["POST"])
def run_pipeline():
    """
    Secure endpoint triggered by GCP Cloud Scheduler during earnings season.
    Requires Bearer token matching PIPELINE_SECRET env var.
    """
    auth = request.headers.get("Authorization", "")
    if not PIPELINE_SECRET or auth != f"Bearer {PIPELINE_SECRET}":
        logger.warning("Unauthorised pipeline trigger attempt.")
        return jsonify({"error": "Unauthorised"}), 401

    # Run in background so the HTTP request returns immediately
    import threading
    from scraper.orchestrator import run_all_companies

    def _run():
        logger.info("Pipeline triggered by Cloud Scheduler.")
        try:
            run_all_companies(days_back=3)
            logger.info("Pipeline run complete.")
        except Exception as e:
            logger.error(f"Pipeline run failed: {e}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return jsonify({"status": "Pipeline started"}), 202


# ── Error handlers ─────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", page_title=f"Page Not Found — {SITE_NAME}"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("404.html", page_title=f"Server Error — {SITE_NAME}"), 500


if __name__ == "__main__":
    app.run(debug=True, port=8080, use_reloader=False)
