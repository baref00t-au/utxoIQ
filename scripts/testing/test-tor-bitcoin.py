"""
Test Bitcoin RPC connection over Tor.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_tor_connection():
    """Test Tor SOCKS proxy connection."""
    print("=" * 60)
    print("Testing Tor Connection")
    print("=" * 60)
    
    # Test 1: Check if Tor is running locally
    print("\n1. Checking local Tor service...")
    try:
        # Try to connect to Tor SOCKS port
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 9050))
        sock.close()
        
        if result == 0:
            print("   ✅ Tor SOCKS proxy is running on 127.0.0.1:9050")
        else:
            print("   ❌ Tor SOCKS proxy is NOT running on 127.0.0.1:9050")
            print("   Please install and start Tor:")
            print("   - Windows: Download Tor Browser or install Tor service")
            print("   - Linux: sudo apt install tor && sudo systemctl start tor")
            print("   - Mac: brew install tor && brew services start tor")
            return False
    except Exception as e:
        print(f"   ❌ Error checking Tor: {e}")
        return False
    
    # Test 2: Test Tor connection to check.torproject.org
    print("\n2. Testing Tor connectivity...")
    try:
        session = requests.Session()
        session.proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        
        response = session.get('https://check.torproject.org/api/ip', timeout=30)
        data = response.json()
        
        if data.get('IsTor'):
            print(f"   ✅ Tor is working! Exit IP: {data.get('IP')}")
        else:
            print(f"   ❌ Not using Tor. IP: {data.get('IP')}")
            return False
    except Exception as e:
        print(f"   ❌ Tor connectivity test failed: {e}")
        return False
    
    return True


def test_bitcoin_rpc_over_tor():
    """Test Bitcoin RPC connection over Tor."""
    print("\n" + "=" * 60)
    print("Testing Bitcoin RPC over Tor")
    print("=" * 60)
    
    # Get credentials from environment
    password = os.getenv('BITCOIN_RPC_PASSWORD')
    onion_address = "hkps5arunnwerusagmrcktq76pjlej4dgenqipavkkprmozj37txqwyd.onion"
    
    if not password:
        print("❌ BITCOIN_RPC_PASSWORD not found in .env")
        return False
    
    rpc_url = f"http://umbrel:{password}@{onion_address}:8332"
    
    print(f"\n1. Testing connection to {onion_address}...")
    print(f"   (This may take 10-30 seconds for first connection)")
    
    try:
        # Create session with Tor proxy
        session = requests.Session()
        session.proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        
        # Test RPC call
        payload = {
            "jsonrpc": "1.0",
            "id": "test",
            "method": "getblockcount",
            "params": []
        }
        
        response = session.post(
            f"http://{onion_address}:8332",
            json=payload,
            auth=('umbrel', password),
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            block_count = result.get('result')
            print(f"   ✅ Connected successfully!")
            print(f"   ✅ Current block height: {block_count}")
            
            # Test another call
            print("\n2. Testing getblockchaininfo...")
            payload['method'] = 'getblockchaininfo'
            response = session.post(
                f"http://{onion_address}:8332",
                json=payload,
                auth=('umbrel', password),
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                info = result.get('result', {})
                print(f"   ✅ Chain: {info.get('chain')}")
                print(f"   ✅ Blocks: {info.get('blocks')}")
                print(f"   ✅ Headers: {info.get('headers')}")
                print(f"   ✅ Verification progress: {info.get('verificationprogress', 0) * 100:.2f}%")
                
                return True
            else:
                print(f"   ❌ RPC call failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        else:
            print(f"   ❌ Connection failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Connection timed out")
        print("   This could mean:")
        print("   - Tor circuit is still building (try again in 30 seconds)")
        print("   - Bitcoin node is not accessible via Tor")
        print("   - Firewall blocking connection")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_with_python_bitcoinrpc():
    """Test using python-bitcoinrpc library with Tor."""
    print("\n" + "=" * 60)
    print("Testing with python-bitcoinrpc Library")
    print("=" * 60)
    
    try:
        from bitcoinrpc.authproxy import AuthServiceProxy
        import socks
        import socket
        
        password = os.getenv('BITCOIN_RPC_PASSWORD')
        onion_address = "hkps5arunnwerusagmrcktq76pjlej4dgenqipavkkprmozj37txqwyd.onion"
        
        if not password:
            print("❌ BITCOIN_RPC_PASSWORD not found in .env")
            return False
        
        print("\n1. Configuring SOCKS proxy...")
        
        # Configure SOCKS proxy globally (for this test only)
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
        socket.socket = socks.socksocket
        
        print("   ✅ SOCKS proxy configured")
        
        print(f"\n2. Connecting to Bitcoin Core via Tor...")
        rpc_url = f"http://umbrel:{password}@{onion_address}:8332"
        rpc = AuthServiceProxy(rpc_url, timeout=60)
        
        print("   Testing getblockcount...")
        block_count = rpc.getblockcount()
        print(f"   ✅ Block count: {block_count}")
        
        print("\n   Testing getblockchaininfo...")
        info = rpc.getblockchaininfo()
        print(f"   ✅ Chain: {info['chain']}")
        print(f"   ✅ Blocks: {info['blocks']}")
        print(f"   ✅ Verification: {info['verificationprogress'] * 100:.2f}%")
        
        return True
        
    except ImportError:
        print("   ⚠️  python-bitcoinrpc not installed")
        print("   Install with: pip install python-bitcoinrpc")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n🧅 Bitcoin RPC over Tor Test Suite\n")
    
    # Test 1: Tor connectivity
    if not test_tor_connection():
        print("\n❌ Tor is not working. Please fix Tor setup first.")
        sys.exit(1)
    
    # Test 2: Bitcoin RPC over Tor (using requests)
    if not test_bitcoin_rpc_over_tor():
        print("\n❌ Bitcoin RPC connection failed.")
        sys.exit(1)
    
    # Test 3: Using python-bitcoinrpc library
    test_with_python_bitcoinrpc()
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\nYour Bitcoin node is accessible via Tor.")
    print("You can now deploy the monitoring service to Cloud Run.")
    print("\nNext steps:")
    print("  cd services/utxoiq-ingestion")
    print("  gcloud run deploy utxoiq-ingestion --source . ...")


if __name__ == '__main__':
    main()
