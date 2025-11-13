#!/usr/bin/env python3
"""
Test backfill script with progress reporting to API
Simulates blockchain data processing for testing the dashboard
"""

import time
import requests
from datetime import datetime, timedelta
import random

API_URL = "http://localhost:8080"
JOB_ID = f"test_backfill_{int(time.time())}"

def create_job(start_block: int, end_block: int):
    """Create a new backfill job"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/monitoring/backfill",
            json={
                "job_id": JOB_ID,
                "status": "running",
                "start_block": start_block,
                "end_block": end_block,
                "current_block": start_block,
                "blocks_processed": 0,
                "blocks_remaining": end_block - start_block + 1,
                "progress_percent": 0.0,
                "rate_blocks_per_sec": 0.0,
                "started_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "error_count": 0
            }
        )
        response.raise_for_status()
        print(f"✅ Created job {JOB_ID}")
        return True
    except Exception as e:
        print(f"❌ Failed to create job: {e}")
        return False

def update_progress(current_block: int, blocks_processed: int, blocks_remaining: int, rate: float, error_count: int, start_block: int, end_block: int, started_at: str):
    """Update job progress"""
    try:
        progress_percent = (blocks_processed / (blocks_processed + blocks_remaining)) * 100 if (blocks_processed + blocks_remaining) > 0 else 0
        
        # Calculate ETA
        if rate > 0:
            seconds_remaining = blocks_remaining / rate
            eta = datetime.utcnow() + timedelta(seconds=seconds_remaining)
        else:
            eta = None
        
        payload = {
            "job_id": JOB_ID,
            "status": "running",
            "start_block": start_block,
            "end_block": end_block,
            "current_block": current_block,
            "blocks_processed": blocks_processed,
            "blocks_remaining": blocks_remaining,
            "progress_percent": progress_percent,
            "rate_blocks_per_sec": rate,
            "started_at": started_at,
            "updated_at": datetime.utcnow().isoformat(),
            "error_count": error_count
        }
        
        if eta:
            payload["estimated_completion"] = eta.isoformat()
        
        response = requests.put(
            f"{API_URL}/api/v1/monitoring/backfill/{JOB_ID}",
            json=payload
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"⚠️  Failed to update progress: {e}")
        return False

def complete_job(blocks_processed: int, error_count: int):
    """Mark job as completed"""
    try:
        response = requests.put(
            f"{API_URL}/api/v1/monitoring/backfill/{JOB_ID}",
            json={
                "job_id": JOB_ID,
                "status": "completed",
                "blocks_processed": blocks_processed,
                "blocks_remaining": 0,
                "progress_percent": 100.0,
                "updated_at": datetime.utcnow().isoformat(),
                "error_count": error_count
            }
        )
        response.raise_for_status()
        print(f"✅ Marked job {JOB_ID} as completed")
        return True
    except Exception as e:
        print(f"❌ Failed to complete job: {e}")
        return False

def main():
    """Run test backfill"""
    START_BLOCK = 870000
    END_BLOCK = 870100
    TOTAL_BLOCKS = END_BLOCK - START_BLOCK + 1
    
    print("🚀 Starting Test Backfill with Progress Tracking\n")
    print(f"📊 Configuration:")
    print(f"   Job ID: {JOB_ID}")
    print(f"   Start: {START_BLOCK:,}")
    print(f"   End: {END_BLOCK:,}")
    print(f"   Total: {TOTAL_BLOCKS:,} blocks")
    print(f"   API: {API_URL}\n")
    
    # Create job
    if not create_job(START_BLOCK, END_BLOCK):
        print("Failed to create job. Is the API running?")
        return
    
    print("📈 Processing blocks (simulated)...\n")
    
    start_time = time.time()
    started_at = datetime.utcnow().isoformat()
    blocks_processed = 0
    error_count = 0
    
    try:
        for height in range(START_BLOCK, END_BLOCK + 1):
            # Simulate processing time (0.1-0.3 seconds per block)
            time.sleep(random.uniform(0.1, 0.3))
            
            # Simulate occasional errors (5% chance)
            if random.random() < 0.05:
                error_count += 1
                print(f"⚠️  Simulated error at block {height}")
            
            blocks_processed += 1
            blocks_remaining = END_BLOCK - height
            
            # Calculate rate
            elapsed = time.time() - start_time
            rate = blocks_processed / elapsed if elapsed > 0 else 0
            
            # Update progress every 5 blocks
            if blocks_processed % 5 == 0 or blocks_remaining == 0:
                update_progress(height, blocks_processed, blocks_remaining, rate, error_count, START_BLOCK, END_BLOCK, started_at)
                
                progress = (blocks_processed / TOTAL_BLOCKS) * 100
                eta_seconds = blocks_remaining / rate if rate > 0 else 0
                
                print(f"Progress: {progress:.1f}% | Blocks: {blocks_processed:,}/{TOTAL_BLOCKS:,} | "
                      f"Rate: {rate:.1f}/sec | ETA: {eta_seconds:.0f}s | Errors: {error_count}")
        
        # Complete job
        complete_job(blocks_processed, error_count)
        
        elapsed = time.time() - start_time
        print(f"\n✅ Complete!")
        print(f"   Job ID: {JOB_ID}")
        print(f"   Blocks processed: {blocks_processed:,}")
        print(f"   Errors: {error_count}")
        print(f"   Time: {elapsed:.1f} seconds")
        print(f"   Rate: {blocks_processed/elapsed:.1f} blocks/sec")
        print(f"\n🌐 View in dashboard: http://localhost:3000/dashboard")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return
    except Exception as e:
        print(f"\n\n❌ Job failed: {e}")
        return

if __name__ == '__main__':
    main()
