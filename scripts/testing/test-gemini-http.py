#!/usr/bin/env python3
"""
Test Gemini AI using direct HTTP requests (no protobuf dependency)
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

from bitcoin_rpc import BitcoinRPCClient

def generate_insight(api_key, prompt):
    """Call Gemini API directly via HTTP"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
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

def format_block_summary(block_data):
    """Format block data for AI analysis"""
    return f"""
Bitcoin Block Analysis Request:

Block Height: {block_data.get('height')}
Block Hash: {block_data.get('hash')}
Timestamp: {datetime.fromtimestamp(block_data.get('time')).strftime('%Y-%m-%d %H:%M:%S UTC')}
Number of Transactions: {len(block_data.get('tx', []))}
Block Size: {block_data.get('size'):,} bytes

Please analyze this Bitcoin block and provide:
1. A concise headline (max 100 characters)
2. A brief summary (2-3 sentences) explaining what's notable about this block

Focus on making it understandable for traders and analysts.
"""

def main():
    print("🚀 Testing Gemini AI Integration (Direct HTTP)\n")
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
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
        insight = generate_insight(api_key, prompt)
        
        print("\n✨ AI-Generated Insight:\n")
        print(insight)
        print("\n" + "=" * 60)
        
        # Show some stats
        print(f"\n📊 Block Stats:")
        print(f"   Height: {block_data.get('height'):,}")
        print(f"   Transactions: {len(block_data.get('tx', []))}")
        print(f"   Size: {block_data.get('size'):,} bytes")
        print(f"   Time: {datetime.fromtimestamp(block_data.get('time')).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        print("\n✅ SUCCESS! Your first AI-generated blockchain insight!")
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Failed: {e}")

if __name__ == '__main__':
    main()
