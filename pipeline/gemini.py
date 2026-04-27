"""
Two-stage Gemini pipeline:
  Stage 1 (Gemini 2.0 Flash)  — cheap number extraction via regex + AI fallback
  Stage 2 (Gemini 2.5 Flash)  — smart insight & narrative generation
"""
import re
import json
import logging
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_STAGE1_MODEL, GEMINI_STAGE2_MODEL, MAX_GEMINI_CALLS_PER_DAY
from pipeline.prompts import (
    STAGE1_PROMPT, STAGE2_PROMPT,
    REVENUE_PATTERNS, EPS_PATTERNS, BEAT_PATTERNS, MISS_PATTERNS,
)
from models.db import get_gemini_calls_today, increment_gemini_calls

logger = logging.getLogger(__name__)

# Initialise Gemini client once
_client = genai.Client(api_key=GEMINI_API_KEY)


# ── Rate limit guard ───────────────────────────────────────

def _can_call_gemini() -> bool:
    return get_gemini_calls_today() < MAX_GEMINI_CALLS_PER_DAY


def _call_gemini(model: str, prompt: str) -> str:
    """Call Gemini and return raw text response. Tracks daily usage."""
    if not _can_call_gemini():
        raise RuntimeError("Daily Gemini call limit reached. Will retry tomorrow.")

    response = _client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,         # Low temp = consistent, factual output
            response_mime_type="application/json",
        ),
    )
    increment_gemini_calls()
    return response.text


# ── Stage 0: Regex-based number extraction (free) ─────────

def _extract_with_regex(text: str) -> dict:
    """Try to extract financial numbers using regex patterns. Cost: $0."""
    result = {
        "revenue_actual": None, "revenue_expected": None, "revenue_beat": None,
        "eps_actual": None, "eps_expected": None, "eps_beat": None,
        "net_income": None, "gross_margin": None, "yoy_growth": None,
    }

    # Revenue
    for pattern in REVENUE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            amount = m.group(1).replace(",", "")
            unit   = m.group(2)
            result["revenue_actual"] = f"${amount}{unit[0].upper()}"
            break

    # EPS
    for pattern in EPS_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            result["eps_actual"] = f"${m.group(1)}"
            break

    # Beat/Miss
    beat_found = any(re.search(p, text, re.IGNORECASE) for p in BEAT_PATTERNS)
    miss_found = any(re.search(p, text, re.IGNORECASE) for p in MISS_PATTERNS)
    if beat_found and not miss_found:
        result["revenue_beat"] = True
    elif miss_found and not beat_found:
        result["revenue_beat"] = False

    return result


def _regex_is_sufficient(data: dict) -> bool:
    """Return True if regex got enough data to skip Stage 1 AI call."""
    return data.get("revenue_actual") is not None and data.get("eps_actual") is not None


# ── Stage 1: Financial number extraction ──────────────────

def stage1_extract_numbers(financial_text: str) -> dict:
    """
    First try regex (free). Only call Gemini if regex fails.
    """
    regex_result = _extract_with_regex(financial_text)

    if _regex_is_sufficient(regex_result):
        logger.info("Stage 1: Regex extraction sufficient — no AI call needed.")
        return regex_result

    logger.info("Stage 1: Regex insufficient — calling Gemini 2.0 Flash.")
    try:
        # Truncate to first 15k chars (financial section is usually early in transcript)
        truncated = financial_text[:15000]
        prompt    = STAGE1_PROMPT.format(text=truncated)
        raw       = _call_gemini(GEMINI_STAGE1_MODEL, prompt)
        parsed    = json.loads(raw)
        # Merge: regex values take precedence over AI (regex is more reliable for numbers)
        for k, v in regex_result.items():
            if v is not None:
                parsed[k] = v
        return parsed
    except Exception as e:
        logger.error(f"Stage 1 AI extraction failed: {e}")
        return regex_result   # Fall back to whatever regex got


# ── Stage 2: Insight & narrative generation ───────────────

def stage2_generate_summary(transcript: str, financial_data: dict) -> dict:
    """
    Use Gemini 2.5 Flash (thinking) to generate the full human-readable summary.
    This is the high-quality output users see on the page.
    """
    # Truncate transcript to 80k chars to stay within token budget
    truncated  = transcript[:80000]
    fin_json   = json.dumps(financial_data, indent=2)
    prompt     = STAGE2_PROMPT.format(financial_data=fin_json, transcript=truncated)

    logger.info("Stage 2: Calling Gemini 2.5 Flash for insights...")
    try:
        raw    = _call_gemini(GEMINI_STAGE2_MODEL, prompt)
        parsed = json.loads(raw)
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"Stage 2 JSON parse error: {e}\nRaw: {raw[:500]}")
        raise
    except Exception as e:
        logger.error(f"Stage 2 Gemini call failed: {e}")
        raise


# ── Master pipeline ───────────────────────────────────────

def process_transcript(transcript_text: str, financial_section: str = None) -> dict:
    """
    Full two-stage pipeline. Returns merged summary dict ready for DB storage.
    """
    # Use full text if no dedicated financial section found
    fin_text = financial_section or transcript_text

    # Stage 1: Numbers (free via regex, AI only if needed)
    financial_data = stage1_extract_numbers(fin_text)
    logger.info(f"Stage 1 complete: {financial_data}")

    # Stage 2: Insights (always AI — this is the core value)
    summary = stage2_generate_summary(transcript_text, financial_data)
    logger.info("Stage 2 complete.")

    # Merge all data into one dict
    return {**financial_data, **summary}
