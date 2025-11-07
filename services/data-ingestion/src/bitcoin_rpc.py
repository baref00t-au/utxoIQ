"""
Bitcoin Core RPC client for blockchain data ingestion
Handles connection to Bitcoin Core node and data streaming
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class BitcoinRPCClient:
    """Client for interacting with Bitcoin Core RPC interface"""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        user: str = None,
        password: str = None
    ):
        self.host = host or os.getenv('BITCOIN_RPC_HOST', 'localhost')
        self.port = port or int(os.getenv('BITCOIN_RPC_PORT', '8332'))
        self.user = user or os.getenv('BITCOIN_RPC_USER', 'bitcoin')
        self.password = password or os.getenv('BITCOIN_RPC_PASSWORD', '')
        self.url = f"http://{self.host}:{self.port}"
        self.auth = HTTPBasicAuth(self.user, self.password)
        self.request_id = 0
        
    def _call(self, method: str, params: List = None) -> Any:
        """Make RPC call to Bitcoin Core"""
        self.request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or []
        }
        
        try:
            response = requests.post(
                self.url,
                json=payload,
                auth=self.auth,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result and result['error']:
                raise Exception(f"RPC Error: {result['error']}")
                
            return result.get('result')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Bitcoin RPC call failed: {method} - {str(e)}")
            raise
    
    def get_blockchain_info(self) -> Dict:
        """Get blockchain information"""
        return self._call('getblockchaininfo')
    
    def get_block_count(self) -> int:
        """Get current block height"""
        return self._call('getblockcount')
    
    def get_block_hash(self, height: int) -> str:
        """Get block hash at specific height"""
        return self._call('getblockhash', [height])
    
    def get_block(self, block_hash: str, verbosity: int = 2) -> Dict:
        """
        Get block data
        verbosity: 0=hex, 1=json without tx, 2=json with tx details
        """
        return self._call('getblock', [block_hash, verbosity])
    
    def get_raw_mempool(self, verbose: bool = True) -> Dict:
        """Get mempool contents"""
        return self._call('getrawmempool', [verbose])
    
    def get_mempool_info(self) -> Dict:
        """Get mempool statistics"""
        return self._call('getmempoolinfo')
    
    def get_transaction(self, txid: str, verbose: bool = True) -> Dict:
        """Get transaction details"""
        return self._call('getrawtransaction', [txid, verbose])
    
    def estimate_smart_fee(self, conf_target: int = 6) -> Dict:
        """Estimate fee for confirmation target"""
        return self._call('estimatesmartfee', [conf_target])


class BlockDataNormalizer:
    """Normalizes raw Bitcoin block data for storage"""
    
    @staticmethod
    def normalize_block(raw_block: Dict) -> Dict:
        """Convert raw block data to normalized format"""
        return {
            'block_hash': raw_block['hash'],
            'height': raw_block['height'],
            'timestamp': raw_block['time'],
            'size': raw_block['size'],
            'tx_count': len(raw_block.get('tx', [])),
            'fees_total': BlockDataNormalizer._calculate_total_fees(raw_block)
        }
    
    @staticmethod
    def _calculate_total_fees(block: Dict) -> int:
        """Calculate total fees in block (satoshis)"""
        total_fees = 0
        for tx in block.get('tx', []):
            if 'fee' in tx:
                # Fee is in BTC, convert to satoshis
                total_fees += int(Decimal(str(tx['fee'])) * Decimal('100000000'))
        return total_fees
    
    @staticmethod
    def normalize_transaction(raw_tx: Dict, block_height: int) -> Dict:
        """Convert raw transaction data to normalized format"""
        return {
            'tx_hash': raw_tx['txid'],
            'block_height': block_height,
            'input_count': len(raw_tx.get('vin', [])),
            'output_count': len(raw_tx.get('vout', [])),
            'fee': int(Decimal(str(raw_tx.get('fee', 0))) * Decimal('100000000')),
            'size': raw_tx.get('size', 0),
            'vsize': raw_tx.get('vsize', 0),
            'weight': raw_tx.get('weight', 0)
        }


class MempoolAnalyzer:
    """Analyzes mempool data for anomaly detection"""
    
    def __init__(self):
        self.fee_history: List[float] = []
        self.size_history: List[int] = []
        self.max_history_size = 144  # ~24 hours of blocks
    
    def analyze_mempool(self, mempool_info: Dict) -> Dict:
        """Analyze mempool for anomalies"""
        current_size = mempool_info.get('size', 0)
        current_bytes = mempool_info.get('bytes', 0)
        
        # Calculate average fee rate
        avg_fee_rate = 0
        if current_bytes > 0:
            total_fee = mempool_info.get('total_fee', 0)
            avg_fee_rate = (total_fee * 100000000) / current_bytes  # sat/byte
        
        # Update history
        self.fee_history.append(avg_fee_rate)
        self.size_history.append(current_size)
        
        # Trim history
        if len(self.fee_history) > self.max_history_size:
            self.fee_history = self.fee_history[-self.max_history_size:]
        if len(self.size_history) > self.max_history_size:
            self.size_history = self.size_history[-self.max_history_size:]
        
        # Detect anomalies
        anomalies = self._detect_anomalies(current_size, avg_fee_rate)
        
        return {
            'current_size': current_size,
            'current_bytes': current_bytes,
            'avg_fee_rate': avg_fee_rate,
            'anomalies': anomalies
        }
    
    def _detect_anomalies(self, current_size: int, current_fee: float) -> List[Dict]:
        """Detect mempool anomalies using 3 standard deviations threshold"""
        anomalies = []
        
        # Size spike detection
        if len(self.size_history) >= 10:
            mean_size = sum(self.size_history) / len(self.size_history)
            variance = sum((x - mean_size) ** 2 for x in self.size_history) / len(self.size_history)
            std_dev = variance ** 0.5
            
            if current_size > mean_size + (3 * std_dev):
                anomalies.append({
                    'type': 'mempool_spike',
                    'severity': 'high',
                    'description': f'Mempool size spike detected: {current_size} txs (mean: {mean_size:.0f}, threshold: {mean_size + 3*std_dev:.0f})',
                    'value': current_size,
                    'threshold': mean_size + (3 * std_dev)
                })
        
        # Fee spike detection
        if len(self.fee_history) >= 10:
            mean_fee = sum(self.fee_history) / len(self.fee_history)
            variance = sum((x - mean_fee) ** 2 for x in self.fee_history) / len(self.fee_history)
            std_dev = variance ** 0.5
            
            if current_fee > mean_fee + (3 * std_dev):
                anomalies.append({
                    'type': 'fee_spike',
                    'severity': 'high',
                    'description': f'Fee rate spike detected: {current_fee:.2f} sat/byte (mean: {mean_fee:.2f}, threshold: {mean_fee + 3*std_dev:.2f})',
                    'value': current_fee,
                    'threshold': mean_fee + (3 * std_dev)
                })
        
        return anomalies


class ReorgDetector:
    """Detects blockchain reorganizations beyond 1 block depth"""
    
    def __init__(self):
        self.block_history: List[Dict] = []
        self.max_depth = 10  # Monitor up to 10 blocks deep
    
    def check_for_reorg(self, current_block: Dict) -> Optional[Dict]:
        """Check if a blockchain reorg has occurred"""
        current_height = current_block['height']
        current_hash = current_block['hash']
        
        # Add current block to history
        self.block_history.append({
            'height': current_height,
            'hash': current_hash,
            'prev_hash': current_block.get('previousblockhash')
        })
        
        # Trim history
        if len(self.block_history) > self.max_depth:
            self.block_history = self.block_history[-self.max_depth:]
        
        # Check for reorg
        if len(self.block_history) >= 2:
            prev_block = self.block_history[-2]
            
            # If current block's previous hash doesn't match previous block's hash
            if current_block.get('previousblockhash') != prev_block['hash']:
                reorg_depth = self._calculate_reorg_depth()
                
                if reorg_depth > 1:
                    return {
                        'detected': True,
                        'depth': reorg_depth,
                        'old_tip': prev_block['hash'],
                        'new_tip': current_hash,
                        'height': current_height
                    }
        
        return None
    
    def _calculate_reorg_depth(self) -> int:
        """Calculate depth of reorganization"""
        # Simple implementation: count consecutive mismatches
        depth = 1
        for i in range(len(self.block_history) - 2, -1, -1):
            if i > 0:
                if self.block_history[i]['prev_hash'] != self.block_history[i-1]['hash']:
                    depth += 1
                else:
                    break
        return depth
