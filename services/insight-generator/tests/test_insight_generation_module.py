"""
Unit tests for InsightGenerationModule.

Tests the core insight generation logic including:
- Prompt template selection
- AI provider integration
- Evidence extraction
- Insight creation
"""

import pytest
import uuid
import sys
import os
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.insight_generation import (
    InsightGenerationModule,
    Insight,
    Evidence
)
from src.ai_provider import (
    AIProvider,
    Signal,
    InsightContent,
    AIProviderError
)


class MockAIProvider(AIProvider):
    """Mock AI provider for testing"""
    
    def __init__(self, config=None):
        super().__init__(config or {})
        self.generate_insight = AsyncMock()
    
    async def generate_insight(self, signal, prompt_template):
        """Mock implementation"""
        return InsightContent(
            headline="Test Headline",
            summary="Test summary explaining the signal.",
            confidence_explanation="High confidence based on data quality."
        )


@pytest.fixture
def mock_ai_provider():
    """Create mock AI provider"""
    return MockAIProvider()


@pytest.fixture
def insight_module(mock_ai_provider):
    """Create InsightGenerationModule with mock provider"""
    return InsightGenerationModule(mock_ai_provider)


@pytest.fixture
def sample_mempool_signal():
    """Sample mempool signal for testing"""
    return {
        "signal_id": str(uuid.uuid4()),
        "signal_type": "mempool",
        "block_height": 800000,
        "confidence": 0.85,
        "metadata": {
            "fee_rate_median": 50.5,
            "fee_rate_change_pct": 25.3,
            "mempool_size_mb": 120.5,
            "tx_count": 15000,
            "tx_ids": ["tx1", "tx2", "tx3"]
        },
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_exchange_signal():
    """Sample exchange signal for testing"""
    return {
        "signal_id": str(uuid.uuid4()),
        "signal_type": "exchange",
        "block_height": 800001,
        "confidence": 0.78,
        "metadata": {
            "entity_id": "coinbase_001",
            "entity_name": "Coinbase",
            "flow_type": "outflow",
            "amount_btc": 1250.5,
            "tx_count": 45,
            "addresses": ["bc1q...", "3FZbgi..."],
            "transaction_ids": ["tx4", "tx5"]
        },
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_treasury_signal():
    """Sample treasury signal for testing"""
    return {
        "signal_id": str(uuid.uuid4()),
        "signal_type": "treasury",
        "block_height": 800002,
        "confidence": 0.92,
        "metadata": {
            "entity_id": "microstrategy_001",
            "entity_name": "MicroStrategy",
            "company_ticker": "MSTR",
            "flow_type": "accumulation",
            "amount_btc": 500.0,
            "known_holdings_btc": 152800,
            "holdings_change_pct": 0.33,
            "txids": ["tx6"]
        },
        "created_at": datetime.utcnow()
    }


class TestInsightGenerationModule:
    """Test InsightGenerationModule class"""
    
    def test_initialization(self, mock_ai_provider):
        """Test module initialization"""
        module = InsightGenerationModule(mock_ai_provider)
        
        assert module.ai_provider == mock_ai_provider
        assert len(module.PROMPT_TEMPLATES) == 6
        assert "mempool" in module.PROMPT_TEMPLATES
        assert "exchange" in module.PROMPT_TEMPLATES
        assert "treasury" in module.PROMPT_TEMPLATES
    
    def test_validate_signal_valid(self, insight_module, sample_mempool_signal):
        """Test signal validation with valid signal"""
        assert insight_module._validate_signal(sample_mempool_signal) is True
    
    def test_validate_signal_missing_field(self, insight_module):
        """Test signal validation with missing required field"""
        invalid_signal = {
            "signal_id": "test",
            "signal_type": "mempool"
            # Missing block_height, confidence, metadata
        }
        
        assert insight_module._validate_signal(invalid_signal) is False
    
    def test_validate_signal_unsupported_type(self, insight_module):
        """Test signal validation with unsupported signal type"""
        invalid_signal = {
            "signal_id": "test",
            "signal_type": "unsupported_type",
            "block_height": 800000,
            "confidence": 0.8,
            "metadata": {}
        }
        
        assert insight_module._validate_signal(invalid_signal) is False
    
    def test_select_prompt_template_mempool(self, insight_module):
        """Test prompt template selection for mempool signal"""
        template = insight_module._select_prompt_template("mempool")
        
        assert template is not None
        assert "mempool" in template.lower()
        assert "fee_rate_median" in template
    
    def test_select_prompt_template_exchange(self, insight_module):
        """Test prompt template selection for exchange signal"""
        template = insight_module._select_prompt_template("exchange")
        
        assert template is not None
        assert "exchange" in template.lower()
        assert "entity_name" in template
    
    def test_select_prompt_template_treasury(self, insight_module):
        """Test prompt template selection for treasury signal"""
        template = insight_module._select_prompt_template("treasury")
        
        assert template is not None
        assert "treasury" in template.lower() or "company" in template.lower()
        assert "company_ticker" in template
    
    def test_select_prompt_template_invalid(self, insight_module):
        """Test prompt template selection with invalid type"""
        template = insight_module._select_prompt_template("invalid_type")
        
        assert template is None
    
    def test_validate_ai_content_valid(self, insight_module):
        """Test AI content validation with valid content"""
        content = InsightContent(
            headline="Bitcoin Mempool Fees Surge 25%",
            summary="Mempool fees have increased significantly due to high demand.",
            confidence_explanation="High confidence based on consistent data."
        )
        
        assert insight_module._validate_ai_content(content) is True
    
    def test_validate_ai_content_headline_too_long(self, insight_module):
        """Test AI content validation with headline exceeding 80 chars"""
        content = InsightContent(
            headline="A" * 81,  # 81 characters
            summary="Valid summary.",
            confidence_explanation="Valid explanation."
        )
        
        assert insight_module._validate_ai_content(content) is False
    
    def test_validate_ai_content_missing_summary(self, insight_module):
        """Test AI content validation with missing summary"""
        content = InsightContent(
            headline="Valid Headline",
            summary="",
            confidence_explanation="Valid explanation."
        )
        
        assert insight_module._validate_ai_content(content) is False
    
    def test_validate_ai_content_summary_too_short(self, insight_module):
        """Test AI content validation with summary too short"""
        content = InsightContent(
            headline="Valid Headline",
            summary="Short",  # Less than 10 chars
            confidence_explanation="Valid explanation."
        )
        
        assert insight_module._validate_ai_content(content) is False
    
    def test_extract_evidence_with_tx_ids(self, insight_module, sample_mempool_signal):
        """Test evidence extraction with transaction IDs"""
        evidence = insight_module._extract_evidence(sample_mempool_signal)
        
        assert isinstance(evidence, Evidence)
        assert len(evidence.block_heights) == 1
        assert evidence.block_heights[0] == 800000
        assert len(evidence.transaction_ids) == 3
        assert "tx1" in evidence.transaction_ids
        assert "tx2" in evidence.transaction_ids
        assert "tx3" in evidence.transaction_ids
    
    def test_extract_evidence_with_transaction_ids_field(
        self,
        insight_module,
        sample_exchange_signal
    ):
        """Test evidence extraction with transaction_ids field"""
        evidence = insight_module._extract_evidence(sample_exchange_signal)
        
        assert len(evidence.block_heights) == 1
        assert evidence.block_heights[0] == 800001
        assert len(evidence.transaction_ids) == 2
        assert "tx4" in evidence.transaction_ids
        assert "tx5" in evidence.transaction_ids
    
    def test_extract_evidence_with_txids_field(
        self,
        insight_module,
        sample_treasury_signal
    ):
        """Test evidence extraction with txids field"""
        evidence = insight_module._extract_evidence(sample_treasury_signal)
        
        assert len(evidence.block_heights) == 1
        assert evidence.block_heights[0] == 800002
        assert len(evidence.transaction_ids) == 1
        assert "tx6" in evidence.transaction_ids
    
    def test_extract_evidence_no_tx_ids(self, insight_module):
        """Test evidence extraction with no transaction IDs"""
        signal = {
            "signal_id": "test",
            "signal_type": "mempool",
            "block_height": 800000,
            "confidence": 0.8,
            "metadata": {
                "fee_rate_median": 50.5
                # No tx IDs
            }
        }
        
        evidence = insight_module._extract_evidence(signal)
        
        assert len(evidence.block_heights) == 1
        assert len(evidence.transaction_ids) == 0
    
    def test_extract_evidence_removes_duplicates(self, insight_module):
        """Test evidence extraction removes duplicate tx IDs"""
        signal = {
            "signal_id": "test",
            "signal_type": "mempool",
            "block_height": 800000,
            "confidence": 0.8,
            "metadata": {
                "tx_ids": ["tx1", "tx2", "tx1", "tx3", "tx2"]
            }
        }
        
        evidence = insight_module._extract_evidence(signal)
        
        assert len(evidence.transaction_ids) == 3
        assert set(evidence.transaction_ids) == {"tx1", "tx2", "tx3"}
    
    @pytest.mark.asyncio
    async def test_generate_insight_success(
        self,
        insight_module,
        mock_ai_provider,
        sample_mempool_signal
    ):
        """Test successful insight generation"""
        # Configure mock to return valid content
        mock_ai_provider.generate_insight.return_value = InsightContent(
            headline="Bitcoin Mempool Fees Surge 25%",
            summary="Mempool fees have increased significantly due to high demand. "
                    "This may impact transaction confirmation times.",
            confidence_explanation="High confidence based on consistent data."
        )
        
        insight = await insight_module.generate_insight(sample_mempool_signal)
        
        assert insight is not None
        assert isinstance(insight, Insight)
        assert insight.signal_id == sample_mempool_signal["signal_id"]
        assert insight.category == "mempool"
        assert insight.headline == "Bitcoin Mempool Fees Surge 25%"
        assert "increased significantly" in insight.summary
        assert insight.confidence == 0.85
        assert len(insight.evidence.block_heights) == 1
        assert insight.evidence.block_heights[0] == 800000
        assert len(insight.evidence.transaction_ids) == 3
        assert insight.chart_url is None
        
        # Verify AI provider was called
        mock_ai_provider.generate_insight.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_insight_invalid_signal(
        self,
        insight_module,
        mock_ai_provider
    ):
        """Test insight generation with invalid signal"""
        invalid_signal = {
            "signal_id": "test"
            # Missing required fields
        }
        
        insight = await insight_module.generate_insight(invalid_signal)
        
        assert insight is None
        mock_ai_provider.generate_insight.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_insight_ai_provider_error(
        self,
        insight_module,
        mock_ai_provider,
        sample_mempool_signal
    ):
        """Test insight generation when AI provider fails"""
        # Configure mock to raise error
        mock_ai_provider.generate_insight.side_effect = AIProviderError(
            "API rate limit exceeded"
        )
        
        insight = await insight_module.generate_insight(sample_mempool_signal)
        
        assert insight is None
    
    @pytest.mark.asyncio
    async def test_generate_insight_invalid_ai_content(
        self,
        insight_module,
        mock_ai_provider,
        sample_mempool_signal
    ):
        """Test insight generation with invalid AI content"""
        # Configure mock to return invalid content (headline too long)
        mock_ai_provider.generate_insight.return_value = InsightContent(
            headline="A" * 81,  # Too long
            summary="Valid summary.",
            confidence_explanation="Valid explanation."
        )
        
        insight = await insight_module.generate_insight(sample_mempool_signal)
        
        assert insight is None
    
    @pytest.mark.asyncio
    async def test_generate_insights_batch(
        self,
        insight_module,
        mock_ai_provider,
        sample_mempool_signal,
        sample_exchange_signal
    ):
        """Test batch insight generation"""
        # Configure mock to return valid content
        mock_ai_provider.generate_insight.return_value = InsightContent(
            headline="Test Headline",
            summary="Test summary explaining the signal.",
            confidence_explanation="High confidence based on data quality."
        )
        
        signals = [sample_mempool_signal, sample_exchange_signal]
        insights = await insight_module.generate_insights_batch(signals)
        
        assert len(insights) == 2
        assert all(isinstance(i, Insight) for i in insights)
        assert insights[0].category == "mempool"
        assert insights[1].category == "exchange"
    
    @pytest.mark.asyncio
    async def test_generate_insights_batch_partial_failure(
        self,
        insight_module,
        mock_ai_provider,
        sample_mempool_signal
    ):
        """Test batch generation with some failures"""
        # Configure mock to return valid content
        mock_ai_provider.generate_insight.return_value = InsightContent(
            headline="Test Headline",
            summary="Test summary explaining the signal.",
            confidence_explanation="High confidence based on data quality."
        )
        
        invalid_signal = {"signal_id": "invalid"}
        
        signals = [sample_mempool_signal, invalid_signal]
        insights = await insight_module.generate_insights_batch(signals)
        
        # Only one insight should be generated (valid signal)
        assert len(insights) == 1
        assert insights[0].signal_id == sample_mempool_signal["signal_id"]
    
    def test_insight_to_dict(self, sample_mempool_signal):
        """Test Insight.to_dict() method"""
        evidence = Evidence(
            block_heights=[800000],
            transaction_ids=["tx1", "tx2"]
        )
        
        insight = Insight(
            insight_id="insight-123",
            signal_id=sample_mempool_signal["signal_id"],
            category="mempool",
            headline="Test Headline",
            summary="Test summary.",
            confidence=0.85,
            evidence=evidence,
            chart_url="https://example.com/chart.png",
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        result = insight.to_dict()
        
        assert result["insight_id"] == "insight-123"
        assert result["signal_id"] == sample_mempool_signal["signal_id"]
        assert result["category"] == "mempool"
        assert result["headline"] == "Test Headline"
        assert result["summary"] == "Test summary."
        assert result["confidence"] == 0.85
        assert result["evidence"]["block_heights"] == [800000]
        assert result["evidence"]["transaction_ids"] == ["tx1", "tx2"]
        assert result["chart_url"] == "https://example.com/chart.png"
        assert result["created_at"] == datetime(2024, 1, 1, 12, 0, 0)
    
    @pytest.mark.asyncio
    async def test_generate_insight_for_each_signal_type(
        self,
        insight_module,
        mock_ai_provider
    ):
        """Test insight generation for all supported signal types"""
        signal_types = ["mempool", "exchange", "miner", "whale", "treasury", "predictive"]
        
        # Configure mock to return valid content
        mock_ai_provider.generate_insight.return_value = InsightContent(
            headline="Test Headline",
            summary="Test summary explaining the signal.",
            confidence_explanation="High confidence based on data quality."
        )
        
        for signal_type in signal_types:
            signal = {
                "signal_id": str(uuid.uuid4()),
                "signal_type": signal_type,
                "block_height": 800000,
                "confidence": 0.8,
                "metadata": {},
                "created_at": datetime.utcnow()
            }
            
            insight = await insight_module.generate_insight(signal)
            
            assert insight is not None
            assert insight.category == signal_type
