#!/bin/bash
# Create BigQuery tables for signal-to-insight pipeline
# Usage: ./create-signal-tables.sh [project-id]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project ID from argument or environment
PROJECT_ID="${1:-$GCP_PROJECT_ID}"

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: Project ID not provided${NC}"
    echo "Usage: $0 [project-id]"
    echo "Or set GCP_PROJECT_ID environment variable"
    exit 1
fi

echo -e "${GREEN}Creating BigQuery tables for project: $PROJECT_ID${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCHEMA_DIR="$SCRIPT_DIR/../../infrastructure/bigquery/schemas"

# Function to create table
create_table() {
    local sql_file=$1
    local table_name=$2
    
    echo -e "${YELLOW}Creating table: $table_name${NC}"
    
    if bq query --project_id="$PROJECT_ID" --use_legacy_sql=false < "$sql_file"; then
        echo -e "${GREEN}✓ Successfully created $table_name${NC}"
    else
        echo -e "${RED}✗ Failed to create $table_name${NC}"
        return 1
    fi
    echo ""
}

# Create datasets if they don't exist
echo -e "${YELLOW}Ensuring datasets exist...${NC}"
bq mk --dataset --project_id="$PROJECT_ID" intel 2>/dev/null || echo "Dataset intel already exists"
bq mk --dataset --project_id="$PROJECT_ID" btc 2>/dev/null || echo "Dataset btc already exists"
echo ""

# Create tables
create_table "$SCHEMA_DIR/intel_signals.sql" "intel.signals"
create_table "$SCHEMA_DIR/intel_insights.sql" "intel.insights"
create_table "$SCHEMA_DIR/btc_known_entities.sql" "btc.known_entities"

# Verify tables were created
echo -e "${YELLOW}Verifying tables...${NC}"
echo ""

echo "Tables in intel dataset:"
bq ls --project_id="$PROJECT_ID" intel

echo ""
echo "Tables in btc dataset:"
bq ls --project_id="$PROJECT_ID" btc

echo ""
echo -e "${GREEN}✓ All tables created successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Populate known entities: python scripts/populate_treasury_entities.py"
echo "2. Deploy utxoiq-ingestion service"
echo "3. Deploy insight-generator service"
