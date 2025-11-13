# Tor Setup for Windows - Umbrel RPC Access

## Why We Need Tor

To access your Umbrel Bitcoin node's `.onion` address from Cloud Run (GCP), we need Tor to route traffic through the Tor network.

## Installation Options

### Option 1: Tor Expert Bundle (Recommended for Services)

1. **Download Tor Expert Bundle**
   - Visit: https://www.torproject.org/download/tor/
   - Download "Expert Bundle" for Windows
   - Extract to `C:\tor\` (or your preferred location)

2. **Create Tor Configuration**
   Create `C:\tor\torrc` with:
   ```
   SocksPort 9050
   ControlPort 9051
   DataDirectory C:\tor\data
   Log notice file C:\tor\tor.log
   ```

3. **Run Tor as a Service**
   ```cmd
   # Run in Command Prompt as Administrator
   cd C:\tor
   tor.exe -f torrc
   ```

4. **Test Tor Connection**
   ```cmd
   curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip
   ```
   Should return: `{"IsTor": true, "IP": "..."}`

### Option 2: Tor Browser (Quick Test Only)

**Note**: Tor Browser's SOCKS proxy is NOT suitable for production use.

1. Download Tor Browser: https://www.torproject.org/download/
2. Start Tor Browser
3. Tor SOCKS proxy runs on `127.0.0.1:9150` (not 9050!)
4. Update test script to use port 9150

### Option 3: Use Tor in Docker (Production Ready)

Create `docker-compose.tor.yml`:
```yaml
version: '3.8'

services:
  tor:
    image: dperson/torproxy
    container_name: tor-proxy
    ports:
      - "9050:9050"  # SOCKS5 proxy
      - "9051:9051"  # Control port
    restart: unless-stopped
    environment:
      - TOR_LOG_LEVEL=notice
```

Run:
```cmd
docker-compose -f docker-compose.tor.yml up -d
```

## Testing Tor Connection

After setting up Tor, run:
```cmd
.\venv312\Scripts\python.exe scripts\test-umbrel-tor-connection.py
```

Expected output:
- ✅ Direct Connection (Local): PASS
- ✅ Tor Connection (.onion): PASS
- ✅ Performance Test: PASS

## Troubleshooting

### Port 9050 Already in Use
```cmd
# Check what's using port 9050
netstat -ano | findstr "9050"

# If it's not Tor, stop that service or use a different port
```

### Tor Connection Timeout
- Check firewall settings
- Verify Tor is running: `netstat -an | findstr "9050"`
- Check Tor logs: `C:\tor\tor.log`

### .onion Address Not Resolving
- Ensure you're using `socks5h://` (not `socks5://`) - the 'h' means hostname resolution via proxy
- Verify .onion address is correct in Umbrel dashboard

## Production Deployment (Cloud Run)

For Cloud Run, we'll include Tor in the Docker container:

```dockerfile
FROM python:3.12-slim

# Install Tor
RUN apt-get update && \
    apt-get install -y tor && \
    rm -rf /var/lib/apt/lists/*

# Copy Tor config
COPY torrc /etc/tor/torrc

# Start Tor in background and run app
CMD tor -f /etc/tor/torrc & python -m uvicorn main:app --host 0.0.0.0 --port 8080
```

## Current Status

- ✅ Umbrel node accessible locally at `umbrel.local:8332`
- ✅ .onion address available: `hkps5arunnwerusagmrcktq76pjlej4dgenqipavkkprmozj37txqwyd.onion:8332`
- ⏳ Tor service needs to be installed/configured
- ⏳ Test Tor connection to .onion address

## Next Steps

1. Install Tor (choose option above)
2. Run test script to verify connection
3. Update ingestion service to use Tor for remote access
4. Deploy to Cloud Run with Tor support
