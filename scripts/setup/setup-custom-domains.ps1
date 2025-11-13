# Setup Custom Domains for utxoIQ Production
# PowerShell script for Windows

$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = "utxoiq"
$REGION = "us-central1"
$FRONTEND_DOMAIN = "utxoiq.com"
$API_DOMAIN = "api.utxoiq.com"
$WWW_DOMAIN = "www.utxoiq.com"

Write-Host "`n=== utxoIQ Custom Domain Setup ===`n" -ForegroundColor Green

# Check if gcloud is installed
try {
    $null = Get-Command gcloud -ErrorAction Stop
} catch {
    Write-Host "Error: gcloud CLI is not installed" -ForegroundColor Red
    Write-Host "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Check if logged in
$activeAccount = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
if (-not $activeAccount) {
    Write-Host "Not logged in to gcloud. Logging in..." -ForegroundColor Yellow
    gcloud auth login
}

# Set project
Write-Host "Setting GCP project to: $PROJECT_ID" -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

Write-Host "`nStep 1: Checking Cloud Run services" -ForegroundColor Green

# Check if services exist
$frontendService = gcloud run services list --region=$REGION --format="value(metadata.name)" --filter="metadata.name:utxoiq-frontend" 2>$null
$apiService = gcloud run services list --region=$REGION --format="value(metadata.name)" --filter="metadata.name:utxoiq-api" 2>$null

if (-not $frontendService) {
    Write-Host "Warning: Frontend service 'utxoiq-frontend' not found" -ForegroundColor Yellow
    Write-Host "Deploy it first with: cd frontend ; gcloud run deploy utxoiq-frontend --source ."
} else {
    Write-Host "✓ Frontend service found" -ForegroundColor Green
}

if (-not $apiService) {
    Write-Host "Warning: API service 'utxoiq-api' not found" -ForegroundColor Yellow
    Write-Host "Deploy it first with: cd services/web-api ; gcloud run deploy utxoiq-api --source ."
} else {
    Write-Host "✓ API service found" -ForegroundColor Green
}

Write-Host "`nStep 2: Domain Mapping" -ForegroundColor Green
Write-Host "This will create domain mappings for Cloud Run services" -ForegroundColor Yellow
Write-Host "Domains to map:"
Write-Host "  - $FRONTEND_DOMAIN → utxoiq-frontend"
Write-Host "  - $API_DOMAIN → utxoiq-api"
Write-Host ""

$response = Read-Host "Continue? (y/n)"
if ($response -ne "y" -and $response -ne "Y") {
    Write-Host "Skipping domain mapping"
} else {
    # Map frontend domain
    if ($frontendService) {
        Write-Host "Mapping $FRONTEND_DOMAIN to utxoiq-frontend..." -ForegroundColor Yellow
        try {
            gcloud run domain-mappings create `
                --service=utxoiq-frontend `
                --domain=$FRONTEND_DOMAIN `
                --region=$REGION 2>$null
        } catch {
            Write-Host "Domain mapping may already exist" -ForegroundColor Yellow
        }
    }

    # Map API domain
    if ($apiService) {
        Write-Host "Mapping $API_DOMAIN to utxoiq-api..." -ForegroundColor Yellow
        try {
            gcloud run domain-mappings create `
                --service=utxoiq-api `
                --domain=$API_DOMAIN `
                --region=$REGION 2>$null
        } catch {
            Write-Host "Domain mapping may already exist" -ForegroundColor Yellow
        }
    }
}

Write-Host "`nStep 3: DNS Configuration" -ForegroundColor Green
Write-Host "You need to add these DNS records in your domain registrar:`n" -ForegroundColor Yellow

# Get DNS records for frontend
if ($frontendService) {
    Write-Host "For ${FRONTEND_DOMAIN}:" -ForegroundColor Green
    try {
        gcloud run domain-mappings describe $FRONTEND_DOMAIN `
            --region=$REGION `
            --format="table(status.resourceRecords[].name, status.resourceRecords[].type, status.resourceRecords[].rrdata)" 2>$null
    } catch {
        Write-Host "Run domain mapping first"
    }
    Write-Host ""
}

# Get DNS records for API
if ($apiService) {
    Write-Host "For ${API_DOMAIN}:" -ForegroundColor Green
    try {
        gcloud run domain-mappings describe $API_DOMAIN `
            --region=$REGION `
            --format="table(status.resourceRecords[].name, status.resourceRecords[].type, status.resourceRecords[].rrdata)" 2>$null
    } catch {
        Write-Host "Run domain mapping first"
    }
    Write-Host ""
}

Write-Host "`nStep 4: Manual Configuration Required" -ForegroundColor Green
Write-Host "Complete these steps manually:`n" -ForegroundColor Yellow

Write-Host "1. Firebase Console - Add Authorized Domains:"
Write-Host "   https://console.firebase.google.com/project/$PROJECT_ID/authentication/settings"
Write-Host "   Add: $FRONTEND_DOMAIN, $API_DOMAIN, $WWW_DOMAIN"
Write-Host ""

Write-Host "2. Google Cloud Console - Update OAuth Redirect URIs:"
Write-Host "   https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"
Write-Host "   Add these redirect URIs:"
Write-Host "   - https://$FRONTEND_DOMAIN/__/auth/handler"
Write-Host "   - https://$API_DOMAIN/__/auth/handler"
Write-Host "   - https://$WWW_DOMAIN/__/auth/handler"
Write-Host ""

Write-Host "3. GitHub OAuth App - Update Callback URL:"
Write-Host "   https://github.com/settings/developers"
Write-Host "   Set callback URL to: https://$FRONTEND_DOMAIN/__/auth/handler"
Write-Host ""

Write-Host "4. Update Environment Variables:"
Write-Host "   Backend: services/web-api/.env"
Write-Host "   CORS_ORIGINS=https://$FRONTEND_DOMAIN,https://$WWW_DOMAIN,https://$API_DOMAIN"
Write-Host ""
Write-Host "   Frontend: frontend/.env.production"
Write-Host "   NEXT_PUBLIC_API_URL=https://$API_DOMAIN"
Write-Host ""

Write-Host "`nStep 5: Verification" -ForegroundColor Green
Write-Host "After DNS propagates (5-10 minutes), verify:`n" -ForegroundColor Yellow

Write-Host "Check domain mappings:"
Write-Host "  gcloud run domain-mappings list --region=$REGION"
Write-Host ""

Write-Host "Test SSL certificates:"
Write-Host "  curl -vI https://$FRONTEND_DOMAIN 2>&1 | Select-String 'SSL certificate'"
Write-Host "  curl -vI https://$API_DOMAIN 2>&1 | Select-String 'SSL certificate'"
Write-Host ""

Write-Host "Test authentication:"
Write-Host "  Open https://$FRONTEND_DOMAIN and try signing in"
Write-Host ""

Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host "See docs/firebase-custom-domains-setup.md for detailed instructions"
