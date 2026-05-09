"""
SEC EDGAR scraper — finds new earnings call transcripts for US companies.
Uses the public SEC EDGAR full-text search API (no auth required).
"""
import re
import time
import logging
import requests
import fitz  # PyMuPDF
from datetime import date, timedelta
from bs4 import BeautifulSoup
from config import SEC_EDGAR_USER_AGENT, SEC_SUBMISSIONS_URL, SEC_FILING_URL

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": SEC_EDGAR_USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov",
}
SEARCH_HEADERS = {
    "User-Agent": SEC_EDGAR_USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
}


# ── Public API: Latest filings for a company ───────────────

def get_recent_filings(cik: str, form_type: str = "8-K", days_back: int = 7) -> list:
    """
    Fetch recent earnings-related 8-K filings (Item 2.02 only) from SEC EDGAR.
    Item 2.02 = 'Results of Operations and Financial Condition' = earnings press release.
    """
    cik_padded = cik.zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch submissions for CIK {cik}: {e}")
        return []

    filings = data.get("filings", {}).get("recent", {})
    forms       = filings.get("form", [])
    dates       = filings.get("filingDate", [])
    accessions  = filings.get("accessionNumber", [])
    documents   = filings.get("primaryDocument", [])
    items_list  = filings.get("items", [])   # e.g. "2.02" or "2.02,9.01"

    cutoff = date.today() - timedelta(days=days_back)
    results = []

    for i, form in enumerate(forms):
        if form != form_type:
            continue
        filing_date = date.fromisoformat(dates[i])
        if filing_date < cutoff:
            continue
        # Only pick filings that include Item 2.02 (Results of Operations)
        items_str = str(items_list[i]) if i < len(items_list) else ""
        if "2.02" not in items_str:
            logger.debug(f"Skipping non-earnings 8-K filed {dates[i]} (items: {items_str})")
            continue
        results.append({
            "accession": accessions[i].replace("-", ""),
            "filing_date": dates[i],
            "primary_doc": documents[i],
            "cik": cik,
        })

    return results


def get_filing_documents(cik: str, accession: str) -> list:
    """
    Fetch the full list of documents in a filing from the EDGAR index.
    Returns list of (filename, description, url).
    """
    cik_padded = cik.zfill(10)
    acc_formatted = f"{accession[:10]}-{accession[10:12]}-{accession[12:]}"
    index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{acc_formatted}-index.htm"

    try:
        resp = requests.get(index_url, headers=SEARCH_HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        rows = soup.select("table.tableFile tr")
        docs = []
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) >= 3:
                description = cols[1].get_text(strip=True)
                link_tag = cols[2].find("a")
                if link_tag:
                    href = link_tag["href"]
                    full_url = f"https://www.sec.gov{href}"
                    docs.append({
                        "description": description,
                        "url": full_url,
                        "filename": href.split("/")[-1],
                    })
        return docs
    except Exception as e:
        logger.error(f"Failed to fetch filing documents for {accession}: {e}")
        return []


# ── Transcript Extraction ──────────────────────────────────

def find_transcript_document(documents: list) -> dict | None:
    """
    From a list of filing documents, pick the one most likely to be the
    earnings call transcript (ex-99.1 or similar exhibit).
    """
    TRANSCRIPT_KEYWORDS = ["transcript", "call", "conference"]
    for doc in documents:
        desc = doc.get("description", "").lower()
        fname = doc.get("filename", "").lower()
        if any(kw in desc or kw in fname for kw in TRANSCRIPT_KEYWORDS):
            return doc
    # Fallback: first exhibit document
    for doc in documents:
        if "ex" in doc.get("filename", "").lower():
            return doc
    return documents[0] if documents else None


def extract_text_from_url(url: str) -> str:
    """
    Download a document (HTML or PDF) and extract clean plain text.
    """
    try:
        resp = requests.get(url, headers=SEARCH_HEADERS, timeout=30)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")

        if "pdf" in content_type or url.endswith(".pdf"):
            return _extract_pdf_text(resp.content)
        else:
            return _extract_html_text(resp.text)

    except Exception as e:
        logger.error(f"Failed to extract text from {url}: {e}")
        return ""


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = [page.get_text() for page in doc]
        return "\n".join(pages)
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""


def _extract_html_text(html: str) -> str:
    """Extract clean text from HTML, stripping tags."""
    soup = BeautifulSoup(html, "lxml")
    # Remove scripts and styles
    for tag in soup(["script", "style", "head", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


# ── Text Cleaning ──────────────────────────────────────────

def clean_transcript(raw_text: str) -> str:
    """
    Remove boilerplate legal headers, page numbers, and normalize whitespace
    to produce clean transcript text ready for AI processing.
    """
    # Remove common SEC boilerplate lines
    boilerplate_patterns = [
        r"UNITED STATES SECURITIES AND EXCHANGE COMMISSION.*?FORM 8-K",
        r"Safe Harbor Statement.*?forward-looking statements",
        r"This transcript.*?purposes only",
        r"^\s*Page \d+\s*$",
        r"^\s*\d+\s*$",       # Standalone page numbers
        r"={3,}",              # Separator lines
        r"-{3,}",
    ]
    text = raw_text
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)

    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def chunk_transcript(text: str) -> dict:
    """
    Split transcript into logical sections for staged AI processing.
    Returns dict with keys: financial_results, guidance, qa
    """
    sections = {"financial_results": "", "guidance": "", "qa": "", "full": text}

    SECTION_PATTERNS = {
        "financial_results": r"(financial results?|revenue|financial highlights?)",
        "guidance":          r"(guidance|outlook|next quarter|fiscal year)",
        "qa":                r"(question.and.answer|q&a|q\s*\&\s*a|questions from)",
    }

    lines = text.split("\n")
    current_section = "full"
    section_text = {k: [] for k in SECTION_PATTERNS}

    for line in lines:
        for section, pattern in SECTION_PATTERNS.items():
            if re.search(pattern, line, re.IGNORECASE) and len(line) < 100:
                current_section = section
                break
        if current_section in section_text:
            section_text[current_section].append(line)

    for section, lines_list in section_text.items():
        sections[section] = "\n".join(lines_list)

    return sections


# ── Quarter Detection ──────────────────────────────────────

def detect_quarter(text: str, filing_date: str) -> str:
    """
    Try to detect which fiscal quarter this transcript covers.
    Falls back to calculating from the filing date.
    """
    patterns = [
        r"(first|second|third|fourth|1st|2nd|3rd|4th)\s+quarter",
        r"Q([1-4])\s+(?:fiscal\s+)?(\d{4})",
        r"(Q[1-4])[- ](\d{4})",
    ]
    for pat in patterns:
        m = re.search(pat, text[:3000], re.IGNORECASE)
        if m:
            groups = m.groups()
            if len(groups) == 1:
                # "first quarter" style
                mapping = {
                    "first": "Q1", "second": "Q2", "third": "Q3", "fourth": "Q4",
                    "1st": "Q1", "2nd": "Q2", "3rd": "Q3", "4th": "Q4",
                }
                q = mapping.get(groups[0].lower(), "Q1")
                year = filing_date[:4]
                return f"{q}-{year}"
            elif len(groups) == 2:
                return f"Q{groups[0]}-{groups[1]}" if groups[0].isdigit() else f"{groups[0]}-{groups[1]}"

    # Fallback: estimate from filing month
    month = int(filing_date[5:7])
    year  = filing_date[:4]
    quarter_map = {(1,2,3): "Q1", (4,5,6): "Q2", (7,8,9): "Q3", (10,11,12): "Q4"}
    for months, q in quarter_map.items():
        if month in months:
            return f"{q}-{year}"
    return f"Q1-{year}"
