#!/bin/bash
# Startup script for block monitor with Tor

set -e

echo "Starting Tor daemon..."
tor -f /etc/tor/torrc &
TOR_PID=$!

# Wait for Tor to be ready
echo "Waiting for Tor to establish connection..."
sleep 10

# Check if Tor is running
if ! kill -0 $TOR_PID 2>/dev/null; then
    echo "ERROR: Tor failed to start"
    exit 1
fi

echo "Tor is running (PID: $TOR_PID)"
echo "Starting block monitor..."

# Start block monitor
python block-monitor.py

# If monitor exits, kill Tor
kill $TOR_PID 2>/dev/null || true
