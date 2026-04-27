"""
Orchestrator — ties scraping + pipeline + DB together.
Called by the scheduler and by manual scripts.
"""
import logging
import uuid
from datetime import date
from scraper.sec_edgar import (
    get_recent_filings, get_filing_documents,
    find_transcript_document, extract_text_from_url,
    clean_transcript, chunk_transcript, detect_quarter,
)
from pipeline.gemini import process_transcript
from models.db import (
    get_all_companies, get_company_by_ticker,
    upsert_earnings_call, upsert_summary, update_earnings_status,
)

logger = logging.getLogger(__name__)


def process_company(company: dict, days_back: int = 7) -> list:
    """
    Check for new earnings call filings for a single company.
    Scrape, process through AI, and save to DB.
    Returns list of quarters successfully processed.
    """
    cik  = company.get("cik")
    name = company.get("name")

    if not cik:
        logger.warning(f"No CIK for {name}, skipping.")
        return []

    logger.info(f"Checking filings for {name} (CIK: {cik})")
    filings = get_recent_filings(cik, form_type="8-K", days_back=days_back)

    if not filings:
        logger.info(f"No recent filings for {name}.")
        return []

    processed = []

    for filing in filings:
        try:
            # Get all documents in this filing
            docs = get_filing_documents(cik, filing["accession"])
            transcript_doc = find_transcript_document(docs)

            if not transcript_doc:
                logger.warning(f"No transcript doc found for {name} filing {filing['accession']}")
                continue

            # Download and extract text
            raw_text = extract_text_from_url(transcript_doc["url"])
            if not raw_text or len(raw_text) < 1000:
                logger.warning(f"Transcript too short for {name}, skipping.")
                continue

            # Clean and chunk
            clean_text = clean_transcript(raw_text)
            sections   = chunk_transcript(clean_text)
            quarter    = detect_quarter(clean_text, filing["filing_date"])

            # Save earnings call record (status=pending)
            earnings_id = str(uuid.uuid4())
            earnings_record = {
                "id":             earnings_id,
                "company_id":     company["id"],
                "quarter":        quarter,
                "fiscal_year":    int(quarter.split("-")[1]),
                "call_date":      filing["filing_date"],
                "transcript_url": transcript_doc["url"],
                "raw_text":       clean_text[:50000],  # Store first 50k chars
                "status":         "pending",
            }
            saved = upsert_earnings_call(earnings_record)
            if saved:
                earnings_id = saved.get("id", earnings_id)

            # Run AI pipeline
            logger.info(f"Running AI pipeline for {name} {quarter}...")
            result = process_transcript(
                transcript_text=clean_text,
                financial_section=sections.get("financial_results"),
            )

            # Save summary
            summary_record = {
                "earnings_call_id": earnings_id,
                "language":         "en",
                "tldr":             result.get("tldr", ""),
                "revenue_actual":   result.get("revenue_actual"),
                "revenue_expected": result.get("revenue_expected"),
                "revenue_beat":     result.get("revenue_beat"),
                "eps_actual":       result.get("eps_actual"),
                "eps_expected":     result.get("eps_expected"),
                "eps_beat":         result.get("eps_beat"),
                "wins":             result.get("wins", []),
                "concerns":         result.get("concerns", []),
                "ceo_guidance":     result.get("ceo_guidance", ""),
                "key_quote":        result.get("key_quote", ""),
                "sentiment":        result.get("sentiment", "neutral"),
                "sentiment_reason": result.get("sentiment_reason", ""),
                "generated_at":     date.today().isoformat(),
            }
            upsert_summary(summary_record)

            # Mark earnings as processed
            update_earnings_status(earnings_id, "processed")
            processed.append(quarter)
            logger.info(f"✅ {name} {quarter} processed successfully.")

        except Exception as e:
            logger.error(f"❌ Failed to process {name}: {e}")
            if 'earnings_id' in locals():
                update_earnings_status(earnings_id, "failed")

    return processed


def run_all_companies(days_back: int = 7):
    """Run the scraper for all active companies in the DB."""
    companies = get_all_companies()
    logger.info(f"Running scraper for {len(companies)} companies...")
    total_processed = 0
    for company in companies:
        quarters = process_company(company, days_back=days_back)
        total_processed += len(quarters)
    logger.info(f"Done. {total_processed} earnings calls processed.")
    return total_processed
