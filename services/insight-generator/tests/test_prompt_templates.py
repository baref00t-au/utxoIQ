"""
Unit tests for prompt templates
"""

import pytest
from src.prompts.templates import PromptTemplates


class TestPromptTemplates:
    """Test prompt template functionality"""
    
    def test_get_prompt_for_mempool(self):
        """Test mempool prompt template retrieval"""
        prompt = PromptTemplates.get_prompt_for_signal_type('mempool')
        
        assert prompt
        assert 'mempool' in prompt.lower()
        assert '{block_height}' in prompt
        assert '{p50}' in prompt
    
    def test_get_prompt_for_exchange(self):
        """Test exchange prompt template retrieval"""
        prompt = PromptTemplates.get_prompt_for_signal_type('exchange')
        
        assert prompt
        assert 'exchange' in prompt.lower()
        assert '{exchange_name}' in prompt
        assert '{inflow_btc}' in prompt
    
    def test_get_prompt_for_miner(self):
        """Test miner prompt template retrieval"""
        prompt = PromptTemplates.get_prompt_for_signal_type('miner')
        
        assert prompt
        assert 'miner' in prompt.lower()
        assert '{entity_name}' in prompt
        assert '{balance_change}' in prompt
    
    def test_get_prompt_for_whale(self):
        """Test whale prompt template retrieval"""
        prompt = PromptTemplates.get_prompt_for_signal_type('whale')
        
        assert prompt
        assert 'whale' in prompt.lower()
        assert '{accumulation_btc}' in prompt
        assert '{streak_days}' in prompt
    
    def test_get_prompt_for_predictive(self):
        """Test predictive prompt template retrieval"""
        prompt = PromptTemplates.get_prompt_for_signal_type('predictive')
        
        assert prompt
        assert 'predictive' in prompt.lower()
        assert '{forecast_value}' in prompt
        assert '{confidence_interval}' in prompt
    
    def test_format_mempool_prompt(self):
        """Test mempool prompt formatting"""
        signal_data = {
            'block_height': 800000,
            'p25': 10,
            'p50': 20,
            'p75': 30,
            'p95': 50,
            'mempool_size': 5000,
            'next_block_fee': 25,
            'signal_strength': 0.8,
            'historical_p50': 18,
            'change_24h': 11.1,
            'is_anomaly': False
        }
        
        formatted = PromptTemplates.format_prompt('mempool', signal_data)
        
        assert '800000' in formatted
        assert '20' in formatted  # p50
        assert '5000' in formatted  # mempool_size
        assert 'JSON' in formatted
    
    def test_format_exchange_prompt(self):
        """Test exchange prompt formatting"""
        signal_data = {
            'block_height': 800000,
            'exchange_name': 'Binance',
            'inflow_btc': 1500.5,
            'tx_count': 25,
            'anomaly_score': 0.85,
            'signal_strength': 0.9,
            'avg_inflow_7d': 500.0,
            'std_dev': 200.0,
            'std_dev_multiple': 3.5,
            'historical_context': 'Highest inflow in 30 days'
        }
        
        formatted = PromptTemplates.format_prompt('exchange', signal_data)
        
        assert '800000' in formatted
        assert 'Binance' in formatted
        assert '1500.5' in formatted
        assert '3.5' in formatted
    
    def test_format_prompt_missing_field(self):
        """Test prompt formatting with missing required field"""
        signal_data = {
            'block_height': 800000
            # Missing other required fields
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            PromptTemplates.format_prompt('mempool', signal_data)
    
    def test_format_explainability_prompt(self):
        """Test explainability prompt formatting"""
        formatted = PromptTemplates.format_explainability_prompt(
            confidence=0.85,
            headline="Bitcoin mempool fees spike 50%",
            signal_type='mempool',
            signal_strength=0.9,
            data_quality=0.95,
            historical_accuracy=0.82
        )
        
        assert '0.85' in formatted
        assert 'Bitcoin mempool fees spike 50%' in formatted
        assert 'mempool' in formatted
        assert '0.9' in formatted
        assert 'JSON' in formatted
    
    def test_system_prompt_exists(self):
        """Test system prompt is defined"""
        assert PromptTemplates.SYSTEM_PROMPT
        assert 'Bitcoin' in PromptTemplates.SYSTEM_PROMPT
        assert 'analyst' in PromptTemplates.SYSTEM_PROMPT.lower()
    
    def test_all_prompts_request_json(self):
        """Test all prompts request JSON response format"""
        signal_types = ['mempool', 'exchange', 'miner', 'whale', 'predictive']
        
        for signal_type in signal_types:
            prompt = PromptTemplates.get_prompt_for_signal_type(signal_type)
            assert 'JSON' in prompt or 'json' in prompt
