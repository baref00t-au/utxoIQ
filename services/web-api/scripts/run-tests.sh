#!/bin/bash
# Test runner script for web-api service
# Sets up Docker containers, runs migrations, and executes tests

set -e

echo "🚀 Starting test environment setup..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Change to script directory
cd "$(dirname "$0")/.."

# Load test environment variables
export $(cat .env.test | grep -v '^#' | xargs)

echo "📦 Starting Docker containers..."
docker-compose -f docker-compose.test.yml up -d

echo "⏳ Waiting for services to be healthy..."
timeout=30
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if docker-compose -f docker-compose.test.yml ps | grep -q "healthy"; then
        echo -e "${GREEN}✓ Services are healthy${NC}"
        break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
    echo "  Waiting... ($elapsed/$timeout seconds)"
done

if [ $elapsed -ge $timeout ]; then
    echo -e "${RED}✗ Services failed to become healthy${NC}"
    docker-compose -f docker-compose.test.yml logs
    docker-compose -f docker-compose.test.yml down
    exit 1
fi

echo "🗄️  Running database migrations..."
alembic upgrade head || {
    echo -e "${RED}✗ Migration failed${NC}"
    docker-compose -f docker-compose.test.yml down
    exit 1
}

echo "🧪 Running tests..."
pytest tests/test_endpoint_protection_simple.py -v --tb=short || TEST_RESULT=$?

echo "🧹 Cleaning up..."
docker-compose -f docker-compose.test.yml down

if [ -n "$TEST_RESULT" ]; then
    echo -e "${RED}✗ Tests failed${NC}"
    exit $TEST_RESULT
else
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
fi
