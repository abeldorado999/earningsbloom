"""Create all EarningsBloom secrets in GCP Secret Manager."""
import subprocess, sys

PROJECT = "project-bec3bbbc-a067-4b2c-8fd"

secrets = {
    "GEMINI_API_KEY":        "AIzaSyAVG7GssuNK2WvwVUBw1CPGFYk8vh28lVk",
    "SUPABASE_URL":          "https://upjlskawmgbmntawltcu.supabase.co",
    "SUPABASE_KEY":          "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVwamxza2F3bWdibW50YXdsdGN1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzczMjAyNDYsImV4cCI6MjA5Mjg5NjI0Nn0.QhvDO8UCXxEqwfPdO8zRSE1YqWVlbDWhJZPWpj6MltM",
    "SUPABASE_SERVICE_KEY":  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVwamxza2F3bWdibW50YXdsdGN1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMyMDI0NiwiZXhwIjoyMDkyODk2MjQ2fQ.Azz0RJcdjulFx8UKkqVnCJ6qPBHoMRVLtqwO5HVmYUw",
    "SEC_EDGAR_USER_AGENT":  "EarningsBloom contact@earningsbloom.com",
    "FLASK_SECRET_KEY":      "earningsbloom-secret-2026-gcp",
    "ADSENSE_PUBLISHER_ID":  "ca-pub-2391191777904568",
    "SITE_URL":              "https://earningsbloom.com",
}

for name, value in secrets.items():
    # Try to create; if exists, add new version
    create = subprocess.run(
        ["gcloud", "secrets", "create", name,
         "--replication-policy=automatic",
         f"--project={PROJECT}"],
        capture_output=True, text=True
    )
    if "already exists" in create.stderr or create.returncode == 0:
        # Add version
        proc = subprocess.run(
            ["gcloud", "secrets", "versions", "add", name,
             "--data-file=-", f"--project={PROJECT}"],
            input=value, capture_output=True, text=True
        )
    else:
        # Create with initial value
        proc = subprocess.run(
            ["gcloud", "secrets", "create", name,
             "--replication-policy=automatic",
             "--data-file=-",
             f"--project={PROJECT}"],
            input=value, capture_output=True, text=True
        )

    if proc.returncode == 0:
        print(f"  [OK]  {name}")
    else:
        print(f"  [ERR] {name}: {proc.stderr.strip()[:80]}")

print("\nAll secrets processed.")
