# ============================================================
#  EarningsBloom — One-Click Deploy Script
#  Usage: .\deploy.ps1
#  Optional: .\deploy.ps1 -SkipBuild   (re-deploy existing image)
# ============================================================

param(
    [switch]$SkipBuild
)

$PROJECT    = "project-bec3bbbc-a067-4b2c-8fd"
$SERVICE    = "earningsbloom"
$REGION     = "us-central1"
$IMAGE      = "gcr.io/$PROJECT/$SERVICE"
$SECRETS    = @(
    "GEMINI_API_KEY=GEMINI_API_KEY:latest",
    "SUPABASE_URL=SUPABASE_URL:latest",
    "SUPABASE_KEY=SUPABASE_KEY:latest",
    "SUPABASE_SERVICE_KEY=SUPABASE_SERVICE_KEY:latest",
    "SEC_EDGAR_USER_AGENT=SEC_EDGAR_USER_AGENT:latest",
    "FLASK_SECRET_KEY=FLASK_SECRET_KEY:latest",
    "ADSENSE_PUBLISHER_ID=ADSENSE_PUBLISHER_ID:latest",
    "SITE_URL=SITE_URL:latest",
    "GA_MEASUREMENT_ID=GA_MEASUREMENT_ID:latest",
    "PIPELINE_SECRET=PIPELINE_SECRET:latest"
) -join ","

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "   EarningsBloom Deploy" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Build ──────────────────────────────────────────
if (-not $SkipBuild) {
    Write-Host "[1/2] Building Docker image..." -ForegroundColor Yellow
    gcloud builds submit `
        --tag $IMAGE `
        --project=$PROJECT `
        --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "BUILD FAILED." -ForegroundColor Red
        exit 1
    }
    Write-Host "Build SUCCESS." -ForegroundColor Green
} else {
    Write-Host "[1/2] Skipping build (using existing image)." -ForegroundColor DarkGray
}

# ── Step 2: Deploy ─────────────────────────────────────────
Write-Host ""
Write-Host "[2/2] Deploying to Cloud Run..." -ForegroundColor Yellow

gcloud run deploy $SERVICE `
    --image $IMAGE `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 3 `
    --set-secrets=$SECRETS `
    --project=$PROJECT

if ($LASTEXITCODE -ne 0) {
    Write-Host "DEPLOY FAILED." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "   Deployed successfully!" -ForegroundColor Green
Write-Host "   https://earningsbloom.com" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""
