"""
Unit tests for confidence scoring and filtering
"""

import pytest
from src.generators.confidence_scorer import (
    ConfidenceScorer,
    ConfidenceLevel,
    ConfidenceFactors,
    ConfidenceScore
)


class TestConfidenceScorer:
    """Test confidence scoring functionality"""
    
    def test_calculate_confidence_high(self):
        """Test high confidence calculation"""
        score = ConfidenceScorer.calculate_confidence(
            signal_strength=0.9,
            historical_accuracy=0.85,
            data_quality=0.95
        )
        
        assert score.score >= 0.85
        assert score.level == ConfidenceLevel.HIGH
        assert score.should_publish is True
    
    def test_calculate_confidence_medium(self):
        """Test medium confidence calculation"""
        score = ConfidenceScorer.calculate_confidence(
            signal_strength=0.7,
            historical_accuracy=0.75,
            data_quality=0.8
        )
        
        assert 0.70 <= score.score < 0.85
        assert score.level == ConfidenceLevel.MEDIUM
        assert score.should_publish is True
    
    def test_calculate_confidence_low(self):
        """Test low confidence calculation"""
        score = ConfidenceScorer.calculate_confidence(
            signal_strength=0.4,
            historical_accuracy=0.5,
            data_quality=0.6
        )
        
        assert score.score < 0.70
        assert score.level == ConfidenceLevel.LOW
        assert score.should_publish is False
    
    def test_calculate_confidence_with_anomaly(self):
        """Test confidence calculation with anomaly penalty"""
        score_normal = ConfidenceScorer.calculate_confidence(
            signal_strength=0.9,
            historical_accuracy=0.85,
            data_quality=0.95,
            is_anomaly=False
        )
        
        score_anomaly = ConfidenceScorer.calculate_confidence(
            signal_strength=0.9,
            historical_accuracy=0.85,
            data_quality=0.95,
            is_anomaly=True
        )
        
        assert score_anomaly.score < score_normal.score
        assert score_anomaly.should_publish is False  # Anomaly prevents publication
    
    def test_calculate_mempool_strength(self):
        """Test mempool signal strength calculation"""
        signal_data = {
            'change_24h': 50.0,
            'is_anomaly': False
        }
        
        strength = ConfidenceScorer._calculate_mempool_strength(signal_data)
        
        assert 0.0 <= strength <= 1.0
        assert strength == 0.5  # 50% change = 0.5 strength
    
    def test_calculate_exchange_strength(self):
        """Test exchange flow signal strength calculation"""
        signal_data = {
            'std_dev_multiple': 2.5,
            'anomaly_score': 0.7
        }
        
        strength = ConfidenceScorer._calculate_exchange_strength(signal_data)
        
        assert 0.0 <= strength <= 1.0
        assert strength > 0.8  # 2.5 std devs = high strength
    
    def test_calculate_data_quality_complete(self):
        """Test data quality calculation with complete data"""
        signal_data = {
            'block_height': 800000,
            'signal_strength': 0.8,
            'transaction_ids': ['tx1', 'tx2', 'tx3']
        }
        
        quality = ConfidenceScorer.calculate_data_quality(signal_data)
        
        assert quality == 1.0
    
    def test_calculate_data_quality_incomplete(self):
        """Test data quality calculation with incomplete data"""
        signal_data = {
            'block_height': 800000,
            # Missing signal_strength
            'transaction_ids': []  # Empty transactions
        }
        
        quality = ConfidenceScorer.calculate_data_quality(signal_data)
        
        assert quality < 1.0
    
    def test_detect_quiet_mode_mempool_spike(self):
        """Test quiet mode detection for mempool spike"""
        signal_data = {
            'change_24h': 350.0,  # Extreme change
            'is_anomaly': True,
            'std_dev_multiple': 4.0
        }
        
        should_quiet, reason = ConfidenceScorer.detect_quiet_mode(signal_data, 'mempool')
        
        assert should_quiet is True
        assert 'mempool' in reason.lower() or 'volatility' in reason.lower()
    
    def test_detect_quiet_mode_reorg(self):
        """Test quiet mode detection for blockchain reorg"""
        signal_data = {
            'reorg_detected': True,
            'block_height': 800000
        }
        
        should_quiet, reason = ConfidenceScorer.detect_quiet_mode(signal_data, 'exchange')
        
        assert should_quiet is True
        assert 'reorg' in reason.lower()
    
    def test_detect_quiet_mode_normal(self):
        """Test quiet mode detection with normal data"""
        signal_data = {
            'change_24h': 20.0,
            'is_anomaly': False,
            'block_height': 800000,
            'signal_strength': 0.8
        }
        
        should_quiet, reason = ConfidenceScorer.detect_quiet_mode(signal_data, 'mempool')
        
        assert should_quiet is False
        assert reason == ""
    
    def test_get_historical_accuracy(self):
        """Test historical accuracy retrieval"""
        accuracy = ConfidenceScorer.get_historical_accuracy('mempool', '1.0.0')
        
        assert 0.0 <= accuracy <= 1.0
        assert accuracy > 0.5  # Should have reasonable default
    
    def test_confidence_factors_to_dict(self):
        """Test ConfidenceFactors serialization"""
        factors = ConfidenceFactors(
            signal_strength=0.8,
            historical_accuracy=0.75,
            data_quality=0.9
        )
        
        factors_dict = factors.to_dict()
        
        assert factors_dict['signal_strength'] == 0.8
        assert factors_dict['historical_accuracy'] == 0.75
        assert factors_dict['data_quality'] == 0.9
    
    def test_confidence_score_to_dict(self):
        """Test ConfidenceScore serialization"""
        factors = ConfidenceFactors(
            signal_strength=0.8,
            historical_accuracy=0.75,
            data_quality=0.9
        )
        
        score = ConfidenceScore(
            score=0.82,
            level=ConfidenceLevel.MEDIUM,
            factors=factors,
            should_publish=True
        )
        
        score_dict = score.to_dict()
        
        assert score_dict['score'] == 0.82
        assert score_dict['level'] == 'medium'
        assert score_dict['should_publish'] is True
        assert 'factors' in score_dict
