"""
Confidence scoring and filtering with explainability
Calculates confidence scores based on signal metrics and context
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence level categories"""
    HIGH = "high"  # >= 0.85
    MEDIUM = "medium"  # 0.70 - 0.84
    LOW = "low"  # < 0.70


@dataclass
class ConfidenceFactors:
    """Individual factors contributing to confidence score"""
    signal_strength: float  # 0-1
    historical_accuracy: float  # 0-1
    data_quality: float  # 0-1
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'signal_strength': self.signal_strength,
            'historical_accuracy': self.historical_accuracy,
            'data_quality': self.data_quality
        }


@dataclass
class ConfidenceScore:
    """Complete confidence score with factors and explanation"""
    score: float  # 0-1
    level: ConfidenceLevel
    factors: ConfidenceFactors
    should_publish: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'score': self.score,
            'level': self.level.value,
            'factors': self.factors.to_dict(),
            'should_publish': self.should_publish
        }


class ConfidenceScorer:
    """Calculates confidence scores for insights"""
    
    # Confidence threshold for auto-publication
    PUBLICATION_THRESHOLD = 0.7
    
    # Weights for confidence factors
    SIGNAL_STRENGTH_WEIGHT = 0.4
    HISTORICAL_ACCURACY_WEIGHT = 0.35
    DATA_QUALITY_WEIGHT = 0.25
    
    # Anomaly detection thresholds
    MEMPOOL_SPIKE_THRESHOLD = 3.0  # standard deviations
    
    @staticmethod
    def calculate_confidence(
        signal_strength: float,
        historical_accuracy: float,
        data_quality: float,
        is_anomaly: bool = False
    ) -> ConfidenceScore:
        """
        Calculate overall confidence score from individual factors
        
        Args:
            signal_strength: Strength of the signal (0-1)
            historical_accuracy: Historical accuracy of similar signals (0-1)
            data_quality: Quality of underlying data (0-1)
            is_anomaly: Whether data anomaly was detected
            
        Returns:
            ConfidenceScore with overall score and factors
        """
        # Validate inputs
        signal_strength = max(0.0, min(1.0, signal_strength))
        historical_accuracy = max(0.0, min(1.0, historical_accuracy))
        data_quality = max(0.0, min(1.0, data_quality))
        
        # Calculate weighted score
        score = (
            signal_strength * ConfidenceScorer.SIGNAL_STRENGTH_WEIGHT +
            historical_accuracy * ConfidenceScorer.HISTORICAL_ACCURACY_WEIGHT +
            data_quality * ConfidenceScorer.DATA_QUALITY_WEIGHT
        )
        
        # Apply anomaly penalty if detected
        if is_anomaly:
            score *= 0.8  # Reduce confidence by 20% during anomalies
        
        # Ensure score is in valid range
        score = max(0.0, min(1.0, score))
        
        # Determine confidence level
        if score >= 0.85:
            level = ConfidenceLevel.HIGH
        elif score >= 0.70:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW
        
        # Determine if should publish
        should_publish = score >= ConfidenceScorer.PUBLICATION_THRESHOLD and not is_anomaly
        
        factors = ConfidenceFactors(
            signal_strength=signal_strength,
            historical_accuracy=historical_accuracy,
            data_quality=data_quality
        )
        
        return ConfidenceScore(
            score=score,
            level=level,
            factors=factors,
            should_publish=should_publish
        )
    
    @staticmethod
    def calculate_signal_strength(signal_data: Dict[str, Any], signal_type: str) -> float:
        """
        Calculate signal strength based on signal type and data
        
        Args:
            signal_data: Raw signal data
            signal_type: Type of signal (mempool, exchange, miner, whale, predictive)
            
        Returns:
            Signal strength (0-1)
        """
        if signal_type == 'mempool':
            return ConfidenceScorer._calculate_mempool_strength(signal_data)
        elif signal_type == 'exchange':
            return ConfidenceScorer._calculate_exchange_strength(signal_data)
        elif signal_type == 'miner':
            return ConfidenceScorer._calculate_miner_strength(signal_data)
        elif signal_type == 'whale':
            return ConfidenceScorer._calculate_whale_strength(signal_data)
        elif signal_type == 'predictive':
            return ConfidenceScorer._calculate_predictive_strength(signal_data)
        else:
            return 0.5  # Default moderate strength
    
    @staticmethod
    def _calculate_mempool_strength(signal_data: Dict[str, Any]) -> float:
        """Calculate strength for mempool signals"""
        # Use fee deviation from historical average
        change_24h = abs(signal_data.get('change_24h', 0))
        
        # Normalize to 0-1 scale (100% change = 1.0)
        strength = min(change_24h / 100.0, 1.0)
        
        # Boost if anomaly detected
        if signal_data.get('is_anomaly', False):
            strength = min(strength * 1.2, 1.0)
        
        return strength
    
    @staticmethod
    def _calculate_exchange_strength(signal_data: Dict[str, Any]) -> float:
        """Calculate strength for exchange flow signals"""
        # Use standard deviation multiple
        std_dev_multiple = signal_data.get('std_dev_multiple', 1.0)
        
        # Normalize: 3 std devs = 1.0 strength
        strength = min(std_dev_multiple / 3.0, 1.0)
        
        # Boost for very large flows
        anomaly_score = signal_data.get('anomaly_score', 0)
        if anomaly_score > 0.8:
            strength = min(strength * 1.15, 1.0)
        
        return strength
    
    @staticmethod
    def _calculate_miner_strength(signal_data: Dict[str, Any]) -> float:
        """Calculate strength for miner treasury signals"""
        # Use balance change relative to average
        balance_change = abs(signal_data.get('balance_change', 0))
        avg_change_30d = abs(signal_data.get('avg_change_30d', 1))
        
        if avg_change_30d == 0:
            return 0.5
        
        # Normalize: 2x average = 1.0 strength
        strength = min(balance_change / (avg_change_30d * 2), 1.0)
        
        return strength
    
    @staticmethod
    def _calculate_whale_strength(signal_data: Dict[str, Any]) -> float:
        """Calculate strength for whale accumulation signals"""
        # Use streak length and accumulation rate
        streak_days = signal_data.get('streak_days', 0)
        accumulation_btc = signal_data.get('accumulation_btc', 0)
        
        # Normalize streak: 7 days = 0.5, 14 days = 1.0
        streak_strength = min(streak_days / 14.0, 1.0)
        
        # Normalize accumulation: 100 BTC = 0.5, 500 BTC = 1.0
        accumulation_strength = min(accumulation_btc / 500.0, 1.0)
        
        # Combine factors
        strength = (streak_strength * 0.6 + accumulation_strength * 0.4)
        
        return strength
    
    @staticmethod
    def _calculate_predictive_strength(signal_data: Dict[str, Any]) -> float:
        """Calculate strength for predictive signals"""
        # Use model confidence and historical accuracy
        model_confidence = signal_data.get('model_confidence', 0.5)
        historical_accuracy = signal_data.get('historical_accuracy', 0.5)
        
        # Combine factors
        strength = (model_confidence * 0.6 + historical_accuracy * 0.4)
        
        return strength
    
    @staticmethod
    def calculate_data_quality(signal_data: Dict[str, Any]) -> float:
        """
        Calculate data quality score
        
        Args:
            signal_data: Raw signal data
            
        Returns:
            Data quality score (0-1)
        """
        quality = 1.0
        
        # Check for missing critical fields
        required_fields = ['block_height', 'signal_strength']
        for field in required_fields:
            if field not in signal_data or signal_data[field] is None:
                quality *= 0.8
        
        # Check for data completeness
        if 'transaction_ids' in signal_data:
            tx_ids = signal_data['transaction_ids']
            if not tx_ids or len(tx_ids) == 0:
                quality *= 0.9
        
        # Check for data freshness (blocks should be recent)
        block_height = signal_data.get('block_height', 0)
        if block_height > 0:
            # Assume current block is around 800000 (will be updated in production)
            # Penalize if block is very old
            if block_height < 700000:
                quality *= 0.7
        
        return max(0.0, min(1.0, quality))
    
    @staticmethod
    def detect_quiet_mode(signal_data: Dict[str, Any], signal_type: str) -> Tuple[bool, str]:
        """
        Detect if system should enter quiet mode due to data anomalies
        
        Args:
            signal_data: Raw signal data
            signal_type: Type of signal
            
        Returns:
            Tuple of (should_enter_quiet_mode, reason)
        """
        # Check for mempool spikes
        if signal_type == 'mempool':
            change_24h = abs(signal_data.get('change_24h', 0))
            if change_24h > 300:  # 300% change
                return True, "Extreme mempool volatility detected"
            
            # Check for standard deviation spike
            if signal_data.get('is_anomaly', False):
                std_dev_multiple = signal_data.get('std_dev_multiple', 0)
                if std_dev_multiple > ConfidenceScorer.MEMPOOL_SPIKE_THRESHOLD:
                    return True, f"Mempool spike exceeds {ConfidenceScorer.MEMPOOL_SPIKE_THRESHOLD} standard deviations"
        
        # Check for blockchain reorg indicators
        if 'reorg_detected' in signal_data and signal_data['reorg_detected']:
            return True, "Blockchain reorganization detected"
        
        # Check for data quality issues
        data_quality = ConfidenceScorer.calculate_data_quality(signal_data)
        if data_quality < 0.5:
            return True, "Data quality below acceptable threshold"
        
        return False, ""
    
    @staticmethod
    def get_historical_accuracy(signal_type: str, model_version: str = "1.0.0") -> float:
        """
        Get historical accuracy for a signal type
        This would query BigQuery in production, using defaults for now
        
        Args:
            signal_type: Type of signal
            model_version: Model version
            
        Returns:
            Historical accuracy (0-1)
        """
        # Default accuracies by signal type (would be queried from database)
        default_accuracies = {
            'mempool': 0.82,
            'exchange': 0.78,
            'miner': 0.85,
            'whale': 0.75,
            'predictive': 0.70,
        }
        
        return default_accuracies.get(signal_type, 0.75)
