"""
Quick test script to verify Bitcoin Core RPC connection
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from bitcoin_rpc import BitcoinRPCClient

def test_connection():
    """Test Bitcoin Core RPC connection"""
    print("Testing Bitcoin Core RPC connection...")
    print(f"Host: {os.getenv('BITCOIN_RPC_HOST', 'localhost')}")
    print(f"Port: {os.getenv('BITCOIN_RPC_PORT', '8332')}")
    print(f"User: {os.getenv('BITCOIN_RPC_USER', 'bitcoin')}")
    print("-" * 50)
    
    try:
        client = BitcoinRPCClient()
        
        # Test 1: Get blockchain info
        print("\n1. Getting blockchain info...")
        info = client.get_blockchain_info()
        print(f"   ✓ Connected successfully!")
        print(f"   Chain: {info.get('chain', 'unknown')}")
        print(f"   Blocks: {info.get('blocks', 0):,}")
        print(f"   Headers: {info.get('headers', 0):,}")
        print(f"   Verification progress: {info.get('verificationprogress', 0) * 100:.2f}%")
        
        # Test 2: Get current block count
        print("\n2. Getting block count...")
        block_count = client.get_block_count()
        print(f"   ✓ Current block height: {block_count:,}")
        
        # Test 3: Get latest block
        print("\n3. Getting latest block...")
        latest_hash = client.get_block_hash(block_count)
        print(f"   ✓ Latest block hash: {latest_hash[:16]}...")
        
        # Test 4: Get block details
        print("\n4. Getting block details...")
        block = client.get_block(latest_hash, verbosity=1)
        print(f"   ✓ Block size: {block.get('size', 0):,} bytes")
        print(f"   ✓ Transactions: {block.get('nTx', 0):,}")
        print(f"   ✓ Timestamp: {block.get('time', 0)}")
        
        # Test 5: Get mempool info
        print("\n5. Getting mempool info...")
        mempool = client.get_mempool_info()
        print(f"   ✓ Mempool size: {mempool.get('size', 0):,} transactions")
        print(f"   ✓ Mempool bytes: {mempool.get('bytes', 0):,}")
        print(f"   ✓ Total fee: {mempool.get('total_fee', 0):.8f} BTC")
        
        # Test 6: Estimate fee
        print("\n6. Estimating smart fee...")
        fee_estimate = client.estimate_smart_fee(6)
        if 'feerate' in fee_estimate:
            print(f"   ✓ Fee rate (6 blocks): {fee_estimate['feerate']:.8f} BTC/kB")
        else:
            print(f"   ⚠ Fee estimation not available yet")
        
        print("\n" + "=" * 50)
        print("✓ All tests passed! Bitcoin Core connection is working.")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n✗ Connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check if Bitcoin Core is running: bitcoin-cli getblockchaininfo")
        print("2. Verify RPC credentials in .env match bitcoin.conf")
        print("3. Ensure RPC server is enabled in bitcoin.conf (server=1)")
        print("4. Check if rpcallowip includes 127.0.0.1")
        return False

if __name__ == '__main__':
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    success = test_connection()
    sys.exit(0 if success else 1)
