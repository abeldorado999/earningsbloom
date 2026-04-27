"""
All Gemini prompt templates for the two-stage AI pipeline.
"""

# ── Stage 1: Number Extraction (Gemini 2.0 Flash — cheap) ─
STAGE1_PROMPT = """
You are a financial data extraction bot. Extract ONLY the key financial numbers
from the text below. Return ONLY valid JSON, no other text.

Return this exact structure:
{{
  "revenue_actual": "string like $94.9B or $12.3M or null if not found",
  "revenue_expected": "analyst consensus estimate or null",
  "revenue_beat": true or false or null,
  "eps_actual": "EPS value like $1.53 or null",
  "eps_expected": "EPS estimate or null",
  "eps_beat": true or false or null,
  "net_income": "net income figure or null",
  "gross_margin": "gross margin percentage or null",
  "yoy_growth": "year-over-year revenue growth percentage or null"
}}

TEXT:
{text}
"""

# ── Stage 2: Full Summary (Gemini 2.5 Flash — smart) ──────
STAGE2_PROMPT = """
You are a senior financial analyst at a top investment bank with 20 years of experience.
Analyze this earnings call transcript and return a structured JSON summary.
Return ONLY valid JSON. No markdown, no explanation, no code blocks.

Financial data already extracted (use these exact numbers):
{financial_data}

Return this exact JSON structure:
{{
  "tldr": "Exactly 2 sentences summarizing what happened this quarter and why it matters.",
  "wins": [
    "First specific positive highlight with supporting data if available",
    "Second specific positive highlight",
    "Third specific positive highlight"
  ],
  "concerns": [
    "First specific concern or risk raised on the call",
    "Second concern",
    "Third concern"
  ],
  "ceo_guidance": "2-3 sentences on exactly what management said about the next quarter or fiscal year outlook.",
  "key_quote": "The single most impactful or surprising direct quote from an executive. Include the speaker name.",
  "sentiment": "bullish or neutral or bearish",
  "sentiment_reason": "One sentence explaining why you chose this sentiment.",
  "topics": ["topic1", "topic2", "topic3"]
}}

TRANSCRIPT:
{transcript}
"""

# ── Regex fallback patterns for Stage 1 ───────────────────
REVENUE_PATTERNS = [
    r"revenue\s+(?:of|was|were|totaled?)?\s*\$?([\d,\.]+)\s*(billion|million|B|M)\b",
    r"\$?([\d,\.]+)\s*(billion|million|B|M)\s+in\s+(?:total\s+)?revenue",
    r"(?:total\s+)?(?:net\s+)?revenue[s]?\s*[:\-]?\s*\$?([\d,\.]+)\s*(billion|million|B|M)",
]

EPS_PATTERNS = [
    r"(?:earnings|eps)\s+per\s+(?:diluted\s+)?share\s+(?:of|was|were)?\s*\$?([\d\.]+)",
    r"\$?([\d\.]+)\s+(?:diluted\s+)?(?:earnings\s+per\s+share|eps)\b",
    r"(?:diluted\s+)?eps[:\s]+\$?([\d\.]+)",
]

BEAT_PATTERNS = [
    r"(?:exceeded|beat|surpassed|topped|came\s+in\s+above)\s+(?:analyst\s+)?(?:estimate|expectation|consensus|forecast)",
    r"above\s+(?:the\s+)?(?:analyst\s+)?(?:estimate|expectation|consensus)",
]

MISS_PATTERNS = [
    r"(?:missed|fell\s+short\s+of|below)\s+(?:analyst\s+)?(?:estimate|expectation|consensus|forecast)",
    r"below\s+(?:the\s+)?(?:analyst\s+)?(?:estimate|expectation|consensus)",
]
