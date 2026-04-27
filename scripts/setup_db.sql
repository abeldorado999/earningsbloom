-- ============================================================
-- EarningsBloom — Supabase Database Setup
-- Run this SQL in your Supabase project's SQL Editor
-- ============================================================

-- ── Companies ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS companies (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        VARCHAR(255)  NOT NULL,
  ticker      VARCHAR(20)   NOT NULL,
  exchange    VARCHAR(20)   NOT NULL DEFAULT 'NASDAQ',
  sector      VARCHAR(100),
  cik         VARCHAR(20),
  slug        VARCHAR(255)  NOT NULL UNIQUE,
  logo_url    VARCHAR(500),
  is_active   BOOLEAN       NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_companies_slug   ON companies(slug);
CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies(ticker);

-- ── Earnings Calls ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS earnings_calls (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
  quarter         VARCHAR(15)  NOT NULL,
  fiscal_year     INTEGER,
  call_date       DATE,
  transcript_url  VARCHAR(500),
  raw_text        TEXT,
  status          VARCHAR(20)  NOT NULL DEFAULT 'pending',
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  UNIQUE(company_id, quarter)
);
CREATE INDEX IF NOT EXISTS idx_earnings_company  ON earnings_calls(company_id);
CREATE INDEX IF NOT EXISTS idx_earnings_date     ON earnings_calls(call_date DESC);
CREATE INDEX IF NOT EXISTS idx_earnings_status   ON earnings_calls(status);

-- ── Summaries ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS summaries (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  earnings_call_id    UUID REFERENCES earnings_calls(id) ON DELETE CASCADE,
  language            VARCHAR(10)  NOT NULL DEFAULT 'en',
  tldr                TEXT,
  revenue_actual      VARCHAR(50),
  revenue_expected    VARCHAR(50),
  revenue_beat        BOOLEAN,
  eps_actual          VARCHAR(50),
  eps_expected        VARCHAR(50),
  eps_beat            BOOLEAN,
  net_income          VARCHAR(50),
  gross_margin        VARCHAR(50),
  yoy_growth          VARCHAR(50),
  wins                JSONB        NOT NULL DEFAULT '[]',
  concerns            JSONB        NOT NULL DEFAULT '[]',
  ceo_guidance        TEXT,
  key_quote           TEXT,
  sentiment           VARCHAR(20),
  sentiment_reason    TEXT,
  topics              JSONB        NOT NULL DEFAULT '[]',
  generated_at        DATE         NOT NULL DEFAULT CURRENT_DATE,
  UNIQUE(earnings_call_id, language)
);
CREATE INDEX IF NOT EXISTS idx_summaries_earnings ON summaries(earnings_call_id);

-- ── API Usage Tracking (rate limiting) ──────────────────
CREATE TABLE IF NOT EXISTS api_usage (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date        DATE NOT NULL UNIQUE,
  call_count  INTEGER NOT NULL DEFAULT 0
);

-- ── Enable Row Level Security (recommended for Supabase) ─
ALTER TABLE companies     ENABLE ROW LEVEL SECURITY;
ALTER TABLE earnings_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE summaries      ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage      ENABLE ROW LEVEL SECURITY;

-- Allow public read access (needed for the website to work)
CREATE POLICY "Allow public read companies"
  ON companies FOR SELECT TO anon USING (true);

CREATE POLICY "Allow public read earnings"
  ON earnings_calls FOR SELECT TO anon USING (true);

CREATE POLICY "Allow public read summaries"
  ON summaries FOR SELECT TO anon USING (true);

-- Allow service role full access (for the scraper/pipeline)
CREATE POLICY "Service role full access companies"
  ON companies FOR ALL TO service_role USING (true);

CREATE POLICY "Service role full access earnings"
  ON earnings_calls FOR ALL TO service_role USING (true);

CREATE POLICY "Service role full access summaries"
  ON summaries FOR ALL TO service_role USING (true);

CREATE POLICY "Service role full access api_usage"
  ON api_usage FOR ALL TO service_role USING (true);
