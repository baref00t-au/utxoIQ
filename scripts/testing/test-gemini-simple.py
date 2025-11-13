#!/usr/bin/env python3
"""
Test Gemini AI integration using direct HTTP requests (Python 3.14 compatible)
"""

import os
import sys
import json
import requests
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'data-ingestion', 'src'))

from dotenv import load_dotenv
load_dotenv()

# Import Bitcoin RPC client
from bitcoin_rpc import BitcoinRPCClient

def format_block_summary(block_data):
    """Format block data for AI analysis"""
    return f"""
Bitcoin Block Analysis Request:

Block Height: {block_data.get('height')}
Block Hash: {block_data.get('hash')}
Timestamp: {datetime.fromtimestamp(block_data.get('time')).strftime('%Y-%m-%d %H:%M:%S UTC')}
Number of Transactions: {len(block_data.get('tx', []))}
Block Size: {block_data.get('size'):,} bytes
Block Weight: {block_data.get('weight'):,}

Transaction Summary:
- Total transactions: {len(block_data.get('tx', []))}
- Coinbase reward: {block_data.get('tx', [{}])[0].get('vout', [{}])[0].get('value', 0) if block_data.get('tx') else 0} BTC

Please analyze this Bitcoin block and provide:
1. A concise headline (max 100 characters)
2. A brief summary (2-3 sentences) explaining what's notable about this block
3. Any interesting patterns or anomalies you notice

Focus on making it understandable for traders and analysts, not just technical details.
"""

def call_gemini_api(prompt, api_key):
    """Call Gemini API directly via HTTP"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    
    result = response.json()
    return result['candidates'][0]['content']['parts'][0]['text']

def main():
    print("🚀 Testing Gemini AI Integration\n")
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("\nMake sure it's in your .env file:")
        print("   GEMINI_API_KEY=your_key_here")
        return
    
    print(f"✅ API key found\n")
    
    # Get a recent block from Bitcoin
    print("🔗 Connecting to Bitcoin node...")
    try:
        rpc = BitcoinRPCClient()
        current_height = rpc.get_block_count()
        print(f"✅ Connected to Bitcoin node (height: {current_height:,})\n")
        
        # Get the latest block
        print(f"📦 Fetching block {current_height}...")
        block_hash = rpc.get_block_hash(current_height)
        block_data = rpc.get_block(block_hash, verbosity=2)
        print(f"✅ Block fetched: {block_hash[:16]}...\n")
        
    except Exception as e:
        print(f"❌ Failed to fetch block: {e}")
        return
    
    # Format block data for AI
    prompt = format_block_summary(block_data)
    
    print("🤖 Generating AI insight...")
    print("=" * 60)
    
    try:
        # Generate insight
        insight = call_gemini_api(prompt, api_key)
        
        print("\n✨ AI-Generated Insight:\n")
        print(insight)
        print("\n" + "=" * 60)
        
        # Show some stats
        print(f"\n📊 Stats:")
        print(f"   Block Height: {block_data.get('height'):,}")
        print(f"   Transactions: {len(block_data.get('tx', []))}")
        print(f"   Block Size: {block_data.get('size'):,} bytes")
        print(f"   Timestamp: {datetime.fromtimestamp(block_data.get('time')).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        print("\n✅ Test completed successfully!")
        print("\n💡 Next steps:")
        print("   - This insight could be stored in BigQuery")
        print("   - Posted to X (Twitter)")
        print("   - Displayed in the web frontend")
        print("   - Sent as email alerts to users")
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API request failed: {e}")
        print(f"Response: {e.response.text}")
        print("\nTroubleshooting:")
        print("1. Check your API key is valid")
        print("2. Verify you have quota for Gemini API calls")
        print("3. Make sure the API key has the right permissions")
    except Exception as e:
        print(f"\n❌ Failed to generate insight: {e}")

if __name__ == '__main__':
    main()
