"""
Unit tests for Bitcoin RPC client and data processing
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.bitcoin_rpc import (
    BitcoinRPCClient,
    BlockDataNormalizer,
    MempoolAnalyzer,
    ReorgDetector
)


class TestBitcoinRPCClient(unittest.TestCase):
    """Test Bitcoin RPC client"""
    
    def setUp(self):
        self.client = BitcoinRPCClient(
            host='localhost',
            port=8332,
            user='test',
            password='test'
        )
    
    @patch('src.bitcoin_rpc.requests.post')
    def test_get_block_count(self, mock_post):
        """Test getting block count"""
        mock_response = Mock()
        mock_response.json.return_value = {'result': 800000, 'error': None}
        mock_post.return_value = mock_response
        
        result = self.client.get_block_count()
        self.assertEqual(result, 800000)
    
    @patch('src.bitcoin_rpc.requests.post')
    def test_get_block_hash(self, mock_post):
        """Test getting block hash"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'result': '00000000000000000001234567890abcdef',
            'error': None
        }
        mock_post.return_value = mock_response
        
        result = self.client.get_block_hash(800000)
        self.assertEqual(result, '00000000000000000001234567890abcdef')


class TestBlockDataNormalizer(unittest.TestCase):
    """Test block data normalization"""
    
    def test_normalize_block(self):
        """Test normalizing block data"""
        raw_block = {
            'hash': '00000000000000000001234567890abcdef',
            'height': 800000,
            'time': 1704067200,
            'size': 1500000,
            'tx': [
                {'fee': 0.0001},
                {'fee': 0.0002}
            ]
        }
        
        normalized = BlockDataNormalizer.normalize_block(raw_block)
        
        self.assertEqual(normalized['block_hash'], '00000000000000000001234567890abcdef')
        self.assertEqual(normalized['height'], 800000)
        self.assertEqual(normalized['timestamp'], 1704067200)
        self.assertEqual(normalized['size'], 1500000)
        self.assertEqual(normalized['tx_count'], 2)
        self.assertEqual(normalized['fees_total'], 30000)  # 0.0003 BTC in satoshis


class TestMempoolAnalyzer(unittest.TestCase):
    """Test mempool anomaly detection"""
    
    def setUp(self):
        self.analyzer = MempoolAnalyzer()
    
    def test_analyze_mempool_normal(self):
        """Test mempool analysis with normal conditions"""
        mempool_info = {
            'size': 50000,
            'bytes': 100000000,
            'total_fee': 1.5
        }
        
        result = self.analyzer.analyze_mempool(mempool_info)
        
        self.assertEqual(result['current_size'], 50000)
        self.assertEqual(result['current_bytes'], 100000000)
        self.assertGreater(result['avg_fee_rate'], 0)
        self.assertEqual(len(result['anomalies']), 0)
    
    def test_detect_mempool_spike(self):
        """Test detection of mempool size spike"""
        # Build history with normal values
        for _ in range(20):
            self.analyzer.analyze_mempool({
                'size': 50000,
                'bytes': 100000000,
                'total_fee': 1.0
            })
        
        # Introduce spike (3+ standard deviations)
        result = self.analyzer.analyze_mempool({
            'size': 200000,  # Significant spike
            'bytes': 400000000,
            'total_fee': 4.0
        })
        
        self.assertGreater(len(result['anomalies']), 0)
        self.assertTrue(any(a['type'] == 'mempool_spike' for a in result['anomalies']))
    
    def test_detect_fee_spike(self):
        """Test detection of fee rate spike"""
        # Build history with normal fee rates
        for _ in range(20):
            self.analyzer.analyze_mempool({
                'size': 50000,
                'bytes': 100000000,
                'total_fee': 1.0
            })
        
        # Introduce fee spike
        result = self.analyzer.analyze_mempool({
            'size': 50000,
            'bytes': 100000000,
            'total_fee': 10.0  # 10x normal fee
        })
        
        self.assertGreater(len(result['anomalies']), 0)
        self.assertTrue(any(a['type'] == 'fee_spike' for a in result['anomalies']))


class TestReorgDetector(unittest.TestCase):
    """Test blockchain reorganization detection"""
    
    def setUp(self):
        self.detector = ReorgDetector()
    
    def test_no_reorg_normal_chain(self):
        """Test normal chain progression without reorg"""
        block1 = {
            'height': 800000,
            'hash': 'hash1',
            'previousblockhash': 'hash0'
        }
        block2 = {
            'height': 800001,
            'hash': 'hash2',
            'previousblockhash': 'hash1'
        }
        
        result1 = self.detector.check_for_reorg(block1)
        result2 = self.detector.check_for_reorg(block2)
        
        self.assertIsNone(result1)
        self.assertIsNone(result2)
    
    def test_detect_reorg(self):
        """Test detection of blockchain reorg"""
        # Normal chain
        block1 = {
            'height': 800000,
            'hash': 'hash1',
            'previousblockhash': 'hash0'
        }
        block2 = {
            'height': 800001,
            'hash': 'hash2',
            'previousblockhash': 'hash1'
        }
        
        self.detector.check_for_reorg(block1)
        self.detector.check_for_reorg(block2)
        
        # Reorg: new block at same height with different previous hash
        block2_alt = {
            'height': 800001,
            'hash': 'hash2_alt',
            'previousblockhash': 'hash1_alt'  # Different previous hash
        }
        
        result = self.detector.check_for_reorg(block2_alt)
        
        # Note: This is a simplified test. In reality, reorg detection
        # requires more sophisticated logic
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
