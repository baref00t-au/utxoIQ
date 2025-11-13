"""
Mempool signal processing module
Implements fee quantile calculation and block inclusion time estimation
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from ..models import Signal, SignalType, MempoolData, BlockData
from ..config import settings
from .base_processor import SignalProcessor, ProcessorConfig, ProcessingContext


class MempoolProcessor(SignalProcessor):
    """
    Processes mempool data to generate signals about fee conditions
    and block inclusion time estimates
    """
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        if config is None:
            config = ProcessorConfig(
                enabled=getattr(settings, 'mempool_processor_enabled', True),
                confidence_threshold=getattr(settings, 'confidence_threshold', 0.7),
                time_window=getattr(settings, 'mempool_time_window', '1h')
            )
        super().__init__(config)
        self.signal_type = "mempool"
        self.spike_threshold = getattr(settings, 'mempool_spike_threshold', 0.2)
        self.historical_window = 144  # ~24 hours of blocks
        
    def calculate_fee_quantiles(
        self, 
        fee_rates: List[float]
    ) -> Dict[str, float]:
        """
        Calculate fee quantiles from mempool transactions
        
        Args:
            fee_rates: List of fee rates in sat/vB
            
        Returns:
            Dictionary with quantile values (p10, p25, p50, p75, p90)
        """
        if not fee_rates:
            return {
                "p10": 0.0,
                "p25": 0.0,
                "p50": 0.0,
                "p75": 0.0,
                "p90": 0.0
            }
        
        fee_array = np.array(fee_rates)
        
        return {
            "p10": float(np.percentile(fee_array, 10)),
            "p25": float(np.percentile(fee_array, 25)),
            "p50": float(np.percentile(fee_array, 50)),
            "p75": float(np.percentile(fee_array, 75)),
            "p90": float(np.percentile(fee_array, 90))
        }
    
    def estimate_block_inclusion_time(
        self,
        fee_rate: float,
        current_quantiles: Dict[str, float],
        avg_block_time_minutes: float = 10.0
    ) -> Dict[str, float]:
        """
        Estimate time until transaction inclusion based on fee rate
        
        Args:
            fee_rate: Transaction fee rate in sat/vB
            current_quantiles: Current mempool fee quantiles
            avg_block_time_minutes: Average block time in minutes
            
        Returns:
            Dictionary with estimated blocks and minutes until inclusion
        """
        # Determine priority tier based on fee rate
        if fee_rate >= current_quantiles["p90"]:
            estimated_blocks = 1
        elif fee_rate >= current_quantiles["p75"]:
            estimated_blocks = 2
        elif fee_rate >= current_quantiles["p50"]:
            estimated_blocks = 3
        elif fee_rate >= current_quantiles["p25"]:
            estimated_blocks = 6
        else:
            estimated_blocks = 12
        
        estimated_minutes = estimated_blocks * avg_block_time_minutes
        
        return {
            "estimated_blocks": float(estimated_blocks),
            "estimated_minutes": estimated_minutes,
            "priority_tier": self._get_priority_tier(fee_rate, current_quantiles)
        }
    
    def _get_priority_tier(
        self,
        fee_rate: float,
        quantiles: Dict[str, float]
    ) -> str:
        """Determine priority tier for fee rate"""
        if fee_rate >= quantiles["p90"]:
            return "high"
        elif fee_rate >= quantiles["p50"]:
            return "medium"
        else:
            return "low"
    
    def calculate_confidence_score(
        self,
        mempool_data: MempoolData,
        historical_avg: Optional[float] = None
    ) -> float:
        """
        Calculate confidence score for mempool signal
        
        Args:
            mempool_data: Current mempool snapshot
            historical_avg: Historical average fee rate
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence on data quality
        confidence = 0.5
        
        # Increase confidence if we have sufficient transactions
        if mempool_data.transaction_count > 1000:
            confidence += 0.2
        elif mempool_data.transaction_count > 500:
            confidence += 0.1
        
        # Increase confidence if fee distribution is stable
        if mempool_data.fee_quantiles:
            p50 = mempool_data.fee_quantiles.get("p50", 0)
            p90 = mempool_data.fee_quantiles.get("p90", 0)
            
            if p90 > 0 and p50 > 0:
                ratio = p90 / p50
                # Stable if ratio is between 1.5 and 3.0
                if 1.5 <= ratio <= 3.0:
                    confidence += 0.2
                elif ratio < 1.5 or ratio > 5.0:
                    confidence -= 0.1
        
        # Compare to historical average if available
        if historical_avg and historical_avg > 0:
            current_avg = mempool_data.avg_fee_rate
            deviation = abs(current_avg - historical_avg) / historical_avg
            
            # Lower confidence for extreme deviations
            if deviation > 2.0:
                confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    async def process_block(
        self,
        block: BlockData,
        context: ProcessingContext
    ) -> List[Signal]:
        """
        Process block and generate mempool signals
        
        Args:
            block: Block data to process
            context: Processing context with historical data
            
        Returns:
            List of mempool signals above confidence threshold
        """
        signals = []
        
        # Extract mempool data from context
        mempool_data = context.historical_data.get('mempool_data')
        if not mempool_data:
            return signals
        
        # Get historical mempool data for comparison
        historical_mempool = context.historical_data.get('historical_mempool', [])
        
        # Generate signal
        signal = self.generate_mempool_signal(mempool_data, historical_mempool)
        
        # Only include if above threshold
        if signal and self.should_generate_signal(signal.strength):
            signals.append(signal)
        
        return signals
    
    def generate_mempool_signal(
        self,
        mempool_data: MempoolData,
        historical_data: Optional[List[MempoolData]] = None
    ) -> Signal:
        """
        Generate mempool nowcast signal with confidence scoring
        
        Args:
            mempool_data: Current mempool snapshot
            historical_data: Historical mempool snapshots for comparison
            
        Returns:
            Signal object with mempool analysis
        """
        # Calculate historical average if data available
        historical_avg = None
        if historical_data:
            avg_fees = [d.avg_fee_rate for d in historical_data]
            historical_avg = np.mean(avg_fees) if avg_fees else None
        
        # Calculate confidence score
        confidence = self.calculate_confidence_score(
            mempool_data,
            historical_avg
        )
        
        # Detect fee spike
        is_spike = False
        spike_magnitude = 0.0
        if historical_avg and historical_avg > 0:
            spike_magnitude = (
                mempool_data.avg_fee_rate - historical_avg
            ) / historical_avg
            is_spike = spike_magnitude > self.spike_threshold
        
        # Calculate fee rate change percentage
        fee_rate_change_pct = 0.0
        if historical_avg and historical_avg > 0:
            fee_rate_change_pct = (
                (mempool_data.avg_fee_rate - historical_avg) / historical_avg
            ) * 100
        
        # Get median fee rate from quantiles
        fee_rate_median = mempool_data.fee_quantiles.get("p50", mempool_data.avg_fee_rate)
        
        # Build signal data with required metadata fields
        signal_data = {
            "fee_rate_median": fee_rate_median,
            "fee_rate_change_pct": fee_rate_change_pct,
            "mempool_size_mb": mempool_data.mempool_size_bytes / (1024 * 1024),
            "tx_count": mempool_data.transaction_count,
            "fee_quantiles": mempool_data.fee_quantiles,
            "avg_fee_rate": mempool_data.avg_fee_rate,
            "is_spike": is_spike,
            "spike_magnitude": spike_magnitude,
            "historical_avg": historical_avg,
            "timestamp": mempool_data.timestamp.isoformat()
        }
        
        # Add inclusion time estimates for common fee rates
        if mempool_data.fee_quantiles:
            signal_data["inclusion_estimates"] = {
                "p50_fee": self.estimate_block_inclusion_time(
                    mempool_data.fee_quantiles["p50"],
                    mempool_data.fee_quantiles
                ),
                "p75_fee": self.estimate_block_inclusion_time(
                    mempool_data.fee_quantiles["p75"],
                    mempool_data.fee_quantiles
                )
            }
        
        return Signal(
            type=SignalType.MEMPOOL,
            strength=confidence,
            data=signal_data,
            block_height=mempool_data.block_height,
            transaction_ids=[],
            entity_ids=[],
            is_predictive=False
        )
