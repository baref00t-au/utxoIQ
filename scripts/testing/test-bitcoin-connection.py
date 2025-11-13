#!/usr/bin/env python3
"""
Test Bitcoin Core RPC connection.
"""

import sys
import os

# Add service path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'feature-engine', 'src'))

try:
    from bitcoinrpc.authproxy import AuthServiceProxy
except ImportError:
    print("Error: python-bitcoinrpc not installed")
    print("Install with: pip install python-bitcoinrpc")
    sys.exit(1)


def test_connection(rpc_url: str = "http://user:pass@localhost:8332"):
    """Test Bitcoin Core RPC connection."""
    print("="*60)
    print("Testing Bitcoin Core RPC Connection")
    print("="*60)
    print(f"URL: {rpc_url.replace('user:pass', 'user:***')}")
    print()
    
    try:
        print("Connecting to Bitcoin Core...")
        rpc = AuthServiceProxy(rpc_url)
        
        # Test basic connection
        print("✓ Connection established")
        
        # Get blockchain info
        print("\nFetching blockchain info...")
        info = rpc.getblockchaininfo()
        
        print(f"✓ Chain: {info['chain']}")
        print(f"✓ Blocks: {info['blocks']:,}")
        print(f"✓ Headers: {info['headers']:,}")
        print(f"✓ Verification progress: {info.get('verificationprogress', 1.0) * 100:.2f}%")
        print(f"✓ Pruned: {info.get('pruned', False)}")
        
        # Get latest block
        print("\nFetching latest block...")
        latest_height = info['blocks']
        block_hash = rpc.getblockhash(latest_height)
        block = rpc.getblock(block_hash, 1)  # Verbosity 1 for basic info
        
        print(f"✓ Latest block height: {latest_height:,}")
        print(f"✓ Latest block hash: {block_hash}")
        print(f"✓ Block time: {block['time']}")
        print(f"✓ Transactions: {block['nTx']}")
        
        # Calculate blocks in last hour (approximately 6 blocks)
        blocks_per_hour = 6
        start_height = max(0, latest_height - blocks_per_hour)
        
        print(f"\n✓ Ready to backfill blocks {start_height:,} to {latest_height:,}")
        print(f"  ({blocks_per_hour} blocks, approximately 1 hour)")
        
        print("\n" + "="*60)
        print("Connection Test: SUCCESS")
        print("="*60)
        print("\nNext step: Run backfill script")
        print("  python scripts/backfill-recent-blocks.py")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Connection failed: {str(e)}")
        print("\n" + "="*60)
        print("Connection Test: FAILED")
        print("="*60)
        print("\nTroubleshooting:")
        print("  1. Check Bitcoin Core is running")
        print("  2. Verify RPC credentials in bitcoin.conf")
        print("  3. Check RPC port (default: 8332)")
        print("  4. Ensure RPC server is enabled (server=1)")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Bitcoin Core RPC connection")
    parser.add_argument(
        "--rpc-url",
        default="http://user:pass@localhost:8332",
        help="Bitcoin Core RPC URL"
    )
    
    args = parser.parse_args()
    
    success = test_connection(args.rpc_url)
    sys.exit(0 if success else 1)
