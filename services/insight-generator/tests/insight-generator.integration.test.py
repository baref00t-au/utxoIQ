"""
Unit tests for main insight generator
"""

import pytest
from datetime import datetime
from src.generators.insight_generator import InsightGenerator, Insight


class TestInsightGenerator:
    """Test main insight generation functionality"""
    
    def test_generate_insight_mempool(self):
        """Test insight generation for mempool signal"""
        generator = InsightGenerator(model_version='1.0.0')
        
        signal_data = {
            'block_height': 800000,
            'signal_strength': 0.8,
            'p25': 10,
            'p50': 20,
            'p75': 30,
            'p95': 50,
            'mempool_size': 5000,
            'next_block_fee': 25,
            'historical_p50': 18,
            'change_24h': 11.1,
            'is_anomaly': False,
            'transaction_ids': ['tx1', 'tx2'],
            'entity_ids': []
        }
        
        insight = generator.generate_insight(
            signal_data=signal_data,
            signal_type='mempool',
            chart_url='https://example.com/chart.png'
        )
        
        assert insight is not None
        assert insight.signal_type == 'mempool'
        assert insight.headline
        assert insight.summary
        assert 0.0 <= insight.confidence <= 1.0
        assert insight.block_height == 800000
        assert len(insight.evidence) > 0
        assert insight.chart_url == 'https://example.com/chart.png'
        assert insight.explainability is not None
    
    def test_generate_insight_exchange(self):
        """Test insight generation for exchange signal"""
        generator = InsightGenerator(model_version='1.0.0')
        
        signal_data = {
            'block_height': 800000,
            'signal_strength': 0.85,
            'exchange_name': 'Binance',
            'inflow_btc': 1500.5,
            'tx_count': 25,
            'anomaly_score': 0.85,
            'avg_inflow_7d': 500.0,
            'std_dev': 200.0,
            'std_dev_multiple': 3.5,
            'historical_context': 'Highest inflow in 30 days',
            'is_anomaly': False,
            'transaction_ids': ['tx1', 'tx2', 'tx3'],
            'entity_ids': ['entity1']
        }
        
        insight = generator.generate_insight(
            signal_data=signal_data,
            signal_type='exchange'
        )
        
        assert insight is not None
        assert insight.signal_type == 'exchange'
        assert insight.confidence >= 0.7  # Should be publishable
    
    def test_generate_insight_low_confidence(self):
        """Test insight generation with low confidence (should not publish)"""
        generator = InsightGenerator(model_version='1.0.0')
        
        signal_data = {
            'block_height': 800000,
            'signal_strength': 0.3,  # Low strength
            'change_24h': 5.0,
            'is_anomaly': False,
            'transaction_ids': [],
            'entity_ids': []
        }
        
        insight = generator.generate_insight(
            signal_data=signal_data,
            signal_type='mempool'
        )
        
        # Should return None due to low confidence
        assert insight is None
    
    def test_generate_insight_quiet_mode(self):
        """Test insight generation during quiet mode"""
        generator = InsightGenerator(model_version='1.0.0')
        
        signal_data = {
            'block_height': 800000,
            'signal_strength': 0.9,
            'change_24h': 350.0,  # Extreme change triggers quiet mode
            'is_anomaly': True,
            'std_dev_multiple': 4.0,
            'transaction_ids': ['tx1'],
            'entity_ids': []
        }
        
        insight = generator.generate_insight(
            signal_data=signal_data,
            signal_type='mempool'
        )
        
        # Should return None due to quiet mode
        assert insight is None
    
    def test_generate_insight_with_tags(self):
        """Test insight generation includes appropriate tags"""
        generator = InsightGenerator(model_version='1.0.0')
        
        signal_data = {
            'block_height': 800000,
            'signal_strength': 0.85,
            'change_24h': 60.0,  # High volatility
            'is_anomaly': False,
            'transaction_ids': ['tx1'],
            'entity_ids': []
        }
        
        insight = generator.generate_insight(
            signal_data=signal_data,
            signal_type='mempool'
        )
        
        if insight:
            assert 'mempool' in insight.tags
            assert 'high-confidence' in insight.tags
            assert 'high-volatility' in insight.tags
    
    def test_generate_insight_predictive(self):
        """Test insight generation for predictive signal"""
        generator = InsightGenerator(model_version='1.0.0')
        
        signal_data = {
            'block_height': 800000,
            'signal_strength': 0.75,
            'prediction_type': 'fee_forecast',
            'forecast_value': 30.5,
            'ci_lower': 25.0,
            'ci_upper': 35.0,
            'forecast_horizon': 'next_block',
            'model_version': '1.0.0',
            'current_value': 28.0,
            'predicted_change': 8.9,
            'historical_accuracy': 0.75,
            'model_confidence': 0.8,
            'is_predictive': True,
            'transaction_ids': [],
            'entity_ids': []
        }
        
        insight = generator.generate_insight(
            signal_data=signal_data,
            signal_type='predictive'
        )
        
        if insight:
            assert insight.is_predictive is True
            assert 'predictive' in insight.tags
    
    def test_generate_explainability_for_existing_insight(self):
        """Test explainability generation for existing insight"""
        generator = InsightGenerator(model_version='1.0.0')
        
        # Create a mock insight
        insight = Insight(
            id='insight-123',
            signal_type='mempool',
            headline='Test headline',
            summary='Test summary',
            confidence=0.85,
            timestamp=datetime.now(),
            block_height=800000,
            evidence=[],
            tags=['mempool']
        )
        
        signal_data = {
            'block_height': 800000,
            'signal_strength': 0.85,
            'change_24h': 50.0,
            'is_anomaly': False
        }
        
        explainability = generator.generate_explainability_for_existing_insight(
            insight, signal_data
        )
        
        assert explainability is not None
        assert explainability.explanation
        assert len(explainability.supporting_evidence) > 0
    
    def test_insight_to_dict(self):
        """Test Insight serialization"""
        insight = Insight(
            id='insight-123',
            signal_type='mempool',
            headline='Test headline',
            summary='Test summary',
            confidence=0.85,
            timestamp=datetime.now(),
            block_height=800000,
            evidence=[],
            chart_url='https://example.com/chart.png',
            tags=['mempool', 'high-confidence'],
            is_predictive=False
        )
        
        insight_dict = insight.to_dict()
        
        assert insight_dict['id'] == 'insight-123'
        assert insight_dict['signal_type'] == 'mempool'
        assert insight_dict['headline'] == 'Test headline'
        assert insight_dict['confidence'] == 0.85
        assert insight_dict['block_height'] == 800000
        assert 'mempool' in insight_dict['tags']
