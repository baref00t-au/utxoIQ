"""
Main SignalProcessor class coordinating all signal computation
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import (
    Signal, BlockData, MempoolData, ExchangeFlowData,
    MinerTreasuryData, WhaleActivityData
)
from .processors import (
    MempoolProcessor,
    ExchangeProcessor,
    MinerProcessor,
    WhaleProcessor,
    PredictiveAnalytics
)
from .config import settings
import logging

logger = logging.getLogger(__name__)


class SignalProcessor:
    """
    Main signal processing coordinator
    Orchestrates all signal computation methods
    """
    
    def __init__(self):
        """Initialize all signal processors"""
        self.mempool_processor = MempoolProcessor()
        self.exchange_processor = ExchangeProcessor()
        self.miner_processor = MinerProcessor()
        self.whale_processor = WhaleProcessor()
        self.predictive_analytics = PredictiveAnalytics()
        
        self.confidence_threshold = settings.confidence_threshold
        
        logger.info("SignalProcessor initialized with all processors")
    
    def process_block(
        self,
        block_data: BlockData,
        mempool_data: Optional[MempoolData] = None,
        exchange_flows: Optional[List[ExchangeFlowData]] = None,
        miner_data: Optional[List[MinerTreasuryData]] = None,
        whale_data: Optional[List[WhaleActivityData]] = None
    ) -> List[Signal]:
        """
        Process a new block and generate all applicable signals
        
        Args:
            block_data: Block information
            mempool_data: Current mempool snapshot
            exchange_flows: Exchange flow data
            miner_data: Miner treasury data
            whale_data: Whale activity data
            
        Returns:
            List of generated signals
        """
        signals = []
        
        logger.info(f"Processing block {block_data.height}")
        
        # Process mempool signals if data available
        if mempool_data:
            try:
                mempool_signal = self.compute_mempool_signals(mempool_data)
                if mempool_signal and mempool_signal.strength >= self.confidence_threshold:
                    signals.append(mempool_signal)
                    logger.info(f"Generated mempool signal with confidence {mempool_signal.strength}")
            except Exception as e:
                logger.error(f"Error processing mempool signal: {e}")
        
        # Process exchange flow signals if data available
        if exchange_flows:
            for flow in exchange_flows:
                try:
                    exchange_signal = self.detect_exchange_flows(flow)
                    if exchange_signal and exchange_signal.strength >= self.confidence_threshold:
                        signals.append(exchange_signal)
                        logger.info(f"Generated exchange signal for {flow.entity_name}")
                except Exception as e:
                    logger.error(f"Error processing exchange signal: {e}")
        
        # Process miner treasury signals if data available
        if miner_data:
            for miner in miner_data:
                try:
                    miner_signal = self.analyze_miner_treasury(miner)
                    if miner_signal and miner_signal.strength >= self.confidence_threshold:
                        signals.append(miner_signal)
                        logger.info(f"Generated miner signal for {miner.entity_name}")
                except Exception as e:
                    logger.error(f"Error processing miner signal: {e}")
        
        # Process whale accumulation signals if data available
        if whale_data:
            for whale in whale_data:
                try:
                    whale_signal = self.track_whale_accumulation(whale)
                    if whale_signal and whale_signal.strength >= self.confidence_threshold:
                        signals.append(whale_signal)
                        logger.info(f"Generated whale signal for {whale.address}")
                except Exception as e:
                    logger.error(f"Error processing whale signal: {e}")
        
        logger.info(f"Generated {len(signals)} signals for block {block_data.height}")
        return signals
    
    def compute_mempool_signals(
        self,
        mempool_data: MempoolData,
        historical_data: Optional[List[MempoolData]] = None
    ) -> Signal:
        """
        Compute mempool-related signals
        
        Args:
            mempool_data: Current mempool snapshot
            historical_data: Historical mempool data
            
        Returns:
            Mempool signal
        """
        return self.mempool_processor.generate_mempool_signal(
            mempool_data,
            historical_data
        )
    
    def detect_exchange_flows(
        self,
        flow_data: ExchangeFlowData,
        historical_flows: Optional[List[ExchangeFlowData]] = None
    ) -> Signal:
        """
        Detect exchange flow anomalies
        
        Args:
            flow_data: Current exchange flow data
            historical_flows: Historical flow data
            
        Returns:
            Exchange flow signal
        """
        return self.exchange_processor.generate_exchange_signal(
            flow_data,
            historical_flows
        )
    
    def analyze_miner_treasury(
        self,
        miner_data: MinerTreasuryData,
        historical_data: Optional[List[MinerTreasuryData]] = None
    ) -> Signal:
        """
        Analyze miner treasury changes
        
        Args:
            miner_data: Current miner treasury data
            historical_data: Historical treasury data
            
        Returns:
            Miner treasury signal
        """
        return self.miner_processor.generate_miner_signal(
            miner_data,
            historical_data
        )
    
    def track_whale_accumulation(
        self,
        whale_data: WhaleActivityData,
        historical_data: Optional[List[WhaleActivityData]] = None
    ) -> Signal:
        """
        Track whale accumulation patterns
        
        Args:
            whale_data: Current whale activity data
            historical_data: Historical whale data
            
        Returns:
            Whale accumulation signal
        """
        return self.whale_processor.generate_whale_signal(
            whale_data,
            historical_data
        )
    
    def generate_predictive_signals(
        self,
        mempool_data: MempoolData,
        historical_mempool: List[MempoolData],
        exchange_flows: List[ExchangeFlowData],
        current_flow: ExchangeFlowData
    ) -> List[Signal]:
        """
        Generate predictive analytics signals
        
        Args:
            mempool_data: Current mempool data
            historical_mempool: Historical mempool data
            exchange_flows: Historical exchange flows
            current_flow: Current exchange flow
            
        Returns:
            List of predictive signals
        """
        predictive_signals = []
        
        # Generate fee forecast signal
        try:
            fee_signal = self.predictive_analytics.generate_fee_forecast_signal(
                historical_mempool,
                mempool_data
            )
            if fee_signal.strength >= self.confidence_threshold:
                predictive_signals.append(fee_signal)
                logger.info("Generated fee forecast signal")
        except Exception as e:
            logger.error(f"Error generating fee forecast: {e}")
        
        # Generate liquidity pressure signal
        try:
            liquidity_signal = self.predictive_analytics.generate_liquidity_pressure_signal(
                exchange_flows,
                current_flow
            )
            if liquidity_signal.strength >= self.confidence_threshold:
                predictive_signals.append(liquidity_signal)
                logger.info("Generated liquidity pressure signal")
        except Exception as e:
            logger.error(f"Error generating liquidity pressure: {e}")
        
        return predictive_signals
    
    def filter_signals_by_confidence(
        self,
        signals: List[Signal],
        min_confidence: Optional[float] = None
    ) -> List[Signal]:
        """
        Filter signals by confidence threshold
        
        Args:
            signals: List of signals to filter
            min_confidence: Minimum confidence threshold (uses default if None)
            
        Returns:
            Filtered list of signals
        """
        threshold = min_confidence if min_confidence is not None else self.confidence_threshold
        return [s for s in signals if s.strength >= threshold]
