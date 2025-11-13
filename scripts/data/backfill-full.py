#!/usr/bin/env python3
"""
Full backfill script for blocks, transactions, and UTXOs
Starts from block 900,000 for MVP
"""

import os
import sys
import time
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'data-ingestion', 'src'))

from dotenv import load_dotenv
load_dotenv()

from bitcoin_rpc import BitcoinRPCClient
from bigquery_client import BigQueryClient

SATOSHI = Decimal('100000000')

def satoshi_to_btc(satoshi):
    """Convert satoshi to BTC"""
    return Decimal(satoshi) / SATOSHI

class FullBackfiller:
    """Backfill blocks, transactions, and UTXOs"""
    
    def __init__(self, batch_size=50):
        self.rpc = BitcoinRPCClient()
        self.bq = BigQueryClient()
        self.batch_size = batch_size
        
        self.blocks_batch = []
        self.transactions_batch = []
        self.utxos_batch = []
        
        self.blocks_processed = 0
        self.transactions_processed = 0
        self.utxos_processed = 0
    
    def process_block(self, height):
        """Process a single block with all its transactions and UTXOs"""
        try:
            # Fetch block
            block_hash = self.rpc.get_block_hash(height)
            block_data = self.rpc.get_block(block_hash, verbosity=2)
            
            block_time = datetime.fromtimestamp(block_data.get("time"))
            
            # Process block
            block_row = {
                "block_hash": block_data.get("hash"),
                "height": block_data.get("height"),
                "timestamp": block_time.isoformat(),
                "size": block_data.get("size"),
                "tx_count": len(block_data.get("tx", [])),
                "fees_total": 0,  # Will calculate from transactions
            }
            
            total_fees = Decimal('0')
            
            # Process transactions
            for tx in block_data.get("tx", []):
                tx_row, tx_fee, utxos = self.process_transaction(tx, height, block_hash, block_time)
                
                self.transactions_batch.append(tx_row)
                self.utxos_batch.extend(utxos)
                
                total_fees += tx_fee
                self.transactions_processed += 1
                self.utxos_processed += len(utxos)
            
            block_row["fees_total"] = int(total_fees * SATOSHI)
            self.blocks_batch.append(block_row)
            self.blocks_processed += 1
            
            return True
            
        except Exception as e:
            print(f"❌ Error processing block {height}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_transaction(self, tx, block_height, block_hash, block_time):
        """Process a transaction and its UTXOs"""
        txid = tx.get("txid")
        is_coinbase = "coinbase" in tx.get("vin", [{}])[0]
        
        # Calculate input/output values
        input_value = Decimal('0')
        output_value = Decimal('0')
        
        # Process outputs (create UTXOs)
        utxos = []
        for vout in tx.get("vout", []):
            value_btc = Decimal(str(vout.get("value", 0)))
            output_value += value_btc
            
            script_pub_key = vout.get("scriptPubKey", {})
            address = script_pub_key.get("address") or script_pub_key.get("addresses", [None])[0]
            
            utxo = {
                "txid": txid,
                "vout": vout.get("n"),
                "block_height": block_height,
                "timestamp": block_time.isoformat(),
                "value": float(value_btc),
                "address": address,
                "script_type": script_pub_key.get("type", "unknown"),
                "script_pubkey": script_pub_key.get("hex", ""),
                "spent": False,
                "spent_txid": None,
                "spent_block_height": None,
                "spent_timestamp": None,
                "lifespan_blocks": None,
                "is_coinbase": is_coinbase,
            }
            utxos.append(utxo)
        
        # Calculate input value (skip for coinbase)
        # Note: Bitcoin RPC doesn't include input values directly
        # For MVP, we'll estimate from outputs for non-coinbase txs
        if not is_coinbase:
            # Estimate: inputs ≈ outputs + fee (we'll use a small default fee)
            input_value = output_value + Decimal('0.0001')  # Assume small fee
        
        # Calculate fee
        fee = input_value - output_value if not is_coinbase else Decimal('0')
        
        # Ensure fee is non-negative (data quality check)
        if fee < 0:
            fee = Decimal('0')
            input_value = output_value
        
        # Calculate fee rate (round to 2 decimal places for sat/vB)
        vsize = tx.get("vsize", tx.get("size", 1))
        fee_rate = round(float((fee * SATOSHI) / Decimal(vsize)), 2) if vsize > 0 and fee > 0 else 0
        
        tx_row = {
            "txid": txid,
            "block_height": block_height,
            "block_hash": block_hash,
            "timestamp": block_time.isoformat(),
            "version": tx.get("version"),
            "size": tx.get("size"),
            "vsize": vsize,
            "weight": tx.get("weight", tx.get("size", 0) * 4),
            "locktime": tx.get("locktime"),
            "input_count": len(tx.get("vin", [])),
            "output_count": len(tx.get("vout", [])),
            "input_value": float(input_value),
            "output_value": float(output_value),
            "fee": float(fee),
            "fee_rate": fee_rate,
            "is_coinbase": is_coinbase,
        }
        
        return tx_row, fee, utxos
    
    def flush_batches(self):
        """Write all batches to BigQuery"""
        try:
            if self.blocks_batch:
                self.bq.stream_blocks(self.blocks_batch)
                self.blocks_batch = []
            
            if self.transactions_batch:
                # Write transactions
                table = f"{self.bq.project_id}.btc.transactions"
                job = self.bq.client.load_table_from_json(self.transactions_batch, table)
                job.result()
                self.transactions_batch = []
            
            if self.utxos_batch:
                # Write UTXOs
                table = f"{self.bq.project_id}.btc.utxos"
                job = self.bq.client.load_table_from_json(self.utxos_batch, table)
                job.result()
                self.utxos_batch = []
                
        except Exception as e:
            print(f"\n❌ Error flushing batches: {e}")
            # Print first few rows for debugging
            if self.transactions_batch:
                print(f"Sample transaction: {self.transactions_batch[0]}")
            if self.utxos_batch:
                print(f"Sample UTXO: {self.utxos_batch[0]}")
            raise
    
    def run(self, start_height, end_height=None):
        """Run the backfill"""
        current_height = self.rpc.get_block_count()
        end_height = end_height if end_height else current_height
        
        print(f"🚀 Full Backfill Starting\n")
        print(f"📊 Configuration:")
        print(f"   Start: {start_height:,}")
        print(f"   End: {end_height:,}")
        print(f"   Total: {end_height - start_height + 1:,} blocks")
        print(f"   Batch size: {self.batch_size}\n")
        
        response = input("Proceed? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled")
            return
        
        start_time = time.time()
        
        try:
            for height in range(start_height, end_height + 1):
                self.process_block(height)
                
                # Flush batches periodically
                if len(self.blocks_batch) >= self.batch_size:
                    self.flush_batches()
                    
                    elapsed = time.time() - start_time
                    rate = self.blocks_processed / elapsed if elapsed > 0 else 0
                    progress = ((height - start_height + 1) / (end_height - start_height + 1)) * 100
                    
                    print(f"Progress: {progress:.1f}% | "
                          f"Blocks: {self.blocks_processed:,} | "
                          f"Txs: {self.transactions_processed:,} | "
                          f"UTXOs: {self.utxos_processed:,} | "
                          f"Rate: {rate:.1f} blocks/sec")
            
            # Flush remaining
            self.flush_batches()
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            self.flush_batches()
        
        elapsed = time.time() - start_time
        print(f"\n✅ Complete!")
        print(f"   Blocks: {self.blocks_processed:,}")
        print(f"   Transactions: {self.transactions_processed:,}")
        print(f"   UTXOs: {self.utxos_processed:,}")
        print(f"   Time: {elapsed/60:.1f} minutes")
        print(f"   Rate: {self.blocks_processed/elapsed:.1f} blocks/sec")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Full backfill from block 900,000')
    parser.add_argument('--start', type=int, default=900000, help='Starting block (default: 900000)')
    parser.add_argument('--end', type=int, help='Ending block (default: current tip)')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size (default: 50)')
    args = parser.parse_args()
    
    backfiller = FullBackfiller(batch_size=args.batch_size)
    backfiller.run(args.start, args.end)

if __name__ == '__main__':
    main()
