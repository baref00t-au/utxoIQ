# Finding Umbrel Bitcoin Core RPC Credentials

## Method 1: Check Umbrel Dashboard

1. Open Umbrel dashboard: http://umbrel.local
2. Go to Bitcoin app settings
3. Look for "RPC Credentials" or "Connection Details"

## Method 2: SSH into Umbrel

```bash
# SSH into Umbrel
ssh umbrel@umbrel.local

# Find Bitcoin RPC password
cat ~/umbrel/app-data/bitcoin/data/bitcoin/.cookie

# Or check bitcoin.conf
cat ~/umbrel/app-data/bitcoin/data/bitcoin/bitcoin.conf | grep rpcpassword
```

## Method 3: Use .cookie File

Umbrel uses cookie-based authentication. The format is:
```
__cookie__:<long-random-string>
```

## Method 4: Check Environment Variables

```bash
# On Umbrel
docker exec bitcoin bitcoin-cli -getinfo
```

## Common Umbrel Configurations

**Default RPC Port:** 8332
**Default Username:** Usually `umbrel` or `__cookie__`
**Password:** Random string from .cookie file or bitcoin.conf

## Once You Have Credentials

Test connection:
```bash
python scripts/test-bitcoin-connection.py --rpc-url "http://USERNAME:PASSWORD@umbrel.local:8332"
```

## Alternative: Use bitcoin-cli

If you have access to Umbrel's bitcoin-cli:
```bash
# On Umbrel
docker exec bitcoin bitcoin-cli getblockchaininfo
```

Then we can use the same credentials that bitcoin-cli uses.
