#!/bin/bash

# Local development environment setup script for utxoIQ

set -e

echo "=========================================="
echo "utxoIQ Local Development Setup"
echo "=========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

command -v docker >/dev/null 2>&1 || { echo "Error: Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Error: Docker Compose is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Error: Node.js is required but not installed."; exit 1; }

echo "✓ All prerequisites met"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file (please configure it with your settings)"
    echo ""
fi

# Start Docker services
echo "Starting Docker services..."
docker-compose up -d

echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."

# PostgreSQL
if docker exec utxoiq-postgres pg_isready -U utxoiq > /dev/null 2>&1; then
    echo "✓ PostgreSQL is ready"
else
    echo "✗ PostgreSQL is not ready"
fi

# Redis
if docker exec utxoiq-redis redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis is ready"
else
    echo "✗ Redis is not ready"
fi

# Install shared module dependencies
echo ""
echo "Installing shared module dependencies..."
cd shared
npm install
cd ..
echo "✓ Shared module dependencies installed"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Services running:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - BigQuery Emulator: localhost:9050"
echo "  - Pub/Sub Emulator: localhost:8085"
echo ""
echo "Next steps:"
echo "  1. Configure .env file with your settings"
echo "  2. Start backend services: cd services/<service-name> && npm run dev"
echo "  3. Start frontend: cd frontend && npm run dev"
echo ""
echo "To stop services: docker-compose down"
echo "To view logs: docker-compose logs -f"
