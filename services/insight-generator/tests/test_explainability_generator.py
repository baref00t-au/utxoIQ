"""
Unit tests for explainability generation
"""

import pytest
from src.generators.explainability_generator import (
    ExplainabilityGenerator,
    ExplainabilitySummary
)
from src.generators.confidence_scorer import (
    ConfidenceScorer,
    ConfidenceFactors,
    ConfidenceScore,
    ConfidenceLevel
)


class TestExplainabilityGenerator:
    """Test explainability generation functionality"""
    
    def test_generate_explainability_high_confidence(self):
        """Test explainability generation for high confidence insight"""
        factors = ConfidenceFactors(
            signal_strength=0.9,
            historical_accuracy=0.85,
            data_quality=0.95
        )
        
        confidence_score = ConfidenceScore(
            score=0.88,
            level=ConfidenceLevel.HIGH,
            factors=factors,
            should_publish=True
        )
        
        signal_data = {
            'block_height': 800000,
            'change_24h': 50.0
        }
        
        explainability = ExplainabilityGenerator.generate_explainability(
            confidence_score, 'mempool', signal_data
        )
        
        assert explainability.explanation
        assert 'high confidence' in explainability.explanation.lower()
        assert len(explainability.supporting_evidence) > 0
        assert explainability.confidence_factors['signal_strength'] == 0.9
    
    def test_generate_explainability_medium_confidence(self):
        """Test explainability generation for medium confidence insight"""
        factors = ConfidenceFactors(
            signal_strength=0.7,
            historical_accuracy=0.75,
            data_quality=0.8
        )
        
        confidence_score = ConfidenceScore(
            score=0.75,
            level=ConfidenceLevel.MEDIUM,
            factors=factors,
            should_publish=True
        )
        
        signal_data = {
            'block_height': 800000,
            'std_dev_multiple': 2.0
        }
        
        explainability = ExplainabilityGenerator.generate_explainability(
            confidence_score, 'exchange', signal_data
        )
        
        assert explainability.explanation
        assert 'moderate confidence' in explainability.explanation.lower()
        assert len(explainability.supporting_evidence) >= 3
    
    def test_generate_explainability_low_confidence(self):
        """Test explainability generation for low confidence insight"""
        factors = ConfidenceFactors(
            signal_strength=0.4,
            historical_accuracy=0.5,
            data_quality=0.6
        )
        
        confidence_score = ConfidenceScore(
            score=0.48,
            level=ConfidenceLevel.LOW,
            factors=factors,
            should_publish=False
        )
        
        signal_data = {
            'block_height': 800000
        }
        
        explainability = ExplainabilityGenerator.generate_explainability(
            confidence_score, 'miner', signal_data
        )
        
        assert explainability.explanation
        assert 'lower confidence' in explainability.explanation.lower()
        assert len(explainability.supporting_evidence) > 0
    
    def test_generate_supporting_evidence_mempool(self):
        """Test supporting evidence generation for mempool signals"""
        factors = ConfidenceFactors(
            signal_strength=0.8,
            historical_accuracy=0.82,
            data_quality=0.9
        )
        
        signal_data = {
            'block_height': 800000,
            'change_24h': 45.5
        }
        
        evidence = ExplainabilityGenerator._generate_supporting_evidence(
            factors, 'mempool', signal_data
        )
        
        assert len(evidence) >= 3
        assert any('mempool' in e.lower() for e in evidence)
        assert any('45.5%' in e for e in evidence)
        assert any('800000' in e for e in evidence)
    
    def test_generate_supporting_evidence_exchange(self):
        """Test supporting evidence generation for exchange signals"""
        factors = ConfidenceFactors(
            signal_strength=0.85,
            historical_accuracy=0.78,
            data_quality=0.95
        )
        
        signal_data = {
            'block_height': 800000,
            'std_dev_multiple': 2.8
        }
        
        evidence = ExplainabilityGenerator._generate_supporting_evidence(
            factors, 'exchange', signal_data
        )
        
        assert len(evidence) >= 3
        assert any('2.8' in e for e in evidence)
        assert any('standard deviation' in e.lower() for e in evidence)
    
    def test_generate_supporting_evidence_whale(self):
        """Test supporting evidence generation for whale signals"""
        factors = ConfidenceFactors(
            signal_strength=0.75,
            historical_accuracy=0.75,
            data_quality=0.85
        )
        
        signal_data = {
            'block_height': 800000,
            'streak_days': 10
        }
        
        evidence = ExplainabilityGenerator._generate_supporting_evidence(
            factors, 'whale', signal_data
        )
        
        assert len(evidence) >= 3
        assert any('10' in e and 'days' in e.lower() for e in evidence)
    
    def test_format_for_display(self):
        """Test explainability formatting for display"""
        factors = ConfidenceFactors(
            signal_strength=0.8,
            historical_accuracy=0.75,
            data_quality=0.9
        )
        
        explainability = ExplainabilitySummary(
            confidence_factors=factors.to_dict(),
            explanation="This is a test explanation.",
            supporting_evidence=["Evidence 1", "Evidence 2", "Evidence 3"]
        )
        
        formatted = ExplainabilityGenerator.format_for_display(explainability)
        
        assert "Confidence Explanation:" in formatted
        assert "This is a test explanation." in formatted
        assert "Confidence Factors:" in formatted
        assert "Supporting Evidence:" in formatted
        assert "Evidence 1" in formatted
    
    def test_generate_short_explanation(self):
        """Test short explanation generation"""
        factors = ConfidenceFactors(
            signal_strength=0.9,
            historical_accuracy=0.75,
            data_quality=0.8
        )
        
        confidence_score = ConfidenceScore(
            score=0.85,
            level=ConfidenceLevel.HIGH,
            factors=factors,
            should_publish=True
        )
        
        short_explanation = ExplainabilityGenerator.generate_short_explanation(
            confidence_score
        )
        
        assert short_explanation
        assert '85%' in short_explanation or '0.85' in short_explanation
        assert 'signal strength' in short_explanation.lower()
    
    def test_explainability_summary_to_dict(self):
        """Test ExplainabilitySummary serialization"""
        summary = ExplainabilitySummary(
            confidence_factors={
                'signal_strength': 0.8,
                'historical_accuracy': 0.75,
                'data_quality': 0.9
            },
            explanation="Test explanation",
            supporting_evidence=["Evidence 1", "Evidence 2"]
        )
        
        summary_dict = summary.to_dict()
        
        assert summary_dict['explanation'] == "Test explanation"
        assert len(summary_dict['supporting_evidence']) == 2
        assert summary_dict['confidence_factors']['signal_strength'] == 0.8
