"""
Test Bitcoin Core RPC connection to Umbrel over Tor
Tests both direct connection and via SOCKS5 proxy
"""

import os
import sys
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

# Load environment from data-ingestion service
env_path = Path(__file__).parent.parent / 'services' / 'data-ingestion' / '.env'
load_dotenv(env_path)

print("=" * 70)
print("Bitcoin Core RPC Connection Test - Umbrel over Tor")
print("=" * 70)

# Get configuration
BITCOIN_RPC_HOST = os.getenv('BITCOIN_RPC_HOST', 'umbrel.local')
BITCOIN_RPC_HOST_ONION = os.getenv('BITCOIN_RPC_HOST_ONION', '')
BITCOIN_RPC_PORT = os.getenv('BITCOIN_RPC_PORT', '8332')
BITCOIN_RPC_USER = os.getenv('BITCOIN_RPC_USER', 'umbrel')
BITCOIN_RPC_PASSWORD = os.getenv('BITCOIN_RPC_PASSWORD', '')

print(f"\nConfiguration:")
print(f"  Local Host: {BITCOIN_RPC_HOST}")
if BITCOIN_RPC_HOST_ONION:
    print(f"  Onion Host: {BITCOIN_RPC_HOST_ONION}")
print(f"  Port: {BITCOIN_RPC_PORT}")
print(f"  User: {BITCOIN_RPC_USER}")
print(f"  Password: {'*' * len(BITCOIN_RPC_PASSWORD) if BITCOIN_RPC_PASSWORD else '(not set)'}")
print()

# Check if we have onion address
has_onion = bool(BITCOIN_RPC_HOST_ONION)
print(f"  Tor Hidden Service Available: {'Yes' if has_onion else 'No'}")
print()


def test_direct_connection():
    """Test direct HTTP connection (works for local/LAN)"""
    print("-" * 70)
    print("Test 1: Direct HTTP Connection")
    print("-" * 70)
    
    url = f"http://{BITCOIN_RPC_HOST}:{BITCOIN_RPC_PORT}"
    auth = HTTPBasicAuth(BITCOIN_RPC_USER, BITCOIN_RPC_PASSWORD)
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getblockchaininfo",
        "params": []
    }
    
    try:
        print(f"Connecting to: {url}")
        start_time = time.time()
        
        response = requests.post(
            url,
            json=payload,
            auth=auth,
            timeout=10
        )
        
        elapsed = time.time() - start_time
        
        response.raise_for_status()
        result = response.json()
        
        if 'error' in result and result['error']:
            print(f"❌ RPC Error: {result['error']}")
            return False
        
        info = result.get('result', {})
        print(f"✅ Connected successfully! (took {elapsed:.2f}s)")
        print(f"   Chain: {info.get('chain', 'unknown')}")
        print(f"   Blocks: {info.get('blocks', 0):,}")
        print(f"   Headers: {info.get('headers', 0):,}")
        print(f"   Verification: {info.get('verificationprogress', 0) * 100:.2f}%")
        return True
        
    except requests.exceptions.Timeout:
        print(f"❌ Connection timeout after 10 seconds")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_tor_connection():
    """Test connection via Tor SOCKS5 proxy"""
    print("\n" + "-" * 70)
    print("Test 2: Tor SOCKS5 Proxy Connection")
    print("-" * 70)
    
    if not BITCOIN_RPC_HOST_ONION:
        print("⏭️  No .onion address configured, skipping Tor test")
        return False
    
    # Check if Tor is running (using port 9150 to avoid conflict with BigQuery emulator)
    tor_proxy = 'socks5h://127.0.0.1:9150'
    
    print(f"Checking Tor proxy at 127.0.0.1:9150...")
    
    # Test Tor proxy connectivity
    try:
        test_response = requests.get(
            'https://check.torproject.org/api/ip',
            proxies={'http': tor_proxy, 'https': tor_proxy},
            timeout=10
        )
        tor_info = test_response.json()
        if tor_info.get('IsTor'):
            print(f"✅ Tor proxy is working! Exit IP: {tor_info.get('IP')}")
        else:
            print(f"⚠️  Connected but not using Tor network")
    except Exception as e:
        print(f"❌ Tor proxy not accessible: {e}")
        print(f"   Make sure Tor is running on port 9050")
        return False
    
    # Now test Bitcoin RPC via Tor using .onion address
    url = f"http://{BITCOIN_RPC_HOST_ONION}:{BITCOIN_RPC_PORT}"
    auth = HTTPBasicAuth(BITCOIN_RPC_USER, BITCOIN_RPC_PASSWORD)
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getblockchaininfo",
        "params": []
    }
    
    proxies = {
        'http': tor_proxy,
        'https': tor_proxy
    }
    
    try:
        print(f"\nConnecting to Bitcoin RPC via Tor: {url}")
        start_time = time.time()
        
        response = requests.post(
            url,
            json=payload,
            auth=auth,
            proxies=proxies,
            timeout=30  # Tor is slower
        )
        
        elapsed = time.time() - start_time
        
        response.raise_for_status()
        result = response.json()
        
        if 'error' in result and result['error']:
            print(f"❌ RPC Error: {result['error']}")
            return False
        
        info = result.get('result', {})
        print(f"✅ Connected via Tor successfully! (took {elapsed:.2f}s)")
        print(f"   Chain: {info.get('chain', 'unknown')}")
        print(f"   Blocks: {info.get('blocks', 0):,}")
        print(f"   Headers: {info.get('headers', 0):,}")
        print(f"   Verification: {info.get('verificationprogress', 0) * 100:.2f}%")
        print(f"   Latency: {elapsed:.2f}s (typical for Tor: 2-5s)")
        return True
        
    except requests.exceptions.Timeout:
        print(f"❌ Connection timeout after 30 seconds")
        print(f"   Tor connections are slower, but this is too long")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_multiple_rpc_calls():
    """Test multiple RPC calls to measure performance"""
    print("\n" + "-" * 70)
    print("Test 3: Multiple RPC Calls (Performance Test)")
    print("-" * 70)
    
    if not BITCOIN_RPC_HOST_ONION:
        print("⏭️  No .onion address configured, skipping performance test")
        return False
    
    tor_proxy = 'socks5h://127.0.0.1:9150'
    url = f"http://{BITCOIN_RPC_HOST_ONION}:{BITCOIN_RPC_PORT}"
    auth = HTTPBasicAuth(BITCOIN_RPC_USER, BITCOIN_RPC_PASSWORD)
    
    proxies = {
        'http': tor_proxy,
        'https': tor_proxy
    }
    
    test_calls = [
        ("getblockcount", []),
        ("getmempoolinfo", []),
        ("estimatesmartfee", [6]),
    ]
    
    print(f"Running {len(test_calls)} RPC calls via Tor...\n")
    
    total_time = 0
    success_count = 0
    
    for method, params in test_calls:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, auth=auth, proxies=proxies, timeout=30)
            elapsed = time.time() - start_time
            total_time += elapsed
            
            response.raise_for_status()
            result = response.json()
            
            if 'error' not in result or not result['error']:
                print(f"✅ {method:20s} - {elapsed:.2f}s")
                success_count += 1
            else:
                print(f"❌ {method:20s} - Error: {result['error']}")
                
        except Exception as e:
            print(f"❌ {method:20s} - Failed: {e}")
    
    if success_count > 0:
        avg_time = total_time / success_count
        print(f"\n📊 Performance Summary:")
        print(f"   Successful calls: {success_count}/{len(test_calls)}")
        print(f"   Average latency: {avg_time:.2f}s")
        print(f"   Total time: {total_time:.2f}s")
        
        if avg_time < 3:
            print(f"   ✅ Good performance for Tor connection")
        elif avg_time < 5:
            print(f"   ⚠️  Acceptable performance for Tor connection")
        else:
            print(f"   ⚠️  Slow performance, may need optimization")
        
        return True
    
    return False


def main():
    """Run all tests"""
    
    if not BITCOIN_RPC_PASSWORD:
        print("❌ BITCOIN_RPC_PASSWORD not set in .env file")
        print(f"   Expected location: {env_path}")
        return False
    
    # Test 1: Direct connection (local network)
    direct_success = test_direct_connection()
    
    # Test 2: Tor connection
    tor_success = test_tor_connection()
    
    # Test 3: Performance test
    if tor_success:
        perf_success = test_multiple_rpc_calls()
    else:
        perf_success = False
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    print(f"Direct Connection (Local):  {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"Tor Connection (.onion):    {'✅ PASS' if tor_success else '❌ FAIL'}")
    print(f"Performance Test:           {'✅ PASS' if perf_success else '❌ FAIL'}")
    
    if tor_success:
        print("\n✅ Umbrel connection is working! Ready for production use.")
        print("\nNext steps:")
        print("1. Use Tor SOCKS5 proxy for all Bitcoin RPC calls")
        print("2. Implement reconnection logic for Tor circuit failures")
        print("3. Use mempool.space WebSocket as backup for block detection")
        print("4. Cache block data in Redis to reduce RPC calls")
    else:
        print("\n❌ Connection failed. Troubleshooting steps:")
        print("1. Verify Tor is running: netstat -an | findstr 9050")
        print("2. Check Umbrel Bitcoin RPC settings in Umbrel dashboard")
        print("3. Verify .onion address is correct")
        print("4. Test Tor manually: curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip")
    
    print("=" * 70)
    
    return tor_success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
