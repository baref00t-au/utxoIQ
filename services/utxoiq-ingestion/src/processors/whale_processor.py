"""
Whale accumulation detection module
Implements rolling 7-day accumulation pattern analysis and whale identification
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ..models import Signal, SignalType, WhaleActivityData, BlockData
from ..config import settings
from .base_processor import SignalProcessor, ProcessorConfig, ProcessingContext


class WhaleProcessor(SignalProcessor):
    """
    Processes whale activity data to detect accumulation patterns
    """
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        if config is None:
            config = ProcessorConfig(
                enabled=getattr(settings, 'whale_processor_enabled', True),
                confidence_threshold=getattr(settings, 'confidence_threshold', 0.7),
                time_window='7d'
            )
        super().__init__(config)
        self.signal_type = "whale"
        self.whale_threshold = getattr(settings, 'whale_threshold_btc', 1000)
        self.accumulation_window = getattr(settings, 'accumulation_window_days', 7)
        
    def identify_whale_wallet(
        self,
        activity_data: WhaleActivityData
    ) -> Dict[str, any]:
        """
        Identify and classify whale wallet
        
        Args:
            activity_data: Whale activity data
            
        Returns:
            Dictionary with whale classification
        """
        classification = {
            "is_whale": activity_data.balance_btc >= self.whale_threshold,
            "whale_tier": self._get_whale_tier(activity_data.balance_btc),
            "address": activity_data.address,
            "balance_btc": activity_data.balance_btc
        }
        
        return classification
    
    def _get_whale_tier(self, balance_btc: float) -> str:
        """Classify whale by balance tier"""
        if balance_btc >= 10000:
            return "mega_whale"
        elif balance_btc >= 1000:
            return "large_whale"
        elif balance_btc >= 100:
            return "whale"
        else:
            return "not_whale"
    
    def analyze_accumulation_pattern(
        self,
        activity_data: WhaleActivityData,
        historical_data: Optional[List[WhaleActivityData]] = None
    ) -> Dict[str, any]:
        """
        Analyze rolling 7-day accumulation pattern
        
        Args:
            activity_data: Current whale activity data
            historical_data: Historical activity data
            
        Returns:
            Dictionary with accumulation analysis
        """
        analysis = {
            "seven_day_change": activity_data.seven_day_change_btc,
            "accumulation_streak": activity_data.accumulation_streak_days,
            "is_accumulating": activity_data.seven_day_change_btc > 0,
            "accumulation_rate": 0.0,
            "pattern_strength": 0.0
        }
        
        # Calculate accumulation rate
        if activity_data.balance_btc > 0:
            accumulation_rate = (
                activity_data.seven_day_change_btc / activity_data.balance_btc
            ) * 100
            analysis["accumulation_rate"] = accumulation_rate
        
        # Calculate pattern strength based on streak
        if activity_data.accumulation_streak_days >= 7:
            analysis["pattern_strength"] = min(
                1.0,
                activity_data.accumulation_streak_days / 30.0
            )
        
        # Analyze historical trend if available
        if historical_data and len(historical_data) >= 7:
            recent_changes = [
                d.seven_day_change_btc 
                for d in historical_data[-7:]
            ]
            
            # Check for consistent accumulation
            positive_days = sum(1 for c in recent_changes if c > 0)
            if positive_days >= 5:
                analysis["trend"] = "strong_accumulation"
            elif positive_days >= 3:
                analysis["trend"] = "moderate_accumulation"
            else:
                analysis["trend"] = "mixed"
        
        return analysis
    
    def track_accumulation_streak(
        self,
        activity_data: WhaleActivityData,
        historical_data: List[WhaleActivityData]
    ) -> Dict[str, any]:
        """
        Track whale wallet accumulation streak
        
        Args:
            activity_data: Current activity data
            historical_data: Historical activity data
            
        Returns:
            Dictionary with streak tracking
        """
        streak_info = {
            "current_streak": activity_data.accumulation_streak_days,
            "is_active_streak": activity_data.seven_day_change_btc > 0,
            "streak_total_btc": 0.0,
            "avg_daily_accumulation": 0.0
        }
        
        if not historical_data:
            return streak_info
        
        # Calculate total accumulated during streak
        streak_days = min(
            activity_data.accumulation_streak_days,
            len(historical_data)
        )
        
        if streak_days > 0:
            streak_data = historical_data[-streak_days:]
            total_accumulated = sum(
                d.seven_day_change_btc 
                for d in streak_data 
                if d.seven_day_change_btc > 0
            )
            
            streak_info["streak_total_btc"] = total_accumulated
            streak_info["avg_daily_accumulation"] = (
                total_accumulated / streak_days if streak_days > 0 else 0.0
            )
        
        return streak_info
    
    def detect_accumulation_patterns(
        self,
        activity_data: WhaleActivityData,
        historical_data: List[WhaleActivityData]
    ) -> Dict[str, bool]:
        """
        Detect specific accumulation patterns
        
        Args:
            activity_data: Current activity data
            historical_data: Historical activity data
            
        Returns:
            Dictionary with detected patterns
        """
        patterns = {
            "long_streak": activity_data.accumulation_streak_days >= 7,
            "accelerating": False,
            "large_single_day": False,
            "consistent_small": False
        }
        
        if not historical_data or len(historical_data) < 7:
            return patterns
        
        # Check for accelerating accumulation
        recent_changes = [d.seven_day_change_btc for d in historical_data[-7:]]
        if len(recent_changes) >= 3:
            early_avg = np.mean(recent_changes[:3])
            late_avg = np.mean(recent_changes[-3:])
            if late_avg > early_avg * 1.5:
                patterns["accelerating"] = True
        
        # Check for large single-day accumulation
        if activity_data.seven_day_change_btc > 10:  # > 10 BTC in 7 days
            patterns["large_single_day"] = True
        
        # Check for consistent small accumulation
        positive_changes = [c for c in recent_changes if c > 0]
        if len(positive_changes) >= 5:
            avg_change = np.mean(positive_changes)
            std_change = np.std(positive_changes)
            if std_change < avg_change * 0.5:  # Low variance
                patterns["consistent_small"] = True
        
        return patterns
    
    def calculate_confidence_score(
        self,
        activity_data: WhaleActivityData,
        whale_info: Dict[str, any],
        accumulation_analysis: Dict[str, any],
        patterns: Dict[str, bool]
    ) -> float:
        """
        Calculate confidence score for whale accumulation signal
        
        Args:
            activity_data: Current activity data
            whale_info: Whale classification info
            accumulation_analysis: Accumulation analysis
            patterns: Detected patterns
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.5
        
        # Increase confidence for larger whales
        whale_tier = whale_info.get("whale_tier", "not_whale")
        if whale_tier == "mega_whale":
            confidence += 0.2
        elif whale_tier == "large_whale":
            confidence += 0.15
        elif whale_tier == "whale":
            confidence += 0.1
        
        # Increase confidence for longer streaks
        streak = activity_data.accumulation_streak_days
        if streak >= 14:
            confidence += 0.2
        elif streak >= 7:
            confidence += 0.15
        elif streak >= 3:
            confidence += 0.1
        
        # Increase confidence for strong patterns
        pattern_count = sum(1 for v in patterns.values() if v)
        if pattern_count >= 2:
            confidence += 0.15
        elif pattern_count == 1:
            confidence += 0.05
        
        # Increase confidence for significant accumulation
        if activity_data.seven_day_change_btc > 50:
            confidence += 0.1
        elif activity_data.seven_day_change_btc > 10:
            confidence += 0.05
        
        # Decrease confidence for very short streaks
        if streak < 2:
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    async def process_block(
        self,
        block: BlockData,
        context: ProcessingContext
    ) -> List[Signal]:
        """
        Process block and generate whale activity signals
        
        Args:
            block: Block data to process
            context: Processing context with historical data
            
        Returns:
            List of whale signals above confidence threshold
        """
        signals = []
        
        # Extract whale data from context
        whale_data_list = context.historical_data.get('whale_data', [])
        if not whale_data_list:
            return signals
        
        # Get historical whale data for comparison
        historical_whale = context.historical_data.get('historical_whale', [])
        
        # Generate signal for each whale
        for whale_data in whale_data_list:
            signal = self.generate_whale_signal(whale_data, historical_whale)
            
            # Only include if above threshold
            if signal and self.should_generate_signal(signal.strength):
                signals.append(signal)
        
        return signals
    
    def generate_whale_signal(
        self,
        activity_data: WhaleActivityData,
        historical_data: Optional[List[WhaleActivityData]] = None
    ) -> Signal:
        """
        Generate whale accumulation signal with confidence metrics
        
        Args:
            activity_data: Current whale activity data
            historical_data: Historical activity data for comparison
            
        Returns:
            Signal object with whale accumulation analysis
        """
        # Identify whale
        whale_info = self.identify_whale_wallet(activity_data)
        
        # Analyze accumulation pattern
        accumulation_analysis = self.analyze_accumulation_pattern(
            activity_data,
            historical_data
        )
        
        # Track streak
        streak_info = {}
        if historical_data:
            streak_info = self.track_accumulation_streak(
                activity_data,
                historical_data
            )
        
        # Detect patterns
        patterns = {}
        if historical_data:
            patterns = self.detect_accumulation_patterns(
                activity_data,
                historical_data
            )
        
        # Calculate confidence
        confidence = self.calculate_confidence_score(
            activity_data,
            whale_info,
            accumulation_analysis,
            patterns
        )
        
        # Build signal data with required metadata fields
        signal_data = {
            "whale_address": activity_data.address,
            "amount_btc": abs(activity_data.seven_day_change_btc),
            "balance_btc": activity_data.balance_btc,
            "whale_info": whale_info,
            "accumulation_analysis": accumulation_analysis,
            "streak_info": streak_info,
            "patterns_detected": patterns,
            "transaction_count": len(activity_data.transaction_ids),
            "timestamp": activity_data.timestamp.isoformat()
        }
        
        return Signal(
            type=SignalType.WHALE,
            strength=confidence,
            data=signal_data,
            block_height=activity_data.block_height,
            transaction_ids=activity_data.transaction_ids[:10],
            entity_ids=[],
            is_predictive=False
        )
