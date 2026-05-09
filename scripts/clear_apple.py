"""Clear stale Apple records so the corrected pipeline can reprocess them cleanly."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from models.db import get_admin_db

db = get_admin_db()
co = db.table("companies").select("id,name").eq("slug", "apple").execute()
if not co.data:
    print("Apple not found")
    sys.exit(1)

cid = co.data[0]["id"]
print(f"Clearing stale records for Apple Inc...")

ec = db.table("earnings_calls").select("id,quarter").eq("company_id", cid).execute()
for row in ec.data:
    db.table("summaries").delete().eq("earnings_call_id", row["id"]).execute()
    print(f"  Deleted summary for {row['quarter']}")

db.table("earnings_calls").delete().eq("company_id", cid).execute()
print(f"  Deleted {len(ec.data)} earnings call record(s)")
print("Done! Now run: python scripts/test_pipeline.py")
