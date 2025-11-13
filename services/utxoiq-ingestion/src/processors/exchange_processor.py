"""
Exchange flow detection module
Implements entity-tagged transaction analysis and anomaly detection
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from scipy import stats
from ..models import Signal, SignalType, ExchangeFlowData, BlockData
from ..config import settings
from .base_processor import SignalProcessor, ProcessorConfig, ProcessingContext


class ExchangeProcessor(SignalProcessor):
    """
    Processes exchange flow data to detect unusual inflow/outflow patterns
    """
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        if config is None:
            config = ProcessorConfig(
                enabled=getattr(settings, 'exchange_processor_enabled', True),
                confidence_threshold=getattr(settings, 'confidence_threshold', 0.7),
                time_window=getattr(settings, 'exchange_time_window', '24h')
            )
        super().__init__(config)
        self.signal_type = "exchange"
        self.anomaly_threshold = getattr(settings, 'exchange_flow_anomaly_threshold', 2.5)
        self.historical_window = 144  # ~24 hours of blocks
        
    def analyze_entity_flows(
        self,
        flow_data: ExchangeFlowData,
        historical_flows: Optional[List[ExchangeFlowData]] = None
    ) -> Dict[str, any]:
        """
        Analyze exchange flow patterns for a specific entity
        
        Args:
            flow_data: Current flow data for entity
            historical_flows: Historical flow data for comparison
            
        Returns:
            Dictionary with flow analysis metrics
        """
        analysis = {
            "entity_id": flow_data.entity_id,
            "entity_name": flow_data.entity_name,
            "current_inflow": flow_data.inflow_btc,
            "current_outflow": flow_data.outflow_btc,
            "net_flow": flow_data.net_flow_btc,
            "is_anomaly": False,
            "anomaly_type": None,
            "z_score": 0.0,
            "historical_mean": 0.0,
            "historical_std": 0.0
        }
        
        if not historical_flows or len(historical_flows) < 10:
            # Insufficient historical data
            return analysis
        
        # Calculate historical statistics for inflows
        historical_inflows = [f.inflow_btc for f in historical_flows]
        mean_inflow = np.mean(historical_inflows)
        std_inflow = np.std(historical_inflows)
        
        analysis["historical_mean"] = float(mean_inflow)
        analysis["historical_std"] = float(std_inflow)
        
        # Calculate z-score for current inflow
        if std_inflow > 0:
            z_score = (flow_data.inflow_btc - mean_inflow) / std_inflow
            analysis["z_score"] = float(z_score)
            
            # Detect anomaly if z-score exceeds threshold
            if abs(z_score) > self.anomaly_threshold:
                analysis["is_anomaly"] = True
                analysis["anomaly_type"] = (
                    "inflow_spike" if z_score > 0 else "inflow_drop"
                )
        
        return analysis
    
    def detect_unusual_patterns(
        self,
        flow_data: ExchangeFlowData,
        historical_flows: List[ExchangeFlowData]
    ) -> Dict[str, any]:
        """
        Detect unusual patterns in exchange flows
        
        Args:
            flow_data: Current flow data
            historical_flows: Historical flow data
            
        Returns:
            Dictionary with pattern detection results
        """
        patterns = {
            "large_single_transaction": False,
            "rapid_accumulation": False,
            "unusual_timing": False,
            "volume_spike": False
        }
        
        if not historical_flows:
            return patterns
        
        # Check for large single transaction relative to total
        if flow_data.transaction_count > 0:
            avg_tx_size = flow_data.inflow_btc / flow_data.transaction_count
            historical_avg_sizes = [
                f.inflow_btc / f.transaction_count 
                for f in historical_flows 
                if f.transaction_count > 0
            ]
            
            if historical_avg_sizes:
                mean_size = np.mean(historical_avg_sizes)
                if avg_tx_size > mean_size * 5:
                    patterns["large_single_transaction"] = True
        
        # Check for volume spike
        historical_volumes = [f.inflow_btc for f in historical_flows]
        if historical_volumes:
            mean_volume = np.mean(historical_volumes)
            if flow_data.inflow_btc > mean_volume * 3:
                patterns["volume_spike"] = True
        
        # Check for rapid accumulation (net positive flow)
        if flow_data.net_flow_btc > 0:
            recent_net_flows = [
                f.net_flow_btc 
                for f in historical_flows[-10:] 
                if f.net_flow_btc > 0
            ]
            if len(recent_net_flows) >= 7:
                patterns["rapid_accumulation"] = True
        
        return patterns
    
    def calculate_confidence_score(
        self,
        flow_data: ExchangeFlowData,
        analysis: Dict[str, any],
        patterns: Dict[str, any]
    ) -> float:
        """
        Calculate confidence score for exchange flow signal
        
        Args:
            flow_data: Current flow data
            analysis: Flow analysis results
            patterns: Pattern detection results
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.5
        
        # Increase confidence for known entities
        if flow_data.entity_name and flow_data.entity_name != "unknown":
            confidence += 0.2
        
        # Increase confidence for strong anomalies
        if analysis.get("is_anomaly"):
            z_score = abs(analysis.get("z_score", 0))
            if z_score > 3.0:
                confidence += 0.2
            elif z_score > 2.5:
                confidence += 0.1
        
        # Increase confidence if multiple patterns detected
        pattern_count = sum(1 for v in patterns.values() if v)
        if pattern_count >= 2:
            confidence += 0.15
        elif pattern_count == 1:
            confidence += 0.05
        
        # Increase confidence for significant volume
        if flow_data.inflow_btc > 100:  # > 100 BTC
            confidence += 0.1
        
        # Decrease confidence for very few transactions
        if flow_data.transaction_count < 3:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def create_evidence_citations(
        self,
        flow_data: ExchangeFlowData
    ) -> List[str]:
        """
        Create evidence citations for exchange flow signal
        
        Args:
            flow_data: Flow data with transaction IDs
            
        Returns:
            List of transaction IDs as evidence
        """
        # Return up to 10 transaction IDs as evidence
        return flow_data.transaction_ids[:10]
    
    async def process_block(
        self,
        block: BlockData,
        context: ProcessingContext
    ) -> List[Signal]:
        """
        Process block and generate exchange flow signals
        
        Args:
            block: Block data to process
            context: Processing context with historical data
            
        Returns:
            List of exchange signals above confidence threshold
        """
        signals = []
        
        # Extract exchange flow data from context
        exchange_flows = context.historical_data.get('exchange_flows', [])
        if not exchange_flows:
            return signals
        
        # Get historical flows for comparison
        historical_flows = context.historical_data.get('historical_exchange_flows', [])
        
        # Generate signal for each exchange flow
        for flow in exchange_flows:
            signal = self.generate_exchange_signal(flow, historical_flows)
            
            # Only include if above threshold
            if signal and self.should_generate_signal(signal.strength):
                signals.append(signal)
        
        return signals
    
    def generate_exchange_signal(
        self,
        flow_data: ExchangeFlowData,
        historical_flows: Optional[List[ExchangeFlowData]] = None
    ) -> Signal:
        """
        Generate exchange inflow spike signal with evidence citations
        
        Args:
            flow_data: Current exchange flow data
            historical_flows: Historical flow data for comparison
            
        Returns:
            Signal object with exchange flow analysis
        """
        # Analyze flows
        analysis = self.analyze_entity_flows(flow_data, historical_flows)
        
        # Detect patterns
        patterns = {}
        if historical_flows:
            patterns = self.detect_unusual_patterns(flow_data, historical_flows)
        
        # Calculate confidence
        confidence = self.calculate_confidence_score(
            flow_data,
            analysis,
            patterns
        )
        
        # Determine flow type based on net flow
        flow_type = "inflow" if flow_data.net_flow_btc > 0 else "outflow"
        if abs(flow_data.net_flow_btc) < 1.0:  # Minimal net flow
            flow_type = "balanced"
        
        # Determine primary amount (inflow or outflow)
        amount_btc = flow_data.inflow_btc if flow_type == "inflow" else flow_data.outflow_btc
        
        # Build signal data with required metadata fields
        signal_data = {
            "entity_id": flow_data.entity_id,
            "entity_name": flow_data.entity_name,
            "flow_type": flow_type,
            "amount_btc": amount_btc,
            "tx_count": flow_data.transaction_count,
            "inflow_btc": flow_data.inflow_btc,
            "outflow_btc": flow_data.outflow_btc,
            "net_flow_btc": flow_data.net_flow_btc,
            "is_anomaly": analysis.get("is_anomaly", False),
            "anomaly_type": analysis.get("anomaly_type"),
            "z_score": analysis.get("z_score", 0.0),
            "historical_mean": analysis.get("historical_mean", 0.0),
            "patterns_detected": patterns,
            "timestamp": flow_data.timestamp.isoformat()
        }
        
        # Get evidence citations
        evidence_tx_ids = self.create_evidence_citations(flow_data)
        
        return Signal(
            type=SignalType.EXCHANGE,
            strength=confidence,
            data=signal_data,
            block_height=flow_data.block_height,
            transaction_ids=evidence_tx_ids,
            entity_ids=[flow_data.entity_id],
            is_predictive=False
        )
