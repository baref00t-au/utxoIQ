#!/usr/bin/env python3
"""
Enhanced backfill script with progress reporting to API
"""

import os
import sys
import time
import uuid
import requests
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'data-ingestion', 'src'))

from dotenv import load_dotenv
load_dotenv()

from bitcoin_rpc import BitcoinRPCClient
from bigquery_client import BigQueryClient


class ProgressReporter:
    """Reports backfill progress to the API"""
    
    def __init__(self, api_url: str, job_id: str):
        self.api_url = api_url
        self.job_id = job_id
        self.session = requests.Session()
    
    def create_job(self, start_block: int, end_block: int):
        """Create a new backfill job"""
        try:
            response = self.session.post(
                f"{self.api_url}/api/v1/monitoring/backfill",
                json={
                    "job_id": self.job_id,
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
            print(f"✓ Created job {self.job_id}")
        except Exception as e:
            print(f"⚠️  Failed to create job: {e}")
    
    def update_progress(
        self,
        current_block: int,
        blocks_processed: int,
        blocks_remaining: int,
        rate: float,
        error_count: int,
        estimated_completion: Optional[datetime] = None
    ):
        """Update job progress"""
        try:
            progress_percent = (blocks_processed / (blocks_processed + blocks_remaining)) * 100
            
            payload = {
                "job_id": self.job_id,
                "status": "running",
                "current_block": current_block,
                "blocks_processed": blocks_processed,
                "blocks_remaining": blocks_remaining,
                "progress_percent": progress_percent,
                "rate_blocks_per_sec": rate,
                "updated_at": datetime.utcnow().isoformat(),
                "error_count": error_count
            }
            
            if estimated_completion:
                payload["estimated_completion"] = estimated_completion.isoformat()
            
            response = self.session.put(
                f"{self.api_url}/api/v1/monitoring/backfill/{self.job_id}",
                json=payload
            )
            response.raise_for_status()
        except Exception as e:
            # Don't fail the backfill if progress reporting fails
            pass
    
    def complete_job(self, blocks_processed: int, error_count: int):
        """Mark job as completed"""
        try:
            response = self.session.put(
                f"{self.api_url}/api/v1/monitoring/backfill/{self.job_id}",
                json={
                    "job_id": self.job_id,
                    "status": "completed",
                    "blocks_processed": blocks_processed,
                    "blocks_remaining": 0,
                    "progress_percent": 100.0,
                    "updated_at": datetime.utcnow().isoformat(),
                    "error_count": error_count
                }
            )
            response.raise_for_status()
            print(f"✓ Marked job {self.job_id} as completed")
        except Exception as e:
            print(f"⚠️  Failed to complete job: {e}")
    
    def fail_job(self, error_message: str):
        """Mark job as failed"""
        try:
            response = self.session.put(
                f"{self.api_url}/api/v1/monitoring/backfill/{self.job_id}",
                json={
                    "job_id": self.job_id,
                    "status": "failed",
                    "updated_at": datetime.utcnow().isoformat(),
                    "error_message": error_message
                }
            )
            response.raise_for_status()
        except Exception as e:
            print(f"⚠️  Failed to update job status: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Backfill Bitcoin blocks with progress tracking')
    parser.add_argument('--start', type=int, required=True, help='Starting block height')
    parser.add_argument('--end', type=int, help='Ending block height (default: current tip)')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size (default: 100)')
    parser.add_argument('--api-url', type=str, default='http://localhost:8000', help='API URL')
    parser.add_argument('--report-interval', type=int, default=10, help='Progress report interval (batches)')
    args = parser.parse_args()
    
    print("🚀 Starting BigQuery Backfill with Progress Tracking\n")
    
    # Initialize clients
    rpc = BitcoinRPCClient()
    bq = BigQueryClient()
    
    # Generate job ID
    job_id = f"backfill_{args.start}_{int(time.time())}"
    reporter = ProgressReporter(args.api_url, job_id)
    
    current_height = rpc.get_block_count()
    end_height = args.end if args.end else current_height
    total_blocks = end_height - args.start + 1
    
    print(f"📊 Configuration:")
    print(f"   Job ID: {job_id}")
    print(f"   Start: {args.start:,}")
    print(f"   End: {end_height:,}")
    print(f"   Total: {total_blocks:,} blocks")
    print(f"   Batch size: {args.batch_size}")
    print(f"   API: {args.api_url}\n")
    
    response = input("Proceed? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cancelled")
        return
    
    # Create job in API
    reporter.create_job(args.start, end_height)
    
    start_time = time.time()
    blocks_processed = 0
    error_count = 0
    batch = []
    batch_count = 0
    
    try:
        for height in range(args.start, end_height + 1):
            try:
                # Fetch block
                block_hash = rpc.get_block_hash(height)
                block_data = rpc.get_block(block_hash, verbosity=2)
                
                # Prepare for BigQuery
                block_row = {
                    "block_hash": block_data.get("hash"),
                    "height": block_data.get("height"),
                    "timestamp": datetime.fromtimestamp(block_data.get("time")).isoformat(),
                    "size": block_data.get("size"),
                    "tx_count": len(block_data.get("tx", [])),
                    "fees_total": 0,
                }
                
                batch.append(block_row)
                blocks_processed += 1
                
                # Write batch when full
                if len(batch) >= args.batch_size:
                    bq.stream_blocks(batch)
                    batch_count += 1
                    
                    elapsed = time.time() - start_time
                    rate = blocks_processed / elapsed if elapsed > 0 else 0
                    blocks_remaining = end_height - height
                    progress = (blocks_processed / total_blocks) * 100
                    
                    # Calculate ETA
                    if rate > 0:
                        seconds_remaining = blocks_remaining / rate
                        eta = datetime.utcnow() + timedelta(seconds=seconds_remaining)
                    else:
                        eta = None
                    
                    # Report progress to API
                    if batch_count % args.report_interval == 0:
                        reporter.update_progress(
                            current_block=height,
                            blocks_processed=blocks_processed,
                            blocks_remaining=blocks_remaining,
                            rate=rate,
                            error_count=error_count,
                            estimated_completion=eta
                        )
                    
                    # Console output
                    print(f"Progress: {progress:.1f}% | Blocks: {blocks_processed:,}/{total_blocks:,} | "
                          f"Rate: {rate:.1f}/sec | Errors: {error_count}")
                    
                    batch = []
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted by user")
                raise
            except Exception as e:
                print(f"❌ Error at block {height}: {e}")
                error_count += 1
                continue
        
        # Write remaining batch
        if batch:
            bq.stream_blocks(batch)
        
        # Mark job as completed
        reporter.complete_job(blocks_processed, error_count)
        
        elapsed = time.time() - start_time
        print(f"\n✅ Complete!")
        print(f"   Job ID: {job_id}")
        print(f"   Blocks processed: {blocks_processed:,}")
        print(f"   Errors: {error_count}")
        print(f"   Time: {elapsed/60:.1f} minutes")
        print(f"   Rate: {blocks_processed/elapsed:.1f} blocks/sec")
        
    except KeyboardInterrupt:
        reporter.fail_job("Interrupted by user")
        print("\n\n⚠️  Job cancelled")
        sys.exit(1)
    except Exception as e:
        reporter.fail_job(str(e))
        print(f"\n\n❌ Job failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
