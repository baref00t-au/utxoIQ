"""
Bitcoin block processor that transforms Bitcoin Core RPC data
into blockchain-etl compatible format for BigQuery with nested inputs/outputs.
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class BitcoinBlockProcessor:
    """Process Bitcoin blocks into blockchain-etl schema format with nested inputs/outputs."""
    
    @staticmethod
    def process_block(block_data: Dict) -> Dict:
        """
        Transform Bitcoin Core block data to blockchain-etl schema.
        
        Args:
            block_data: Raw block data from Bitcoin Core RPC
            
        Returns:
            Block data in blockchain-etl format
        """
        timestamp = datetime.fromtimestamp(block_data['time'])
        # BigQuery DATE fields need string format 'YYYY-MM-DD'
        timestamp_month = timestamp.date().replace(day=1).strftime('%Y-%m-%d')
        
        return {
            'hash': block_data['hash'],
            'size': block_data.get('size'),
            'stripped_size': block_data.get('strippedsize'),
            'weight': block_data.get('weight'),
            'number': block_data['height'],
            'version': block_data.get('version'),
            'merkle_root': block_data.get('merkleroot'),
            'timestamp': timestamp,
            'timestamp_month': timestamp_month,
            'nonce': str(block_data.get('nonce', '')),
            'bits': block_data.get('bits'),
            'coinbase_param': BitcoinBlockProcessor._extract_coinbase_param(
                block_data
            ),
            'transaction_count': block_data.get('nTx', len(block_data.get('tx', [])))
        }
    
    @staticmethod
    def process_transaction(
        tx_data: Dict,
        block_hash: str,
        block_number: int,
        block_timestamp: datetime
    ) -> Dict:
        """
        Transform Bitcoin Core transaction data to blockchain-etl schema with nested inputs/outputs.
        
        Args:
            tx_data: Raw transaction data from Bitcoin Core RPC
            block_hash: Parent block hash
            block_number: Parent block height
            block_timestamp: Block timestamp
            
        Returns:
            Transaction data in blockchain-etl format with nested inputs/outputs
        """
        is_coinbase = len(tx_data.get('vin', [])) > 0 and \
                     'coinbase' in tx_data['vin'][0]
        
        # Process inputs and outputs as nested arrays
        inputs = BitcoinBlockProcessor.process_inputs(tx_data)
        outputs = BitcoinBlockProcessor.process_outputs(tx_data)
        
        # Calculate input/output values from nested arrays
        input_value = sum(inp.get('value', 0) for inp in inputs)
        output_value = sum(out.get('value', 0) for out in outputs)
        
        # Fee is input - output (0 for coinbase)
        fee = 0 if is_coinbase else (input_value - output_value)
        
        # BigQuery DATE fields need string format 'YYYY-MM-DD'
        block_timestamp_month = block_timestamp.date().replace(day=1).strftime('%Y-%m-%d')
        
        return {
            'hash': tx_data['txid'],
            'size': tx_data.get('size'),
            'virtual_size': tx_data.get('vsize'),
            'version': tx_data.get('version'),
            'lock_time': tx_data.get('locktime'),
            'block_hash': block_hash,
            'block_number': block_number,
            'block_timestamp': block_timestamp,
            'block_timestamp_month': block_timestamp_month,
            'is_coinbase': is_coinbase,
            'input_count': len(inputs),
            'output_count': len(outputs),
            'input_value': input_value,
            'output_value': output_value,
            'fee': fee,
            'inputs': inputs,  # Nested RECORD array
            'outputs': outputs  # Nested RECORD array
        }
    
    @staticmethod
    def process_inputs(tx_data: Dict) -> List[Dict]:
        """
        Transform transaction inputs to blockchain-etl nested schema.
        
        Args:
            tx_data: Raw transaction data from Bitcoin Core RPC
            
        Returns:
            List of input data in blockchain-etl nested format
        """
        inputs = []
        
        for idx, vin in enumerate(tx_data.get('vin', [])):
            # Extract addresses from scriptPubKey
            addresses = []
            if 'prevout' in vin and 'scriptPubKey' in vin['prevout']:
                script_pub_key = vin['prevout']['scriptPubKey']
                if 'addresses' in script_pub_key:
                    addresses = script_pub_key['addresses']
                elif 'address' in script_pub_key:
                    addresses = [script_pub_key['address']]
            
            # Nested schema doesn't include transaction_hash or block_timestamp
            input_data = {
                'index': idx,
                'spent_transaction_hash': vin.get('txid'),
                'spent_output_index': vin.get('vout'),
                'script_asm': vin.get('scriptSig', {}).get('asm'),
                'script_hex': vin.get('scriptSig', {}).get('hex'),
                'sequence': vin.get('sequence'),
                'required_signatures': None,  # Not available in Bitcoin Core
                'type': vin.get('prevout', {}).get('scriptPubKey', {}).get('type'),
                'addresses': addresses,
                'value': int(vin.get('prevout', {}).get('value', 0) * 100_000_000)
            }
            
            inputs.append(input_data)
        
        return inputs
    
    @staticmethod
    def process_outputs(tx_data: Dict) -> List[Dict]:
        """
        Transform transaction outputs to blockchain-etl nested schema.
        
        Args:
            tx_data: Raw transaction data from Bitcoin Core RPC
            
        Returns:
            List of output data in blockchain-etl nested format
        """
        outputs = []
        
        for idx, vout in enumerate(tx_data.get('vout', [])):
            script_pub_key = vout.get('scriptPubKey', {})
            
            # Extract addresses
            addresses = []
            if 'addresses' in script_pub_key:
                addresses = script_pub_key['addresses']
            elif 'address' in script_pub_key:
                addresses = [script_pub_key['address']]
            
            # Nested schema doesn't include transaction_hash or block_timestamp
            output_data = {
                'index': idx,
                'script_asm': script_pub_key.get('asm'),
                'script_hex': script_pub_key.get('hex'),
                'required_signatures': script_pub_key.get('reqSigs'),
                'type': script_pub_key.get('type'),
                'addresses': addresses,
                'value': int(vout.get('value', 0) * 100_000_000)  # BTC to satoshis
            }
            
            outputs.append(output_data)
        
        return outputs
    
    @staticmethod
    def _extract_coinbase_param(block_data: Dict) -> Optional[str]:
        """
        Extract coinbase parameter from block data.
        
        Args:
            block_data: Raw block data from Bitcoin Core RPC
            
        Returns:
            Coinbase parameter or None
        """
        try:
            if 'tx' in block_data and len(block_data['tx']) > 0:
                coinbase_tx = block_data['tx'][0]
                if 'vin' in coinbase_tx and len(coinbase_tx['vin']) > 0:
                    return coinbase_tx['vin'][0].get('coinbase')
        except (KeyError, IndexError):
            pass
        
        return None
