#!/bin/bash
# Cloud SQL Backup Setup Script
# Configures automated backups for Cloud SQL PostgreSQL instance

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-utxoiq-project}"
INSTANCE_NAME="${CLOUDSQL_INSTANCE:-utxoiq-postgres}"
PRIMARY_REGION="${PRIMARY_REGION:-us-central1}"
BACKUP_REGION="${BACKUP_REGION:-us-east1}"
BACKUP_BUCKET="${BACKUP_BUCKET:-utxoiq-backups}"

echo "=== Cloud SQL Backup Configuration ==="
echo "Project: $PROJECT_ID"
echo "Instance: $INSTANCE_NAME"
echo "Primary Region: $PRIMARY_REGION"
echo "Backup Region: $BACKUP_REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed"
    exit 1
fi

# Set project
echo "Setting GCP project..."
gcloud config set project "$PROJECT_ID"

# Create backup bucket if it doesn't exist
echo "Creating backup bucket..."
if ! gsutil ls "gs://$BACKUP_BUCKET" &> /dev/null; then
    gsutil mb -p "$PROJECT_ID" -l "$BACKUP_REGION" "gs://$BACKUP_BUCKET"
    echo "Backup bucket created: gs://$BACKUP_BUCKET"
else
    echo "Backup bucket already exists: gs://$BACKUP_BUCKET"
fi

# Enable versioning on backup bucket
echo "Enabling versioning on backup bucket..."
gsutil versioning set on "gs://$BACKUP_BUCKET"

# Set lifecycle policy for backup bucket
echo "Setting lifecycle policy for backup bucket..."
cat > /tmp/backup-lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 30,
          "isLive": false
        }
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
        "condition": {
          "age": 7,
          "matchesStorageClass": ["STANDARD"]
        }
      }
    ]
  }
}
EOF
gsutil lifecycle set /tmp/backup-lifecycle.json "gs://$BACKUP_BUCKET"
rm /tmp/backup-lifecycle.json

# Configure automated backups
echo "Configuring automated backups..."
gcloud sql instances patch "$INSTANCE_NAME" \
    --backup-start-time=01:00 \
    --enable-bin-log \
    --retained-backups-count=7 \
    --retained-transaction-log-days=7 \
    --backup-location="$BACKUP_REGION" \
    --quiet

echo "Automated backups configured successfully"

# Enable point-in-time recovery
echo "Enabling point-in-time recovery..."
gcloud sql instances patch "$INSTANCE_NAME" \
    --enable-point-in-time-recovery \
    --quiet

echo "Point-in-time recovery enabled"

# Configure high availability
echo "Configuring high availability..."
gcloud sql instances patch "$INSTANCE_NAME" \
    --availability-type=REGIONAL \
    --quiet

echo "High availability configured"

# Set maintenance window
echo "Setting maintenance window..."
gcloud sql instances patch "$INSTANCE_NAME" \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=2 \
    --quiet

echo "Maintenance window set to Sunday 02:00 UTC"

# Verify configuration
echo ""
echo "=== Verifying Backup Configuration ==="
gcloud sql instances describe "$INSTANCE_NAME" \
    --format="table(
        settings.backupConfiguration.enabled,
        settings.backupConfiguration.startTime,
        settings.backupConfiguration.backupRetentionSettings.retainedBackups,
        settings.backupConfiguration.pointInTimeRecoveryEnabled,
        settings.backupConfiguration.location,
        settings.availabilityType
    )"

echo ""
echo "=== Backup Configuration Complete ==="
echo "Backups will run daily at 01:00 UTC"
echo "7 daily backups will be retained"
echo "Point-in-time recovery is enabled"
echo "Backups are stored in: $BACKUP_REGION"
echo "Backup bucket: gs://$BACKUP_BUCKET"
