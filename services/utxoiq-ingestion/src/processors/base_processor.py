"""
Base SignalProcessor abstract class
Defines the interface for all signal processors
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models import Signal, BlockData


class ProcessorConfig:
    """Configuration for signal processors"""
    
    def __init__(
        self,
        enabled: bool = True,
        confidence_threshold: float = 0.7,
        time_window: str = "24h",
        **kwargs
    ):
        self.enabled = enabled
        self.confidence_threshold = confidence_threshold
        self.time_window = time_window
        # Store any additional config parameters
        for key, value in kwargs.items():
            setattr(self, key, value)


class ProcessingContext:
    """Context data for signal processing"""
    
    def __init__(
        self,
        block: BlockData,
        historical_data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        self.block = block
        self.historical_data = historical_data or {}
        self.correlation_id = correlation_id
        self.timestamp = datetime.utcnow()


class SignalProcessor(ABC):
    """
    Abstract base class for all signal processors
    
    Each processor analyzes blockchain data and generates signals
    with confidence scores above a configurable threshold.
    """
    
    def __init__(self, config: ProcessorConfig):
        """
        Initialize signal processor with configuration
        
        Args:
            config: Processor configuration including enabled flag and thresholds
        """
        self.config = config
        self.enabled = config.enabled
        self.confidence_threshold = config.confidence_threshold
        self.signal_type = "unknown"  # Override in subclasses
    
    @abstractmethod
    async def process_block(
        self,
        block: BlockData,
        context: ProcessingContext
    ) -> List[Signal]:
        """
        Analyze block data and generate signals
        
        This method must be implemented by all signal processors.
        It should analyze the block data and return a list of signals
        that meet or exceed the confidence threshold.
        
        Args:
            block: Block data to process
            context: Processing context with historical data and correlation ID
            
        Returns:
            List of signals above confidence threshold
            
        Raises:
            Exception: If processing fails (should be caught by orchestrator)
        """
        pass
    
    def calculate_confidence(
        self,
        metrics: Dict[str, Any],
        base_confidence: float = 0.5
    ) -> float:
        """
        Calculate confidence score for a signal
        
        This helper method provides a standard way to calculate confidence
        scores based on various metrics. Subclasses can override or extend
        this method for custom confidence calculations.
        
        Args:
            metrics: Dictionary of metrics to evaluate
            base_confidence: Starting confidence score (default 0.5)
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = base_confidence
        
        # Boost confidence for high data quality
        if metrics.get("data_quality") == "high":
            confidence += 0.2
        elif metrics.get("data_quality") == "medium":
            confidence += 0.1
        
        # Boost confidence for strong signals
        if metrics.get("signal_strength") == "strong":
            confidence += 0.2
        elif metrics.get("signal_strength") == "moderate":
            confidence += 0.1
        
        # Boost confidence for known entities
        if metrics.get("entity_known", False):
            confidence += 0.1
        
        # Boost confidence for significant amounts
        amount = metrics.get("amount_btc", 0)
        if amount > 1000:
            confidence += 0.15
        elif amount > 500:
            confidence += 0.1
        elif amount > 100:
            confidence += 0.05
        
        # Reduce confidence for low transaction counts
        tx_count = metrics.get("transaction_count", 0)
        if tx_count < 3:
            confidence -= 0.1
        
        # Reduce confidence for extreme deviations (may be data errors)
        deviation = metrics.get("deviation_from_mean", 0)
        if deviation > 5.0:
            confidence -= 0.1
        
        # Ensure confidence stays within bounds
        return max(0.0, min(1.0, confidence))
    
    def should_generate_signal(self, confidence: float) -> bool:
        """
        Determine if a signal should be generated based on confidence
        
        Args:
            confidence: Calculated confidence score
            
        Returns:
            True if signal meets threshold, False otherwise
        """
        return confidence >= self.confidence_threshold
    
    def create_signal(
        self,
        signal_type: str,
        block_height: int,
        confidence: float,
        metadata: Dict[str, Any],
        transaction_ids: Optional[List[str]] = None,
        entity_ids: Optional[List[str]] = None
    ) -> Signal:
        """
        Create a signal object with standard structure
        
        Args:
            signal_type: Type of signal (mempool, exchange, miner, whale, treasury, predictive)
            block_height: Block height where signal was detected
            confidence: Confidence score (0.0 to 1.0)
            metadata: Signal-specific metadata
            transaction_ids: List of transaction IDs as evidence
            entity_ids: List of entity IDs involved
            
        Returns:
            Signal object ready for persistence
        """
        from ..models import SignalType
        
        # Map string to SignalType enum
        type_mapping = {
            "mempool": SignalType.MEMPOOL,
            "exchange": SignalType.EXCHANGE,
            "miner": SignalType.MINER,
            "whale": SignalType.WHALE,
            "predictive": SignalType.PREDICTIVE
        }
        
        return Signal(
            type=type_mapping.get(signal_type, SignalType.MEMPOOL),
            strength=confidence,
            data=metadata,
            block_height=block_height,
            transaction_ids=transaction_ids or [],
            entity_ids=entity_ids or [],
            is_predictive=(signal_type == "predictive")
        )
    
    def __repr__(self) -> str:
        """String representation of processor"""
        return (
            f"{self.__class__.__name__}("
            f"enabled={self.enabled}, "
            f"threshold={self.confidence_threshold})"
        )
