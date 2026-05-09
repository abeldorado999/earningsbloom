import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from models.db import get_admin_db
db = get_admin_db()
companies = db.table("companies").select("name,ticker,slug,cik").order("name").execute()
print(f"Total companies in DB: {len(companies.data)}")
print()
for c in companies.data:
    cik = c.get("cik") or "NO_CIK"
    print(f"  {c['ticker']:<8}  {c['slug']:<35}  cik={cik}")
