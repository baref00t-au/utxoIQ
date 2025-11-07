#!/bin/bash

# utxoIQ Grafana Observability Setup Script
# This script sets up the Grafana and Prometheus monitoring stack

set -e

echo "=========================================="
echo "utxoIQ Grafana Observability Setup"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before continuing."
    echo "Press Enter to continue after editing .env, or Ctrl+C to exit..."
    read
fi

# Load environment variables
source .env

# Validate required environment variables
if [ -z "$GRAFANA_ADMIN_USER" ] || [ -z "$GRAFANA_ADMIN_PASSWORD" ]; then
    echo "Error: GRAFANA_ADMIN_USER and GRAFANA_ADMIN_PASSWORD must be set in .env"
    exit 1
fi

echo "Step 1: Creating required directories..."
mkdir -p provisioning/datasources
mkdir -p provisioning/dashboards
mkdir -p dashboards
mkdir -p alerts

echo "Step 2: Validating dashboard JSON files..."
for dashboard in dashboards/*.json; do
    if [ -f "$dashboard" ]; then
        if ! python -m json.tool "$dashboard" > /dev/null 2>&1; then
            echo "Error: Invalid JSON in $dashboard"
            exit 1
        fi
        echo "  ✓ $(basename $dashboard)"
    fi
done

echo "Step 3: Validating alert YAML files..."
for alert in alerts/*.yml; do
    if [ -f "$alert" ]; then
        echo "  ✓ $(basename $alert)"
    fi
done

echo "Step 4: Starting Docker containers..."
docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 10

# Check if Grafana is running
if docker ps | grep -q utxoiq-grafana; then
    echo "  ✓ Grafana is running"
else
    echo "  ✗ Grafana failed to start"
    docker-compose logs grafana
    exit 1
fi

# Check if Prometheus is running
if docker ps | grep -q utxoiq-prometheus; then
    echo "  ✓ Prometheus is running"
else
    echo "  ✗ Prometheus failed to start"
    docker-compose logs prometheus
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Access your dashboards:"
echo "  Grafana:    http://localhost:3000"
echo "  Prometheus: http://localhost:9090"
echo ""
echo "Grafana credentials:"
echo "  Username: $GRAFANA_ADMIN_USER"
echo "  Password: $GRAFANA_ADMIN_PASSWORD"
echo ""
echo "Available dashboards:"
echo "  - utxoIQ - Performance Monitoring"
echo "  - utxoIQ - Cost Tracking & Analytics"
echo "  - utxoIQ - Accuracy & Feedback"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
