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
You are a senior financial analyst writing for a public website read by both expert investors
and everyday beginners. Your job is to produce a comprehensive, informative, well-written
earnings call summary that is AT LEAST 700 words of actual content.

Financial data already extracted (use these exact numbers):
{financial_data}

Return ONLY valid JSON. No markdown, no explanation, no code blocks.

Return this exact JSON structure:
{{
  "tldr": "Exactly 2 sentences summarizing what happened this quarter and why it matters to investors.",

  "what_this_means": "Write 5-7 clear sentences explaining these results in simple, plain English for a beginner investor who has never read an earnings report. Avoid jargon. Explain what the numbers mean in real life terms — e.g. 'Apple made more money this quarter than any quarter before, mostly because more people bought iPhones than the company expected.'",

  "key_takeaways": [
    "Specific insight #1 with a data point if available",
    "Specific insight #2 with a data point if available",
    "Specific insight #3 with a data point if available",
    "Specific insight #4 with a data point if available",
    "Specific insight #5 with a data point if available"
  ],

  "wins": [
    "First specific positive highlight with supporting data",
    "Second specific positive highlight",
    "Third specific positive highlight"
  ],

  "concerns": [
    "First specific concern or risk raised on the call",
    "Second concern",
    "Third concern"
  ],

  "investor_perspective": {{
    "bullish_case": "2-3 sentences on why an optimistic investor would be encouraged by these results.",
    "bearish_case": "2-3 sentences on what concerns a cautious or skeptical investor might have."
  }},

  "ceo_guidance": "2-3 sentences on exactly what management said about the next quarter or fiscal year outlook.",

  "key_quote": "The single most impactful or surprising direct quote from an executive. Include the speaker name at the end, e.g. '— Tim Cook, CEO'",

  "sentiment": "bullish or neutral or bearish",
  "sentiment_reason": "One sentence explaining why you chose this sentiment.",

  "topics": ["topic1", "topic2", "topic3", "topic4"]
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
