#!/bin/bash

# Setup Custom Domains for utxoIQ Production
# This script helps configure custom domains for Firebase Auth and Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
FIREBASE_PROJECT_ID="utxoiq"
DEV_PROJECT_ID="utxoiq-dev"
PROD_PROJECT_ID="utxoiq"
REGION="us-central1"

# Production domains
PROD_FRONTEND_DOMAIN="utxoiq.com"
PROD_API_DOMAIN="api.utxoiq.com"
WWW_DOMAIN="www.utxoiq.com"

# Development domains
DEV_FRONTEND_DOMAIN="dev.utxoiq.com"
DEV_API_DOMAIN="dev-api.utxoiq.com"

# Staging domains
STAGING_FRONTEND_DOMAIN="staging.utxoiq.com"
STAGING_API_DOMAIN="staging-api.utxoiq.com"

echo -e "${GREEN}=== utxoIQ Custom Domain Setup ===${NC}\n"

echo "Firebase Project: ${FIREBASE_PROJECT_ID}"
echo "Dev GCP Project: ${DEV_PROJECT_ID}"
echo "Prod GCP Project: ${PROD_PROJECT_ID}"
echo ""

# Ask which environment to configure
echo "Which environment do you want to configure?"
echo "1) Development (${DEV_PROJECT_ID})"
echo "2) Staging (${DEV_PROJECT_ID})"
echo "3) Production (${PROD_PROJECT_ID})"
read -p "Enter choice (1-3): " ENV_CHOICE

case $ENV_CHOICE in
    1)
        PROJECT_ID=$DEV_PROJECT_ID
        FRONTEND_DOMAIN=$DEV_FRONTEND_DOMAIN
        API_DOMAIN=$DEV_API_DOMAIN
        SERVICE_SUFFIX="-dev"
        echo -e "${GREEN}Configuring Development environment${NC}"
        ;;
    2)
        PROJECT_ID=$DEV_PROJECT_ID
        FRONTEND_DOMAIN=$STAGING_FRONTEND_DOMAIN
        API_DOMAIN=$STAGING_API_DOMAIN
        SERVICE_SUFFIX="-staging"
        echo -e "${GREEN}Configuring Staging environment${NC}"
        ;;
    3)
        PROJECT_ID=$PROD_PROJECT_ID
        FRONTEND_DOMAIN=$PROD_FRONTEND_DOMAIN
        API_DOMAIN=$PROD_API_DOMAIN
        SERVICE_SUFFIX=""
        echo -e "${GREEN}Configuring Production environment${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${YELLOW}Not logged in to gcloud. Logging in...${NC}"
    gcloud auth login
fi

# Set project
echo -e "${YELLOW}Setting GCP project to: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

echo -e "\n${GREEN}Step 1: Checking Cloud Run services${NC}"

# Check if services exist
FRONTEND_SERVICE=$(gcloud run services list --region=${REGION} --format="value(metadata.name)" --filter="metadata.name:utxoiq-frontend${SERVICE_SUFFIX}" 2>/dev/null || echo "")
API_SERVICE=$(gcloud run services list --region=${REGION} --format="value(metadata.name)" --filter="metadata.name:utxoiq-api${SERVICE_SUFFIX}" 2>/dev/null || echo "")

if [ -z "$FRONTEND_SERVICE" ]; then
    echo -e "${YELLOW}Warning: Frontend service 'utxoiq-frontend${SERVICE_SUFFIX}' not found${NC}"
    echo "Deploy it first with: cd frontend && gcloud run deploy utxoiq-frontend${SERVICE_SUFFIX} --source ."
else
    echo -e "${GREEN}✓ Frontend service found: ${FRONTEND_SERVICE}${NC}"
fi

if [ -z "$API_SERVICE" ]; then
    echo -e "${YELLOW}Warning: API service 'utxoiq-api${SERVICE_SUFFIX}' not found${NC}"
    echo "Deploy it first with: cd services/web-api && gcloud run deploy utxoiq-api${SERVICE_SUFFIX} --source ."
else
    echo -e "${GREEN}✓ API service found: ${API_SERVICE}${NC}"
fi

echo -e "\n${GREEN}Step 2: Domain Mapping${NC}"
echo -e "${YELLOW}This will create domain mappings for Cloud Run services${NC}"
echo -e "GCP Project: ${PROJECT_ID}"
echo -e "Domains to map:"
echo -e "  - ${FRONTEND_DOMAIN} → utxoiq-frontend${SERVICE_SUFFIX}"
echo -e "  - ${API_DOMAIN} → utxoiq-api${SERVICE_SUFFIX}"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Skipping domain mapping"
else
    # Map frontend domain
    if [ ! -z "$FRONTEND_SERVICE" ]; then
        echo -e "${YELLOW}Mapping ${FRONTEND_DOMAIN} to utxoiq-frontend...${NC}"
        gcloud run domain-mappings create \
            --service=utxoiq-frontend \
            --domain=${FRONTEND_DOMAIN} \
            --region=${REGION} 2>/dev/null || echo -e "${YELLOW}Domain mapping may already exist${NC}"
    fi

    # Map API domain
    if [ ! -z "$API_SERVICE" ]; then
        echo -e "${YELLOW}Mapping ${API_DOMAIN} to utxoiq-api...${NC}"
        gcloud run domain-mappings create \
            --service=utxoiq-api \
            --domain=${API_DOMAIN} \
            --region=${REGION} 2>/dev/null || echo -e "${YELLOW}Domain mapping may already exist${NC}"
    fi
fi

echo -e "\n${GREEN}Step 3: DNS Configuration${NC}"
echo -e "${YELLOW}You need to add these DNS records in your domain registrar:${NC}\n"

# Get DNS records for frontend
if [ ! -z "$FRONTEND_SERVICE" ]; then
    echo -e "${GREEN}For ${FRONTEND_DOMAIN}:${NC}"
    gcloud run domain-mappings describe ${FRONTEND_DOMAIN} \
        --region=${REGION} \
        --format="table(status.resourceRecords[].name, status.resourceRecords[].type, status.resourceRecords[].rrdata)" 2>/dev/null || echo "Run domain mapping first"
    echo ""
fi

# Get DNS records for API
if [ ! -z "$API_SERVICE" ]; then
    echo -e "${GREEN}For ${API_DOMAIN}:${NC}"
    gcloud run domain-mappings describe ${API_DOMAIN} \
        --region=${REGION} \
        --format="table(status.resourceRecords[].name, status.resourceRecords[].type, status.resourceRecords[].rrdata)" 2>/dev/null || echo "Run domain mapping first"
    echo ""
fi

echo -e "\n${GREEN}Step 4: Manual Configuration Required${NC}"
echo -e "${YELLOW}Complete these steps manually:${NC}\n"

echo "1. Firebase Console - Add Authorized Domains:"
echo "   https://console.firebase.google.com/project/${PROJECT_ID}/authentication/settings"
echo "   Add: ${FRONTEND_DOMAIN}, ${API_DOMAIN}, ${WWW_DOMAIN}"
echo ""

echo "2. Google Cloud Console - Update OAuth Redirect URIs:"
echo "   https://console.cloud.google.com/apis/credentials?project=${PROJECT_ID}"
echo "   Add these redirect URIs:"
echo "   - https://${FRONTEND_DOMAIN}/__/auth/handler"
echo "   - https://${API_DOMAIN}/__/auth/handler"
echo "   - https://${WWW_DOMAIN}/__/auth/handler"
echo ""

echo "3. GitHub OAuth App - Update Callback URL:"
echo "   https://github.com/settings/developers"
echo "   Set callback URL to: https://${FRONTEND_DOMAIN}/__/auth/handler"
echo ""

echo "4. Update Environment Variables:"
echo "   Backend: services/web-api/.env"
echo "   CORS_ORIGINS=https://${FRONTEND_DOMAIN},https://${WWW_DOMAIN},https://${API_DOMAIN}"
echo ""
echo "   Frontend: frontend/.env.production"
echo "   NEXT_PUBLIC_API_URL=https://${API_DOMAIN}"
echo ""

echo -e "\n${GREEN}Step 5: Verification${NC}"
echo -e "${YELLOW}After DNS propagates (5-10 minutes), verify:${NC}\n"

echo "Check domain mappings:"
echo "  gcloud run domain-mappings list --region=${REGION}"
echo ""

echo "Test SSL certificates:"
echo "  curl -vI https://${FRONTEND_DOMAIN} 2>&1 | grep 'SSL certificate'"
echo "  curl -vI https://${API_DOMAIN} 2>&1 | grep 'SSL certificate'"
echo ""

echo "Test authentication:"
echo "  Open https://${FRONTEND_DOMAIN} and try signing in"
echo ""

echo -e "${GREEN}=== Setup Complete ===${NC}"
echo -e "See docs/firebase-custom-domains-setup.md for detailed instructions"
