# GCP Setup Script for Windows PowerShell
# Sets up BigQuery datasets and Pub/Sub topics for utxoIQ

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId
)

Write-Host "Setting up GCP resources for project: $ProjectId" -ForegroundColor Green

# Set default project
gcloud config set project $ProjectId

Write-Host "`n1. Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable bigquery.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage-api.googleapis.com

Write-Host "`n2. Creating BigQuery datasets..." -ForegroundColor Yellow
# Create btc dataset for raw blockchain data
bq mk --dataset --location=US --description="Raw Bitcoin blockchain data" ${ProjectId}:btc

# Create intel dataset for processed intelligence
bq mk --dataset --location=US --description="Processed blockchain intelligence" ${ProjectId}:intel

Write-Host "`n3. Creating BigQuery tables..." -ForegroundColor Yellow
# Create blocks table
bq mk --table ${ProjectId}:btc.blocks infrastructure/bigquery/schemas/btc_blocks.json

# Create insights table
bq mk --table ${ProjectId}:intel.insights infrastructure/bigquery/schemas/intel_insights.json

# Create signals table
bq mk --table ${ProjectId}:intel.signals infrastructure/bigquery/schemas/intel_signals.json

# Create user feedback table
bq mk --table ${ProjectId}:intel.user_feedback infrastructure/bigquery/schemas/intel_user_feedback.json

Write-Host "`n4. Creating Pub/Sub topics..." -ForegroundColor Yellow
gcloud pubsub topics create btc.blocks
gcloud pubsub topics create btc.transactions
gcloud pubsub topics create btc.mempool
gcloud pubsub topics create intel.signals
gcloud pubsub topics create intel.insights

Write-Host "`n5. Creating Pub/Sub subscriptions..." -ForegroundColor Yellow
gcloud pubsub subscriptions create btc.blocks-sub --topic=btc.blocks
gcloud pubsub subscriptions create btc.transactions-sub --topic=btc.transactions
gcloud pubsub subscriptions create btc.mempool-sub --topic=btc.mempool

Write-Host "`n6. Creating Cloud Storage buckets..." -ForegroundColor Yellow
gsutil mb -l US gs://${ProjectId}-charts
gsutil mb -l US gs://${ProjectId}-assets

Write-Host "`n✅ GCP setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Create a service account and download the key:"
Write-Host "   gcloud iam service-accounts create utxoiq-dev --display-name='utxoIQ Development'"
Write-Host "   gcloud iam service-accounts keys create utxoiq-key.json --iam-account=utxoiq-dev@${ProjectId}.iam.gserviceaccount.com"
Write-Host "`n2. Grant permissions:"
Write-Host "   gcloud projects add-iam-policy-binding $ProjectId --member='serviceAccount:utxoiq-dev@${ProjectId}.iam.gserviceaccount.com' --role='roles/bigquery.admin'"
Write-Host "   gcloud projects add-iam-policy-binding $ProjectId --member='serviceAccount:utxoiq-dev@${ProjectId}.iam.gserviceaccount.com' --role='roles/pubsub.admin'"
Write-Host "   gcloud projects add-iam-policy-binding $ProjectId --member='serviceAccount:utxoiq-dev@${ProjectId}.iam.gserviceaccount.com' --role='roles/aiplatform.user'"
Write-Host "   gcloud projects add-iam-policy-binding $ProjectId --member='serviceAccount:utxoiq-dev@${ProjectId}.iam.gserviceaccount.com' --role='roles/storage.admin'"
Write-Host "`n3. Update your .env file with:"
Write-Host "   GCP_PROJECT_ID=$ProjectId"
Write-Host "   GCP_KEY_FILE=./utxoiq-key.json"
