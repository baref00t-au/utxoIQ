"""
Explainability generator for confidence scores
Generates human-readable explanations of why an insight has a specific confidence score
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from .confidence_scorer import ConfidenceScore, ConfidenceFactors


@dataclass
class ExplainabilitySummary:
    """Explainability summary for an insight"""
    confidence_factors: Dict[str, float]
    explanation: str
    supporting_evidence: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'confidence_factors': self.confidence_factors,
            'explanation': self.explanation,
            'supporting_evidence': self.supporting_evidence
        }


class ExplainabilityGenerator:
    """Generates explainability summaries for confidence scores"""
    
    @staticmethod
    def generate_explainability(
        confidence_score: ConfidenceScore,
        signal_type: str,
        signal_data: Dict[str, Any]
    ) -> ExplainabilitySummary:
        """
        Generate explainability summary for a confidence score
        
        Args:
            confidence_score: Calculated confidence score
            signal_type: Type of signal
            signal_data: Raw signal data
            
        Returns:
            ExplainabilitySummary with explanation and evidence
        """
        factors = confidence_score.factors
        score = confidence_score.score
        
        # Generate main explanation
        explanation = ExplainabilityGenerator._generate_explanation(
            score, factors, signal_type
        )
        
        # Generate supporting evidence
        supporting_evidence = ExplainabilityGenerator._generate_supporting_evidence(
            factors, signal_type, signal_data
        )
        
        return ExplainabilitySummary(
            confidence_factors=factors.to_dict(),
            explanation=explanation,
            supporting_evidence=supporting_evidence
        )
    
    @staticmethod
    def _generate_explanation(
        score: float,
        factors: ConfidenceFactors,
        signal_type: str
    ) -> str:
        """Generate main explanation text"""
        # Determine confidence level description
        if score >= 0.85:
            level_desc = "high confidence"
        elif score >= 0.70:
            level_desc = "moderate confidence"
        else:
            level_desc = "lower confidence"
        
        # Identify dominant factor
        factor_values = {
            'signal_strength': factors.signal_strength,
            'historical_accuracy': factors.historical_accuracy,
            'data_quality': factors.data_quality
        }
        dominant_factor = max(factor_values, key=factor_values.get)
        dominant_value = factor_values[dominant_factor]
        
        # Generate explanation based on dominant factor
        if dominant_factor == 'signal_strength':
            if dominant_value >= 0.8:
                strength_desc = "strong"
            elif dominant_value >= 0.6:
                strength_desc = "moderate"
            else:
                strength_desc = "weak"
            
            explanation = (
                f"This insight has {level_desc} ({score:.0%}) based primarily on "
                f"a {strength_desc} signal strength ({dominant_value:.0%}). "
            )
        elif dominant_factor == 'historical_accuracy':
            if dominant_value >= 0.8:
                accuracy_desc = "excellent"
            elif dominant_value >= 0.6:
                accuracy_desc = "good"
            else:
                accuracy_desc = "moderate"
            
            explanation = (
                f"This insight has {level_desc} ({score:.0%}) supported by "
                f"{accuracy_desc} historical accuracy ({dominant_value:.0%}) for similar {signal_type} signals. "
            )
        else:  # data_quality
            if dominant_value >= 0.9:
                quality_desc = "high-quality"
            elif dominant_value >= 0.7:
                quality_desc = "reliable"
            else:
                quality_desc = "acceptable"
            
            explanation = (
                f"This insight has {level_desc} ({score:.0%}) based on "
                f"{quality_desc} blockchain data ({dominant_value:.0%}). "
            )
        
        # Add context about other factors
        if factors.signal_strength < 0.5:
            explanation += "The signal strength is relatively weak, which lowers confidence. "
        if factors.historical_accuracy < 0.6:
            explanation += "Historical accuracy for this signal type is still being established. "
        if factors.data_quality < 0.8:
            explanation += "Some data quality considerations affect the overall confidence. "
        
        return explanation.strip()
    
    @staticmethod
    def _generate_supporting_evidence(
        factors: ConfidenceFactors,
        signal_type: str,
        signal_data: Dict[str, Any]
    ) -> List[str]:
        """Generate supporting evidence list"""
        evidence = []
        
        # Signal strength evidence
        signal_strength = factors.signal_strength
        if signal_strength >= 0.8:
            evidence.append(
                f"Strong {signal_type} signal detected with {signal_strength:.0%} strength"
            )
        elif signal_strength >= 0.6:
            evidence.append(
                f"Moderate {signal_type} signal with {signal_strength:.0%} strength"
            )
        else:
            evidence.append(
                f"Weak {signal_type} signal with {signal_strength:.0%} strength"
            )
        
        # Add signal-specific evidence
        if signal_type == 'mempool':
            if 'change_24h' in signal_data:
                change = signal_data['change_24h']
                evidence.append(
                    f"Mempool fees changed {abs(change):.1f}% in 24 hours"
                )
        elif signal_type == 'exchange':
            if 'std_dev_multiple' in signal_data:
                std_dev = signal_data['std_dev_multiple']
                evidence.append(
                    f"Exchange flow is {std_dev:.1f}x standard deviations from average"
                )
        elif signal_type == 'miner':
            if 'balance_change' in signal_data:
                change = signal_data['balance_change']
                evidence.append(
                    f"Miner treasury changed by {abs(change):.2f} BTC"
                )
        elif signal_type == 'whale':
            if 'streak_days' in signal_data:
                streak = signal_data['streak_days']
                evidence.append(
                    f"Accumulation streak of {streak} consecutive days"
                )
        elif signal_type == 'predictive':
            if 'model_confidence' in signal_data:
                confidence = signal_data['model_confidence']
                evidence.append(
                    f"Predictive model confidence: {confidence:.0%}"
                )
        
        # Historical accuracy evidence
        historical_accuracy = factors.historical_accuracy
        if historical_accuracy >= 0.8:
            evidence.append(
                f"Historical accuracy of {historical_accuracy:.0%} for {signal_type} signals"
            )
        elif historical_accuracy >= 0.6:
            evidence.append(
                f"Moderate historical accuracy of {historical_accuracy:.0%} for this signal type"
            )
        else:
            evidence.append(
                f"Limited historical data with {historical_accuracy:.0%} accuracy"
            )
        
        # Data quality evidence
        data_quality = factors.data_quality
        if data_quality >= 0.9:
            evidence.append(
                "High-quality blockchain data with complete transaction records"
            )
        elif data_quality >= 0.7:
            evidence.append(
                "Reliable blockchain data with minor gaps"
            )
        else:
            evidence.append(
                "Data quality considerations due to incomplete records"
            )
        
        # Add block confirmation evidence
        if 'block_height' in signal_data:
            block_height = signal_data['block_height']
            evidence.append(
                f"Signal confirmed at block height {block_height}"
            )
        
        return evidence
    
    @staticmethod
    def format_for_display(explainability: ExplainabilitySummary) -> str:
        """Format explainability summary for display"""
        output = []
        
        # Add explanation
        output.append("Confidence Explanation:")
        output.append(explainability.explanation)
        output.append("")
        
        # Add factors
        output.append("Confidence Factors:")
        for factor, value in explainability.confidence_factors.items():
            factor_name = factor.replace('_', ' ').title()
            output.append(f"  • {factor_name}: {value:.0%}")
        output.append("")
        
        # Add supporting evidence
        output.append("Supporting Evidence:")
        for i, evidence in enumerate(explainability.supporting_evidence, 1):
            output.append(f"  {i}. {evidence}")
        
        return "\n".join(output)
    
    @staticmethod
    def generate_short_explanation(confidence_score: ConfidenceScore) -> str:
        """Generate a short one-line explanation"""
        score = confidence_score.score
        factors = confidence_score.factors
        
        # Find highest factor
        factor_values = {
            'signal strength': factors.signal_strength,
            'historical accuracy': factors.historical_accuracy,
            'data quality': factors.data_quality
        }
        highest_factor = max(factor_values, key=factor_values.get)
        highest_value = factor_values[highest_factor]
        
        return f"Confidence {score:.0%} based on {highest_factor} ({highest_value:.0%})"
