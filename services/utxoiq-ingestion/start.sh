#!/bin/bash
# Startup script for utxoIQ ingestion service with optional Tor support

set -e

# Check if Bitcoin RPC URL uses Tor (.onion)
if [[ "$BITCOIN_RPC_URL" == *".onion"* ]]; then
    echo "Detected .onion address - starting Tor daemon..."
    
    # Create Tor data directory with proper permissions
    mkdir -p /tmp/tor
    chmod 700 /tmp/tor
    
    # Start Tor with custom data directory
    tor -f /app/torrc --DataDirectory /tmp/tor &
    TOR_PID=$!
    
    # Wait for Tor to be ready
    echo "Waiting for Tor to establish connection..."
    sleep 15
    
    # Check if Tor is running
    if ! kill -0 $TOR_PID 2>/dev/null; then
        echo "WARNING: Tor failed to start, continuing without Tor"
    else
        echo "Tor is running (PID: $TOR_PID)"
        # Test Tor connection
        curl --socks5-hostname 127.0.0.1:9050 http://check.torproject.org 2>/dev/null && echo "Tor connection verified" || echo "Tor connection test failed"
    fi
else
    echo "No .onion address detected - skipping Tor"
fi

echo "Starting utxoIQ ingestion service..."

# Start the service
exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT}
