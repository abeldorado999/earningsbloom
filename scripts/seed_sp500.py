"""
Expanded company seeder — adds 150+ more S&P 500 companies to DB.
Automatically fetches CIK numbers from SEC EDGAR's official API.
Run: python scripts/seed_sp500.py
"""
import sys, os, uuid, time, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY  = os.getenv("SUPABASE_SERVICE_KEY")

# ── Target companies: (name, ticker, exchange, sector, slug) ────────────────
# CIK is fetched automatically from SEC EDGAR — no hardcoding needed.
# Only include SEC-registered (publicly listed US) companies.
NEW_COMPANIES = [
    # ── Technology ──────────────────────────────────────────────────────────
    ("Oracle Corporation",          "ORCL",  "NYSE",   "Technology",      "oracle"),
    ("Cisco Systems Inc.",          "CSCO",  "NASDAQ", "Technology",      "cisco"),
    ("IBM Corporation",             "IBM",   "NYSE",   "Technology",      "ibm"),
    ("Texas Instruments Inc.",      "TXN",   "NASDAQ", "Technology",      "texas-instruments"),
    ("Accenture PLC",               "ACN",   "NYSE",   "Technology",      "accenture"),
    ("Applied Materials Inc.",      "AMAT",  "NASDAQ", "Technology",      "applied-materials"),
    ("Lam Research Corporation",    "LRCX",  "NASDAQ", "Technology",      "lam-research"),
    ("KLA Corporation",             "KLAC",  "NASDAQ", "Technology",      "kla"),
    ("Micron Technology Inc.",      "MU",    "NASDAQ", "Technology",      "micron"),
    ("Marvell Technology Inc.",     "MRVL",  "NASDAQ", "Technology",      "marvell"),
    ("Fortinet Inc.",               "FTNT",  "NASDAQ", "Technology",      "fortinet"),
    ("Palo Alto Networks",          "PANW",  "NASDAQ", "Technology",      "palo-alto-networks"),
    ("CrowdStrike Holdings",        "CRWD",  "NASDAQ", "Technology",      "crowdstrike"),
    ("Datadog Inc.",                "DDOG",  "NASDAQ", "Technology",      "datadog"),
    ("MongoDB Inc.",                "MDB",   "NASDAQ", "Technology",      "mongodb"),
    ("Zscaler Inc.",                "ZS",    "NASDAQ", "Technology",      "zscaler"),
    ("Okta Inc.",                   "OKTA",  "NASDAQ", "Technology",      "okta"),
    ("Splunk Inc.",                 "SPLK",  "NASDAQ", "Technology",      "splunk"),
    ("Autodesk Inc.",               "ADSK",  "NASDAQ", "Technology",      "autodesk"),
    ("Intuit Inc.",                 "INTU",  "NASDAQ", "Technology",      "intuit"),
    ("Dell Technologies Inc.",      "DELL",  "NYSE",   "Technology",      "dell"),
    ("HP Inc.",                     "HPQ",   "NYSE",   "Technology",      "hp"),
    ("Hewlett Packard Enterprise",  "HPE",   "NYSE",   "Technology",      "hpe"),
    ("Roper Technologies",          "ROP",   "NASDAQ", "Technology",      "roper-technologies"),
    ("ANSYS Inc.",                  "ANSS",  "NASDAQ", "Technology",      "ansys"),
    ("PTC Inc.",                    "PTC",   "NASDAQ", "Technology",      "ptc"),
    ("Veeva Systems",               "VEEV",  "NYSE",   "Technology",      "veeva"),
    ("Tyler Technologies",          "TYL",   "NYSE",   "Technology",      "tyler-technologies"),
    ("Fair Isaac Corporation",      "FICO",  "NYSE",   "Technology",      "fico"),
    ("VeriSign Inc.",               "VRSN",  "NASDAQ", "Technology",      "verisign"),
    # ── Finance & Banking ────────────────────────────────────────────────────
    ("Wells Fargo & Co.",           "WFC",   "NYSE",   "Finance",         "wells-fargo"),
    ("Morgan Stanley",              "MS",    "NYSE",   "Finance",         "morgan-stanley"),
    ("Citigroup Inc.",              "C",     "NYSE",   "Finance",         "citigroup"),
    ("American Express Co.",        "AXP",   "NYSE",   "Finance",         "american-express"),
    ("BlackRock Inc.",              "BLK",   "NYSE",   "Finance",         "blackrock"),
    ("Charles Schwab Corp.",        "SCHW",  "NYSE",   "Finance",         "charles-schwab"),
    ("S&P Global Inc.",             "SPGI",  "NYSE",   "Finance",         "sp-global"),
    ("CME Group Inc.",              "CME",   "NASDAQ", "Finance",         "cme-group"),
    ("Intercontinental Exchange",   "ICE",   "NYSE",   "Finance",         "intercontinental-exchange"),
    ("Moody's Corporation",         "MCO",   "NYSE",   "Finance",         "moodys"),
    ("Coinbase Global Inc.",        "COIN",  "NASDAQ", "Finance",         "coinbase"),
    ("Robinhood Markets",           "HOOD",  "NASDAQ", "Finance",         "robinhood"),
    # ── Healthcare & Pharma ──────────────────────────────────────────────────
    ("AbbVie Inc.",                 "ABBV",  "NYSE",   "Healthcare",      "abbvie"),
    ("Merck & Co. Inc.",            "MRK",   "NYSE",   "Healthcare",      "merck"),
    ("Bristol-Myers Squibb",        "BMY",   "NYSE",   "Healthcare",      "bristol-myers-squibb"),
    ("Amgen Inc.",                  "AMGN",  "NASDAQ", "Healthcare",      "amgen"),
    ("Gilead Sciences",             "GILD",  "NASDAQ", "Healthcare",      "gilead"),
    ("Regeneron Pharmaceuticals",   "REGN",  "NASDAQ", "Healthcare",      "regeneron"),
    ("Vertex Pharmaceuticals",      "VRTX",  "NASDAQ", "Healthcare",      "vertex"),
    ("Biogen Inc.",                 "BIIB",  "NASDAQ", "Healthcare",      "biogen"),
    ("CVS Health Corporation",      "CVS",   "NYSE",   "Healthcare",      "cvs-health"),
    ("Cigna Group",                 "CI",    "NYSE",   "Healthcare",      "cigna"),
    ("Humana Inc.",                 "HUM",   "NYSE",   "Healthcare",      "humana"),
    ("Intuitive Surgical",          "ISRG",  "NASDAQ", "Healthcare",      "intuitive-surgical"),
    ("Edwards Lifesciences",        "EW",    "NYSE",   "Healthcare",      "edwards-lifesciences"),
    ("Becton Dickinson & Co.",      "BDX",   "NYSE",   "Healthcare",      "becton-dickinson"),
    ("Medtronic PLC",               "MDT",   "NYSE",   "Healthcare",      "medtronic"),
    ("Abbott Laboratories",         "ABT",   "NYSE",   "Healthcare",      "abbott"),
    ("Stryker Corporation",         "SYK",   "NYSE",   "Healthcare",      "stryker"),
    ("Boston Scientific Corp.",     "BSX",   "NYSE",   "Healthcare",      "boston-scientific"),
    ("Danaher Corporation",         "DHR",   "NYSE",   "Healthcare",      "danaher"),
    # ── Consumer & Retail ────────────────────────────────────────────────────
    ("Amazon.com Inc.",             "AMZN",  "NASDAQ", "Consumer",        "amazon"),   # already exists - upsert safe
    ("Home Depot Inc.",             "HD",    "NYSE",   "Consumer",        "home-depot"),
    ("Procter & Gamble Co.",        "PG",    "NYSE",   "Consumer",        "procter-gamble"),
    ("PepsiCo Inc.",                "PEP",   "NASDAQ", "Consumer",        "pepsico"),
    ("Costco Wholesale Corp.",      "COST",  "NASDAQ", "Consumer",        "costco"),
    ("Target Corporation",          "TGT",   "NYSE",   "Consumer",        "target"),
    ("Lowe's Companies Inc.",       "LOW",   "NYSE",   "Consumer",        "lowes"),
    ("General Mills Inc.",          "GIS",   "NYSE",   "Consumer",        "general-mills"),
    ("Mondelez International",      "MDLZ",  "NASDAQ", "Consumer",        "mondelez"),
    ("Colgate-Palmolive Co.",       "CL",    "NYSE",   "Consumer",        "colgate-palmolive"),
    ("Kimberly-Clark Corp.",        "KMB",   "NYSE",   "Consumer",        "kimberly-clark"),
    ("Church & Dwight Co.",         "CHD",   "NYSE",   "Consumer",        "church-dwight"),
    ("Dollar General Corp.",        "DG",    "NYSE",   "Consumer",        "dollar-general"),
    ("Dollar Tree Inc.",            "DLTR",  "NASDAQ", "Consumer",        "dollar-tree"),
    ("TJX Companies Inc.",          "TJX",   "NYSE",   "Consumer",        "tjx"),
    ("Ross Stores Inc.",            "ROST",  "NASDAQ", "Consumer",        "ross-stores"),
    ("Booking Holdings Inc.",       "BKNG",  "NASDAQ", "Consumer",        "booking-holdings"),
    ("Airbnb Inc.",                 "ABNB",  "NASDAQ", "Consumer",        "airbnb"),
    ("Uber Technologies Inc.",      "UBER",  "NYSE",   "Consumer",        "uber"),
    ("Lyft Inc.",                   "LYFT",  "NASDAQ", "Consumer",        "lyft"),
    ("DoorDash Inc.",               "DASH",  "NASDAQ", "Consumer",        "doordash"),
    ("Expedia Group Inc.",          "EXPE",  "NASDAQ", "Consumer",        "expedia"),
    ("Marriott International",      "MAR",   "NASDAQ", "Consumer",        "marriott"),
    ("Hilton Worldwide Holdings",   "HLT",   "NYSE",   "Consumer",        "hilton"),
    ("Las Vegas Sands Corp.",       "LVS",   "NYSE",   "Consumer",        "las-vegas-sands"),
    # ── Energy ───────────────────────────────────────────────────────────────
    ("ConocoPhillips",              "COP",   "NYSE",   "Energy",          "conocophillips"),
    ("Marathon Petroleum Corp.",    "MPC",   "NYSE",   "Energy",          "marathon-petroleum"),
    ("Valero Energy Corp.",         "VLO",   "NYSE",   "Energy",          "valero"),
    ("Phillips 66",                 "PSX",   "NYSE",   "Energy",          "phillips-66"),
    ("EOG Resources Inc.",          "EOG",   "NYSE",   "Energy",          "eog-resources"),
    ("Pioneer Natural Resources",   "PXD",   "NYSE",   "Energy",          "pioneer-natural"),
    ("Schlumberger Ltd.",           "SLB",   "NYSE",   "Energy",          "slb"),
    ("Williams Companies Inc.",     "WMB",   "NYSE",   "Energy",          "williams-companies"),
    # ── Industrials ──────────────────────────────────────────────────────────
    ("Caterpillar Inc.",            "CAT",   "NYSE",   "Industrials",     "caterpillar"),
    ("Deere & Company",             "DE",    "NYSE",   "Industrials",     "deere"),
    ("Honeywell International",     "HON",   "NASDAQ", "Industrials",     "honeywell"),
    ("3M Company",                  "MMM",   "NYSE",   "Industrials",     "3m"),
    ("Emerson Electric Co.",        "EMR",   "NYSE",   "Industrials",     "emerson"),
    ("Parker Hannifin Corp.",       "PH",    "NYSE",   "Industrials",     "parker-hannifin"),
    ("Illinois Tool Works",         "ITW",   "NASDAQ", "Industrials",     "illinois-tool-works"),
    ("Eaton Corporation PLC",       "ETN",   "NYSE",   "Industrials",     "eaton"),
    ("Rockwell Automation",         "ROK",   "NYSE",   "Industrials",     "rockwell-automation"),
    ("General Electric Co.",        "GE",    "NYSE",   "Industrials",     "general-electric"),
    ("RTX Corporation",             "RTX",   "NYSE",   "Industrials",     "rtx"),
    ("Northrop Grumman Corp.",      "NOC",   "NYSE",   "Industrials",     "northrop-grumman"),
    ("General Dynamics Corp.",      "GD",    "NYSE",   "Industrials",     "general-dynamics"),
    ("L3Harris Technologies",       "LHX",   "NYSE",   "Industrials",     "l3harris"),
    ("TransDigm Group Inc.",        "TDG",   "NYSE",   "Industrials",     "transdigm"),
    ("Union Pacific Corp.",         "UNP",   "NYSE",   "Industrials",     "union-pacific"),
    ("CSX Corporation",             "CSX",   "NASDAQ", "Industrials",     "csx"),
    ("Norfolk Southern Corp.",      "NSC",   "NYSE",   "Industrials",     "norfolk-southern"),
    ("FedEx Corporation",           "FDX",   "NYSE",   "Industrials",     "fedex"),
    ("United Parcel Service",       "UPS",   "NYSE",   "Industrials",     "ups"),
    # ── Real Estate & Utilities ──────────────────────────────────────────────
    ("American Tower Corp.",        "AMT",   "NYSE",   "Real Estate",     "american-tower"),
    ("Crown Castle Inc.",           "CCI",   "NYSE",   "Real Estate",     "crown-castle"),
    ("Equinix Inc.",                "EQIX",  "NASDAQ", "Real Estate",     "equinix"),
    ("Prologis Inc.",               "PLD",   "NYSE",   "Real Estate",     "prologis"),
    ("Simon Property Group",        "SPG",   "NYSE",   "Real Estate",     "simon-property"),
    ("Duke Energy Corp.",           "DUK",   "NYSE",   "Utilities",       "duke-energy"),
    ("NextEra Energy Inc.",         "NEE",   "NYSE",   "Utilities",       "nextera-energy"),
    ("Southern Company",            "SO",    "NYSE",   "Utilities",       "southern-company"),
    # ── Media & Entertainment ────────────────────────────────────────────────
    ("Comcast Corporation",         "CMCSA", "NASDAQ", "Media",           "comcast"),
    ("Charter Communications",      "CHTR",  "NASDAQ", "Media",           "charter-communications"),
    ("Warner Bros. Discovery",      "WBD",   "NASDAQ", "Media",           "warner-bros-discovery"),
    ("Fox Corporation",             "FOXA",  "NASDAQ", "Media",           "fox"),
    ("Spotify Technology",          "SPOT",  "NYSE",   "Media",           "spotify"),
    ("Roblox Corporation",          "RBLX",  "NYSE",   "Media",           "roblox"),
    # ── Automotive ───────────────────────────────────────────────────────────
    ("General Motors Co.",          "GM",    "NYSE",   "Automotive",      "general-motors"),
    ("Ford Motor Company",          "F",     "NYSE",   "Automotive",      "ford"),
    ("Rivian Automotive",           "RIVN",  "NASDAQ", "Automotive",      "rivian"),
    ("Lucid Group Inc.",            "LCID",  "NASDAQ", "Automotive",      "lucid"),
    # ── Materials ────────────────────────────────────────────────────────────
    ("Linde PLC",                   "LIN",   "NASDAQ", "Materials",       "linde"),
    ("Air Products & Chemicals",    "APD",   "NASDAQ", "Materials",       "air-products"),
    ("Sherwin-Williams Co.",        "SHW",   "NYSE",   "Materials",       "sherwin-williams"),
    ("Nucor Corporation",           "NUE",   "NYSE",   "Materials",       "nucor"),
    # ── International (SEC filers) ───────────────────────────────────────────
    ("Infosys Ltd.",                "INFY",  "NYSE",   "Technology",      "infosys"),
    ("SAP SE",                      "SAP",   "NYSE",   "Technology",      "sap"),
    ("ASML Holding NV",             "ASML",  "NASDAQ", "Technology",      "asml"),
    ("Taiwan Semiconductor",        "TSM",   "NYSE",   "Semiconductors",  "tsmc"),  # already exists
    ("Alibaba Group",               "BABA",  "NYSE",   "E-Commerce",      "alibaba"),
    ("NIO Inc.",                    "NIO",   "NYSE",   "Automotive",      "nio"),
]


def fetch_sec_cik_map():
    """Download SEC EDGAR's official ticker→CIK lookup (free, no auth)."""
    print("Fetching CIK map from SEC EDGAR...")
    url = "https://www.sec.gov/files/company_tickers.json"
    resp = requests.get(url, headers={"User-Agent": "EarningsBloom contact@earningsbloom.com"}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # Map: ticker (uppercase) → {cik_str, title}
    ticker_map = {}
    for entry in data.values():
        ticker = entry["ticker"].upper()
        cik_str = str(entry["cik_str"]).zfill(10)
        ticker_map[ticker] = cik_str
    print(f"  Loaded {len(ticker_map)} tickers from SEC EDGAR.")
    return ticker_map


def seed():
    if not SERVICE_KEY:
        print("ERROR: SUPABASE_SERVICE_KEY not set in .env")
        sys.exit(1)

    db = create_client(SUPABASE_URL, SERVICE_KEY)
    cik_map = fetch_sec_cik_map()

    # Get already existing slugs to avoid duplicate prints
    existing = db.table("companies").select("slug").execute()
    existing_slugs = {r["slug"] for r in existing.data}
    print(f"  Existing companies in DB: {len(existing_slugs)}\n")

    inserted, updated, skipped = 0, 0, 0

    for name, ticker, exchange, sector, slug in NEW_COMPANIES:
        cik_padded = cik_map.get(ticker.upper())

        if not cik_padded:
            print(f"  [SKIP] {ticker:6s} - No CIK found in SEC EDGAR")
            skipped += 1
            continue

        cik_int = str(int(cik_padded))  # strip leading zeros for DB

        record = {
            "id":        str(uuid.uuid4()),
            "name":      name,
            "ticker":    ticker,
            "exchange":  exchange,
            "sector":    sector,
            "cik":       cik_int,
            "slug":      slug,
            "is_active": True,
        }

        try:
            db.table("companies").upsert(record, on_conflict="slug").execute()
            status = "UPDATE" if slug in existing_slugs else "  ADD"
            print(f"  [{status}] {ticker:6s} - {name}  (CIK: {cik_int})")
            if slug in existing_slugs:
                updated += 1
            else:
                inserted += 1
        except Exception as e:
            print(f"  [ERR]  {ticker:6s} - {name}: {e}")
            skipped += 1

        time.sleep(0.05)  # gentle rate limit on Supabase

    total = db.table("companies").select("id", count="exact").execute()
    print(f"\nDone! Added: {inserted} | Updated: {updated} | Skipped: {skipped}")
    print(f"Total companies in DB: {total.count}")


if __name__ == "__main__":
    print("=" * 60)
    print("  EarningsBloom — S&P 500 Company Seeder")
    print("=" * 60 + "\n")
    seed()
