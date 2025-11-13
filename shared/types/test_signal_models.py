"""
Unit tests for signal_models.py Pydantic models.

Tests validation, serialization, and deserialization of Signal, Insight, Evidence, and EntityInfo models.
"""

import pytest
from datetime import datetime
from signal_models import (
    Signal,
    SignalType,
    Insight,
    Evidence,
    EntityInfo,
    EntityType,
    MempoolSignalMetadata,
    ExchangeSignalMetadata,
    TreasurySignalMetadata,
    MinerSignalMetadata,
    WhaleSignalMetadata,
    PredictiveSignalMetadata
)


class TestSignal:
    """Test Signal model validation."""
    
    def test_valid_signal(self):
        """Test creating a valid signal."""
        signal = Signal(
            signal_id="test-uuid-123",
            signal_type=SignalType.MEMPOOL,
            block_height=800000,
            confidence=0.85,
            metadata={"fee_rate_median": 50.5},
            created_at=datetime.utcnow()
        )
        
        assert signal.signal_id == "test-uuid-123"
        assert signal.signal_type == SignalType.MEMPOOL
        assert signal.block_height == 800000
        assert signal.confidence == 0.85
        assert signal.processed is False
        assert signal.processed_at is None
    
    def test_invalid_confidence(self):
        """Test that confidence must be between 0 and 1."""
        with pytest.raises(ValueError):
            Signal(
                signal_id="test-uuid-123",
                signal_type=SignalType.MEMPOOL,
                block_height=800000,
                confidence=1.5,  # Invalid: > 1.0
                metadata={},
                created_at=datetime.utcnow()
            )
    
    def test_invalid_block_height(self):
        """Test that block height must be non-negative."""
        with pytest.raises(ValueError):
            Signal(
                signal_id="test-uuid-123",
                signal_type=SignalType.MEMPOOL,
                block_height=-1,  # Invalid: negative
                confidence=0.85,
                metadata={},
                created_at=datetime.utcnow()
            )
    
    def test_invalid_signal_type(self):
        """Test that signal_type must be valid enum value."""
        with pytest.raises(ValueError):
            Signal(
                signal_id="test-uuid-123",
                signal_type="invalid_type",  # Invalid
                block_height=800000,
                confidence=0.85,
                metadata={},
                created_at=datetime.utcnow()
            )


class TestEvidence:
    """Test Evidence model validation."""
    
    def test_valid_evidence(self):
        """Test creating valid evidence."""
        evidence = Evidence(
            block_heights=[800000, 800001],
            transaction_ids=["tx1", "tx2"]
        )
        
        assert len(evidence.block_heights) == 2
        assert len(evidence.transaction_ids) == 2
    
    def test_empty_evidence(self):
        """Test creating evidence with empty arrays."""
        evidence = Evidence()
        
        assert evidence.block_heights == []
        assert evidence.transaction_ids == []
    
    def test_invalid_block_heights(self):
        """Test that block heights must be non-negative."""
        with pytest.raises(ValueError):
            Evidence(block_heights=[-1, 800000])


class TestInsight:
    """Test Insight model validation."""
    
    def test_valid_insight(self):
        """Test creating a valid insight."""
        insight = Insight(
            insight_id="insight-uuid-123",
            signal_id="signal-uuid-123",
            category=SignalType.EXCHANGE,
            headline="Large Coinbase Outflow Detected",
            summary="A significant outflow of 1,250 BTC from Coinbase suggests institutional accumulation.",
            confidence=0.82,
            evidence=Evidence(
                block_heights=[800000],
                transaction_ids=["tx123"]
            ),
            created_at=datetime.utcnow()
        )
        
        assert insight.insight_id == "insight-uuid-123"
        assert insight.signal_id == "signal-uuid-123"
        assert insight.category == SignalType.EXCHANGE
        assert len(insight.headline) <= 80
        assert insight.chart_url is None
    
    def test_headline_too_long(self):
        """Test that headline must be 80 characters or less."""
        with pytest.raises(ValueError):
            Insight(
                insight_id="insight-uuid-123",
                signal_id="signal-uuid-123",
                category=SignalType.EXCHANGE,
                headline="A" * 81,  # Invalid: > 80 chars
                summary="Summary text",
                confidence=0.82,
                evidence=Evidence(),
                created_at=datetime.utcnow()
            )
    
    def test_empty_headline(self):
        """Test that headline cannot be empty."""
        with pytest.raises(ValueError):
            Insight(
                insight_id="insight-uuid-123",
                signal_id="signal-uuid-123",
                category=SignalType.EXCHANGE,
                headline="",  # Invalid: empty
                summary="Summary text",
                confidence=0.82,
                evidence=Evidence(),
                created_at=datetime.utcnow()
            )


class TestEntityInfo:
    """Test EntityInfo model validation."""
    
    def test_valid_entity(self):
        """Test creating a valid entity."""
        entity = EntityInfo(
            entity_id="microstrategy_001",
            entity_name="MicroStrategy",
            entity_type=EntityType.TREASURY,
            addresses=["bc1q123", "bc1q456"],
            metadata={"ticker": "MSTR", "known_holdings_btc": 152800},
            updated_at=datetime.utcnow()
        )
        
        assert entity.entity_id == "microstrategy_001"
        assert entity.entity_type == EntityType.TREASURY
        assert len(entity.addresses) == 2
        assert entity.metadata["ticker"] == "MSTR"
    
    def test_empty_addresses(self):
        """Test that entity must have at least one address."""
        with pytest.raises(ValueError):
            EntityInfo(
                entity_id="test_001",
                entity_name="Test Entity",
                entity_type=EntityType.EXCHANGE,
                addresses=[],  # Invalid: empty
                updated_at=datetime.utcnow()
            )
    
    def test_invalid_entity_type(self):
        """Test that entity_type must be valid enum value."""
        with pytest.raises(ValueError):
            EntityInfo(
                entity_id="test_001",
                entity_name="Test Entity",
                entity_type="invalid_type",  # Invalid
                addresses=["bc1q123"],
                updated_at=datetime.utcnow()
            )


class TestMetadataModels:
    """Test signal metadata models."""
    
    def test_mempool_metadata(self):
        """Test MempoolSignalMetadata validation."""
        metadata = MempoolSignalMetadata(
            fee_rate_median=50.5,
            fee_rate_change_pct=25.3,
            tx_count=15000,
            mempool_size_mb=120.5,
            comparison_window="1h"
        )
        
        assert metadata.fee_rate_median == 50.5
        assert metadata.tx_count == 15000
    
    def test_treasury_metadata(self):
        """Test TreasurySignalMetadata validation."""
        metadata = TreasurySignalMetadata(
            entity_id="microstrategy_001",
            entity_name="MicroStrategy",
            company_ticker="MSTR",
            flow_type="accumulation",
            amount_btc=500.0,
            tx_count=3,
            addresses=["bc1q123"],
            known_holdings_btc=152800,
            holdings_change_pct=0.33
        )
        
        assert metadata.company_ticker == "MSTR"
        assert metadata.known_holdings_btc == 152800
    
    def test_predictive_metadata(self):
        """Test PredictiveSignalMetadata validation."""
        metadata = PredictiveSignalMetadata(
            prediction_type="fee_forecast",
            predicted_value=55.2,
            confidence_interval=[48.1, 62.3],
            forecast_horizon="1h",
            model_version="v1.2"
        )
        
        assert metadata.prediction_type == "fee_forecast"
        assert len(metadata.confidence_interval) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
